"""
Streamlit chat interface powered by Gemini + FastMCP.
Run with:  streamlit run src/chat/app.py
"""

import asyncio
import json
import re
import sys
import time
from pathlib import Path

import streamlit as st
from fastmcp import FastMCP
from fastmcp.client import Client
from google import genai
from google.genai import types

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.chat.mcp_server import mcp  # noqa: E402 — import after sys.path fix
from src.config.settings import Settings

SYSTEM_PROMPT = """Você é um assistente especializado em dados de licitações públicas brasileiras
do PNCP (Portal Nacional de Contratações Públicas). Você tem acesso a ferramentas para consultar
dados reais armazenados no MongoDB.

Use as ferramentas para responder com precisão. Ao apresentar licitações, destaque:
- Número de controle (numero_controle_pncp)
- Objeto da compra (objetoCompra)
- Órgão responsável (orgaoEntidade.razaoSocial)
- Valor estimado quando disponível
- Data de encerramento de propostas

Responda sempre em português brasileiro de forma clara e objetiva."""

AVAILABLE_MODELS = {
    "gemini-2.0-flash": "Gemini 2.0 Flash",
    "gemini-2.0-flash-lite": "Gemini 2.0 Flash Lite",
    "gemini-1.5-flash": "Gemini 1.5 Flash",
    "gemini-1.5-flash-8b": "Gemini 1.5 Flash 8B",
    "gemini-1.5-pro": "Gemini 1.5 Pro",
}


# ─── Async helpers ────────────────────────────────────────────────────────────

def _run(coro):
    """Execute a coroutine from Streamlit's synchronous context."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


async def _list_tools(server: FastMCP) -> list:
    async with Client(server) as client:
        return await client.list_tools()


async def _call_tool(server: FastMCP, name: str, args: dict):
    async with Client(server) as client:
        return await client.call_tool(name, args)


# ─── MCP ↔ Gemini bridge ──────────────────────────────────────────────────────

_GEMINI_UNSUPPORTED = {"additionalProperties", "$schema", "title", "default"}


def _clean_schema(obj):
    """Recursively strip keys that Gemini's API rejects."""
    if isinstance(obj, dict):
        return {
            k: _clean_schema(v)
            for k, v in obj.items()
            if k not in _GEMINI_UNSUPPORTED
        }
    if isinstance(obj, list):
        return [_clean_schema(i) for i in obj]
    return obj


def _to_gemini_declarations(tools) -> list[types.FunctionDeclaration]:
    declarations = []
    for tool in tools:
        schema = tool.inputSchema or {"type": "object", "properties": {}}
        clean = _clean_schema(schema)
        declarations.append(
            types.FunctionDeclaration(
                name=tool.name,
                description=tool.description or "",
                parameters=clean,
            )
        )
    return declarations


def _execute_tool(name: str, args: dict) -> str:
    result = _run(_call_tool(mcp, name, args))
    if result and hasattr(result[0], "text"):
        return result[0].text
    return json.dumps(result, ensure_ascii=False, default=str)


def _is_rate_limit(exc: Exception) -> bool:
    return "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc)


def _parse_retry_delay(error: Exception) -> float:
    """Extract retry delay in seconds from a 429 error message, default 10s."""
    text = str(error)
    match = re.search(r"retryDelay['\"]?\s*[:\s]+['\"]?(\d+(?:\.\d+)?)", text)
    if match:
        return float(match.group(1)) + 1.0
    return 10.0


# ─── Gemini agentic loop ──────────────────────────────────────────────────────

def chat(
    user_message: str,
    history: list[dict],
    tools: list[types.FunctionDeclaration],
    model: str,
) -> str:
    gemini = genai.Client(api_key=Settings.GEMINI_API_KEY)

    contents: list[types.Content] = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

    tool_config = [types.Tool(function_declarations=tools)] if tools else []

    max_retries = 3
    while True:
        for attempt in range(max_retries):
            try:
                response = gemini.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        tools=tool_config,
                    ),
                )
                break
            except Exception as exc:
                if _is_rate_limit(exc) and attempt < max_retries - 1:
                    delay = _parse_retry_delay(exc)
                    st.toast(f"Cota atingida — aguardando {delay:.0f}s antes de tentar novamente…")
                    time.sleep(delay)
                else:
                    raise

        candidate_content = response.candidates[0].content
        contents.append(candidate_content)

        function_calls = [p for p in candidate_content.parts if p.function_call]
        if not function_calls:
            return "".join(
                p.text for p in candidate_content.parts if hasattr(p, "text") and p.text
            )

        tool_response_parts = []
        for part in function_calls:
            fc = part.function_call
            args = dict(fc.args) if fc.args else {}
            try:
                result_text = _execute_tool(fc.name, args)
            except Exception as exc:
                result_text = json.dumps({"erro": str(exc)})
            tool_response_parts.append(
                types.Part(
                    function_response=types.FunctionResponse(
                        name=fc.name,
                        response={"result": result_text},
                    )
                )
            )

        contents.append(types.Content(role="tool", parts=tool_response_parts))


# ─── Streamlit UI ─────────────────────────────────────────────────────────────

st.set_page_config(page_title="LicitaFácil Chat", page_icon="🏛️", layout="wide")

st.title("🏛️ LicitaFácil — Chat com os Dados")
st.caption("Converse com os dados de licitações do PNCP via Gemini + FastMCP")

# Load MCP tools once per session
if "gemini_tools" not in st.session_state:
    with st.spinner("Conectando ao servidor MCP..."):
        try:
            raw_tools = _run(_list_tools(mcp))
            st.session_state.gemini_tools = _to_gemini_declarations(raw_tools)
            st.session_state.tool_names = [t.name for t in raw_tools]
        except Exception as exc:
            st.error(f"Erro ao inicializar o servidor MCP: {exc}")
            st.session_state.gemini_tools = []
            st.session_state.tool_names = []

# Sidebar
with st.sidebar:
    st.header("Modelo Gemini")
    selected_model = st.selectbox(
        "Modelo",
        options=list(AVAILABLE_MODELS.keys()),
        format_func=lambda k: AVAILABLE_MODELS[k],
        index=0,
        label_visibility="collapsed",
    )
    st.caption("Troque de modelo se atingir a cota do atual.")

    st.divider()
    st.header("Ferramentas MCP")
    for name in st.session_state.get("tool_names", []):
        st.code(name)

    st.divider()
    st.markdown("**Exemplos de perguntas:**")
    st.markdown(
        "- Quantas licitações temos no banco?\n"
        "- Mostre as 5 últimas licitações de TI\n"
        "- Quais órgãos têm mais editais?\n"
        "- Licitações encerradas em 2024"
    )
    st.divider()
    if st.button("🗑️ Limpar conversa"):
        st.session_state.messages = []
        st.rerun()

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
if prompt := st.chat_input("Pergunte sobre as licitações..."):
    if not Settings.GEMINI_API_KEY:
        st.error("GEMINI_API_KEY não configurada no arquivo .env")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Consultando..."):
            try:
                answer = chat(
                    prompt,
                    st.session_state.messages[:-1],
                    st.session_state.gemini_tools,
                    selected_model,
                )
            except Exception as exc:
                if _is_rate_limit(exc):
                    answer = (
                        "**Cota esgotada para o modelo selecionado.** "
                        "Troque o modelo no menu lateral e tente novamente.\n\n"
                        f"Detalhe: `{exc}`"
                    )
                else:
                    answer = f"Erro: {exc}"
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
