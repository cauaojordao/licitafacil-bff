"""
Serviço de enriquecimento de dados com IA.
Classifica editais por CNAE e gera resumo usando Gemini.
"""

import json
import logging
import re
import time
from datetime import datetime
from typing import Any

import google.generativeai as genai

from apps.api.src.repositories.cnae_repository import CNAERepository

logger = logging.getLogger(__name__)


def normalize_cnae(code: str) -> str:
    """Remove máscara do CNAE: 6201-5/00 -> 6201500."""
    return re.sub(r"\D", "", code or "")


class EnrichmentService:
    """
    Serviço responsável pelo enriquecimento de dados com IA.
    """

    MAX_GEMINI_RETRIES = 3
    GEMINI_RETRY_BACKOFF_SECONDS = 2

    FALLBACK_CNAES_MEI = [
        {"codigo": "5611201", "descricao": "Restaurantes e similares"},
        {
            "codigo": "4744001",
            "descricao": "Comércio varejista de ferragens e ferramentas",
        },
        {
            "codigo": "4753900",
            "descricao": "Comércio varejista especializado de eletrodomésticos",
        },
        {
            "codigo": "4789005",
            "descricao": "Comércio varejista de produtos saneantes domissanitários",
        },
        {"codigo": "8121400", "descricao": "Limpeza em prédios e em domicílios"},
        {"codigo": "4330405", "descricao": "Aplicação de revestimentos e de resinas"},
        {"codigo": "4313400", "descricao": "Obras de terraplenagem"},
        {
            "codigo": "4322302",
            "descricao": (
                "Instalação e manutenção de sistemas centrais de ar condicionado"
            ),
        },
        {
            "codigo": "6204000",
            "descricao": "Consultoria em tecnologia da informação",
        },
        {
            "codigo": "6201501",
            "descricao": "Desenvolvimento de programas de computador sob encomenda",
        },
    ]

    def __init__(
        self,
        gemini_api_key: str,
        cnae_repository: CNAERepository | None = None,
        model: str = "gemini-2.5-flash",
    ) -> None:
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel(model)
        self.cnae_repository = cnae_repository
        self.cnaes_mei = self._load_cnaes_from_database()

    def _load_cnaes_from_database(self) -> list[dict]:
        """
        Carrega os CNAEs do banco.
        Caso não consiga, usa fallback local.
        """
        if not self.cnae_repository:
            return self.FALLBACK_CNAES_MEI

        try:
            result = self.cnae_repository.db.table("cnaes").select("*").execute()
            rows = result.data or []

            cnaes = []

            for row in rows:
                codigo = normalize_cnae(str(row.get("id") or ""))

                descricao = (
                    row.get("title")
                    or row.get("description")
                    or row.get("descricao")
                    or ""
                )

                if not codigo or not descricao:
                    continue

                cnaes.append(
                    {
                        "codigo": codigo,
                        "descricao": descricao,
                    }
                )

            return cnaes or self.FALLBACK_CNAES_MEI

        except Exception as e:
            logger.error("Erro ao carregar CNAEs do banco: %s", e)
            return self.FALLBACK_CNAES_MEI

    def enrich_batch(self, documents: list[dict]) -> list[dict]:
        # Sem fallback: se um documento falhar (após os retries do Gemini),
        # a exceção propaga e o processamento do lote falha.
        return [self._enrich_document(doc) for doc in documents]

    def _enrich_document(self, document: dict) -> dict:
        enriched = document.copy()

        objeto_compra = document.get("objeto_compra") or ""

        ai_result = self._call_gemini(document)

        categorias = ai_result.get("categorias", [])
        categoria_principal = self._extract_main_category(categorias)

        enriched["categorias_cnae"] = categorias
        enriched["categoria_ia"] = categoria_principal
        enriched["justificativa_categorizacao"] = ai_result.get("justificativa", "")
        enriched["resumo_simplificado"] = ai_result.get(
            "resumo_simplificado",
            self._fallback_summary(objeto_compra),
        )
        enriched["processamento_status"] = ai_result.get("status", "success")
        enriched["relevancia_score"] = self._calculate_relevance_score(
            document,
            categorias,
        )
        enriched["enriched_at"] = self._get_current_timestamp()
        enriched["enrichment_version"] = "gemini_1.0"

        return enriched

    def _call_gemini(self, document: dict) -> dict[str, Any]:
        objeto_compra = document.get("objeto_compra") or ""
        valor_estimado = document.get("valor_total_estimado") or 0
        modalidade = document.get("modalidade_nome") or "N/A"

        orgao = document.get("orgao_entidade") or {}
        unidade = document.get("unidade_orgao") or {}

        cnaes_json = json.dumps(self.cnaes_mei, indent=2, ensure_ascii=False)

        prompt = f"""
Você é um especialista em licitações públicas e enquadramento de oportunidades \
para Microempreendedor Individual (MEI).

Sua tarefa é analisar o edital fornecido e encontrar os CNAEs MEI mais adequados \
dentro da lista permitida abaixo, utilizando comparação direta rigorosa ("cara-crachá").

CNAES MEI DISPONÍVEIS PARA COMPARAÇÃO:
{cnaes_json}

DADOS DO EDITAL PARA ANÁLISE:
Objeto: {objeto_compra}
Valor estimado: R$ {float(valor_estimado):,.2f}
Modalidade: {modalidade}
Órgão: {orgao.get("razao_social") or "N/A"}
CNPJ órgão: {orgao.get("cnpj") or "N/A"}
Unidade: {unidade.get("nome_unidade") or "N/A"}
Município: {unidade.get("municipio_nome") or "N/A"}
UF: {unidade.get("uf_sigla") or "N/A"}

DIRETRIZES DE ANÁLISE ("CARA-CRACHÁ"):
1. Comparação Direta: compare termos do "Objeto" com a descrição exata de cada CNAE.
2. Rejeição de Genéricos: se nenhum CNAE cobrir a atividade principal, retorne \
"categorias": [].
3. Limite: retorne no máximo 3 CNAEs, do mais específico ao menos específico.
4. O resumo_simplificado deve ter no máximo 150 caracteres.
5. A justificativa deve explicar por que o CNAE escolhido encaixa no objeto.
6. Retorne APENAS JSON válido, sem markdown ou texto extra.

Formato de Saída Obrigatório:
{{
  "categorias": [
    {{
      "codigo": "9511800",
      "descricao": "Reparação e manutenção de computadores",
      "confianca": 0.95
    }}
  ],
  "resumo_simplificado": "Resumo objetivo do edital com até 150 caracteres.",
  "justificativa": "Explicação do match entre o objeto e os CNAEs selecionados.",
  "status": "success"
}}
"""
        last_error: Exception | None = None

        for attempt in range(1, self.MAX_GEMINI_RETRIES + 1):
            try:
                response = self.model.generate_content(prompt)
                result_text = (response.text or "").strip()
                result_text = self._remove_markdown_json(result_text)

                result = json.loads(result_text)

                categorias = self._sanitize_categories(result.get("categorias", []))

                resumo = result.get("resumo_simplificado") or self._fallback_summary(
                    objeto_compra
                )

                return {
                    "categorias": categorias,
                    "resumo_simplificado": resumo[:150],
                    "justificativa": result.get("justificativa", ""),
                    "status": "success",
                }

            except Exception as e:
                last_error = e
                logger.error(
                    "Tentativa %s/%s de chamar o Gemini falhou: %s",
                    attempt,
                    self.MAX_GEMINI_RETRIES,
                    e,
                )

                if attempt < self.MAX_GEMINI_RETRIES:
                    time.sleep(self.GEMINI_RETRY_BACKOFF_SECONDS * attempt)

        # Esgotadas as tentativas: sem fallback, a exceção propaga.
        raise RuntimeError(
            f"Gemini falhou após {self.MAX_GEMINI_RETRIES} tentativas: {last_error}"
        ) from last_error

    def _sanitize_categories(self, categorias: Any) -> list[dict]:
        """
        Garante que o Gemini só retorne CNAEs existentes no banco/lista permitida.
        """
        if not isinstance(categorias, list):
            return []

        allowed_by_code = {
            normalize_cnae(item["codigo"]): item["descricao"] for item in self.cnaes_mei
        }

        sanitized = []

        for item in categorias:
            if not isinstance(item, dict):
                continue

            codigo = normalize_cnae(str(item.get("codigo") or ""))
            descricao = allowed_by_code.get(codigo)

            if not descricao:
                continue

            try:
                confianca = float(item.get("confianca", 0.5))
            except Exception:
                confianca = 0.5

            confianca = min(1.0, max(0.0, confianca))

            sanitized.append(
                {
                    "codigo": codigo,
                    "descricao": descricao,
                    "confianca": confianca,
                }
            )

        return sanitized[:3]

    def _extract_main_category(self, categorias: list[dict]) -> str:
        if not categorias:
            return "Outros"

        return categorias[0].get("descricao") or "Outros"

    def _calculate_relevance_score(
        self,
        document: dict,
        categorias: list[dict],
    ) -> float:
        score = 0.5

        valor = float(document.get("valor_total_estimado") or 0)

        if valor > 100000:
            score += 0.2

        if categorias:
            confianca = float(categorias[0].get("confianca") or 0)
            score += min(0.3, confianca * 0.3)

        return min(1.0, max(0.0, score))

    def _remove_markdown_json(self, text: str) -> str:
        if not text:
            return "{}"

        if text.startswith(" ⁠"):
            text = text.split("```")[1]

            if text.startswith("json"):
                text = text[4:]

            text = text.strip()

        return text

    def _fallback_summary(self, object_text: str) -> str:
        if not object_text:
            return ""

        return object_text[:147] + "..." if len(object_text) > 150 else object_text

    def _get_current_timestamp(self) -> str:
        return datetime.now().isoformat()
