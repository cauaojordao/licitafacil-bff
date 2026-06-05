"""
Serviço de enriquecimento de dados com IA.
Classifica editais por CNAE e gera resumo usando Gemini.
"""

import json
from datetime import datetime
from typing import Any, List

import google.generativeai as genai


class EnrichmentService:
    """
    Serviço responsável pelo enriquecimento de dados com IA.
    """

    CNAES_MEI = [
        {"codigo": "5611-2/01", "descricao": "Restaurantes e similares"},
        {"codigo": "4744-0/01", "descricao": "Comércio varejista de ferragens e ferramentas"},
        {"codigo": "4753-9/00", "descricao": "Comércio varejista especializado de eletrodomésticos"},
        {"codigo": "4789-0/05", "descricao": "Comércio varejista de produtos saneantes domissanitários"},
        {"codigo": "8121-4/00", "descricao": "Limpeza em prédios e em domicílios"},
        {"codigo": "4330-4/05", "descricao": "Aplicação de revestimentos e de resinas"},
        {"codigo": "4313-4/00", "descricao": "Obras de terraplenagem"},
        {
            "codigo": "4322-3/02",
            "descricao": "Instalação e manutenção de sistemas centrais de ar condicionado",
        },
        {"codigo": "7490-1/04", "descricao": "Consultoria em tecnologia da informação"},
        {"codigo": "6201-5/00", "descricao": "Desenvolvimento de programas de computador sob encomenda"},
    ]

    def __init__(self, gemini_api_key: str, model: str = "gemini-2.5-flash"):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel(model)

    def enrich_batch(self, documents: List[dict]) -> List[dict]:
        """
        Enriquece um lote de documentos.
        """
        enriched = []

        for doc in documents:
            try:
                enriched_doc = self._enrich_document(doc)
                enriched.append(enriched_doc)
            except Exception as e:
                print(
                    f"❌ Erro ao enriquecer documento "
                    f"{doc.get('numero_controle_pncp')}: {e}"
                )

                fallback_doc = doc.copy()
                fallback_doc["categorias_cnae"] = []
                fallback_doc["categoria_ia"] = "Outros"
                fallback_doc["justificativa_categorizacao"] = ""
                fallback_doc["resumo_simplificado"] = self._fallback_summary(
                    doc.get("objeto_compra", "")
                )
                fallback_doc["processamento_status"] = "error"
                fallback_doc["relevancia_score"] = 0.5
                fallback_doc["enriched_at"] = self._get_current_timestamp()
                fallback_doc["enrichment_version"] = "fallback_1.0"

                enriched.append(fallback_doc)

        return enriched

    def _enrich_document(self, document: dict) -> dict:
        """
        Enriquece um documento individual usando Gemini.
        """
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
        """
        Chama Gemini uma única vez para classificar CNAEs e gerar resumo.
        """
        objeto_compra = document.get("objeto_compra") or ""
        valor_estimado = document.get("valor_total_estimado") or 0
        modalidade = document.get("modalidade_nome") or "N/A"

        orgao = document.get("orgao_entidade") or {}
        unidade = document.get("unidade_orgao") or {}

        prompt = f"""
Você é um especialista em licitações públicas e enquadramento de oportunidades para MEI.

Analise o edital abaixo e retorne:
1. Até 3 CNAEs MEI mais adequados.
2. Um resumo simples do edital.
3. Uma justificativa curta da categorização.

CNAES DISPONÍVEIS:
{json.dumps(self.CNAES_MEI, ensure_ascii=False, indent=2)}

DADOS DO EDITAL:
Objeto: {objeto_compra}
Valor estimado: R$ {float(valor_estimado):,.2f}
Modalidade: {modalidade}
Órgão: {orgao.get("razao_social") or "N/A"}
CNPJ órgão: {orgao.get("cnpj") or "N/A"}
Unidade: {unidade.get("nome_unidade") or "N/A"}
Município: {unidade.get("municipio_nome") or "N/A"}
UF: {unidade.get("uf_sigla") or "N/A"}

Regras:
- Use somente CNAEs da lista fornecida.
- Retorne no máximo 3 CNAEs.
- Se nenhum CNAE for adequado, retorne "categorias": [].
- O resumo deve ter no máximo 150 caracteres.
- A confiança deve ser um número entre 0 e 1.
- Retorne APENAS JSON válido, sem markdown.

Formato obrigatório:
{{
  "categorias": [
    {{
      "codigo": "XXXX-X/XX",
      "descricao": "...",
      "confianca": 0.95
    }}
  ],
  "resumo_simplificado": "resumo curto do edital",
  "justificativa": "explicação breve",
  "status": "success"
}}
"""
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
            print(f"❌ Erro ao chamar Gemini: {e}")

            return {
                "categorias": [],
                "resumo_simplificado": self._fallback_summary(objeto_compra),
                "justificativa": "",
                "status": "error",
                "error_message": str(e),
            }

    def _sanitize_categories(self, categorias: Any) -> list[dict]:
        """
        Garante que o Gemini só retorne CNAEs existentes na lista permitida.
        """
        if not isinstance(categorias, list):
            return []

        allowed_by_code = {
            item["codigo"]: item["descricao"]
            for item in self.CNAES_MEI
        }

        sanitized = []

        for item in categorias:
            if not isinstance(item, dict):
                continue

            codigo = str(item.get("codigo") or "").strip()
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
        """
        Extrai categoria principal para salvar em categories/opportunity_categories.
        """
        if not categorias:
            return "Outros"

        return categorias[0].get("descricao") or "Outros"

    def _calculate_relevance_score(
            self,
            document: dict,
            categorias: list[dict],
    ) -> float:
        """
        Calcula score de relevância baseado em valor e confiança do Gemini.
        """
        score = 0.5

        valor = float(document.get("valor_total_estimado") or 0)

        if valor > 100000:
            score += 0.2

        if categorias:
            confianca = float(categorias[0].get("confianca") or 0)
            score += min(0.3, confianca * 0.3)

        return min(1.0, max(0.0, score))

    def _remove_markdown_json(self, text: str) -> str:
        """
        Remove ```json ... ``` caso o Gemini retorne markdown.
        """
        if not text:
            return "{}"

        if text.startswith("```"):
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
