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
        {"codigo": "4744001", "descricao": "Comércio varejista de ferragens e ferramentas"},
        {"codigo": "4753900", "descricao": "Comércio varejista especializado de eletrodomésticos"},
        {"codigo": "4789005", "descricao": "Comércio varejista de produtos saneantes domissanitários"},
        {"codigo": "8121400", "descricao": "Limpeza em prédios e em domicílios"},
        {"codigo": "4330405", "descricao": "Aplicação de revestimentos e de resinas"},
        {"codigo": "4313400", "descricao": "Obras de terraplenagem"},
        {
            "codigo": "4322302",
            "descricao": "Instalação e manutenção de sistemas centrais de ar condicionado",
        },
        {"codigo": "6204000", "descricao": "Consultoria em tecnologia da informação"},
        {"codigo": "6201501", "descricao": "Desenvolvimento de programas de computador sob encomenda"},
    ]

    def _init_(
        self,
        gemini_api_key: str,
        cnae_repository: CNAERepository | None = None,
        model: str = "gemini-2.5-flash",
    ):
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

        prompt =  f"""
Você é um especialista em licitações públicas e enquadramento de oportunidades para Microempreendedor Individual (MEI).

Sua tarefa é analisar o edital fornecido e encontrar os CNAEs MEI mais adequados dentro da lista permitida abaixo, utilizando uma abordagem extremamente rigorosa de comparação direta ("cara-crachá").

CNAES MEI DISPONÍVEIS PARA COMPARAÇÃO:
[
  {"codigo": "4321500", "descricao": "Instalação e manutenção elétrica"},
  {"codigo": "4322301", "descricao": "Instalações hidráulicas, sanitárias e de gás"},
  {"codigo": "4330101", "descricao": "Impermeabilização em obras de engenharia civil"},
  {"codigo": "4330102", "descricao": "Aplicação de revestimentos e de resinas em pisos e paredes"},
  {"codigo": "4330103", "descricao": "Obras de acabamento em gesso e gesso cartonado"},
  {"codigo": "4330104", "descricao": "Pintura para construção civil"},
  {"codigo": "4330105", "descricao": "Instalação de portas, janelas, tetos, divisórias e armários embutidos de qualquer material"},
  {"codigo": "4330199", "descricao": "Outras obras de acabamento da construção"},
  {"codigo": "4399103", "descricao": "Obras de alvenaria"},
  {"codigo": "4713002", "descricao": "Lojas de variedades, exceto lojas de departamentos ou magazines"},
  {"codigo": "4721104", "descricao": "Comércio varejista de doces, balas, bombons e semelhantes"},
  {"codigo": "4723700", "descricao": "Comércio varejista de bebidas"},
  {"codigo": "4729699", "descricao": "Comércio varejista de produtos alimentícios em geral ou especializado em produtos alimentícios não especificados anteriormente"},
  {"codigo": "4741500", "descricao": "Comércio varejista de tintas e materiais para pintura"},
  {"codigo": "4742300", "descricao": "Comércio varejista de material elétrico"},
  {"codigo": "4744001", "descricao": "Comércio varejista de ferragens e ferramentas"},
  {"codigo": "4744099", "descricao": "Comércio varejista de materiais de construção em geral"},
  {"codigo": "4751201", "descricao": "Comércio varejista especializado de equipamentos e suprimentos de informática"},
  {"codigo": "4753900", "descricao": "Comércio varejista especializado de eletrodomésticos e equipamentos de áudio e vídeo"},
  {"codigo": "4754701", "descricao": "Comércio varejista de móveis"},
  {"codigo": "4759899", "descricao": "Comércio varejista de outros artigos de uso doméstico não especificados anteriormente"},
  {"codigo": "4761003", "descricao": "Comércio varejista de artigos de papelaria"},
  {"codigo": "4763601", "descricao": "Comércio varejista de brinquedos e artigos recreativos"},
  {"codigo": "4763602", "descricao": "Comércio varejista de artigos esportivos"},
  {"codigo": "4781400", "descricao": "Comércio varejista de artigos do vestuário e acessórios"},
  {"codigo": "4782201", "descricao": "Comércio varejista de calçados"},
  {"codigo": "4789001", "descricao": "Comércio varejista de suvenires, bijuterias e artesanatos"},
  {"codigo": "4789002", "descricao": "Comércio varejista de plantas e flores naturais"},
  {"codigo": "4789004", "descricao": "Comércio varejista de animais vivos e de artigos e alimentos para animais de estimação"},
  {"codigo": "4789005", "descricao": "Comércio varejista de produtos saneantes domissanitários"},
  {"codigo": "4789007", "descricao": "Comércio varejista de equipamentos para escritório"},
  {"codigo": "4789008", "descricao": "Comércio varejista de artigos de óptica"},
  {"codigo": "4789099", "descricao": "Comércio varejista de outros produtos não especificados anteriormente"},
  {"codigo": "4923001", "descricao": "Serviço de táxi"},
  {"codigo": "4929901", "descricao": "Transporte rodoviário coletivo de passageiros, sob regime de fretamento, municipal"},
  {"codigo": "4930201", "descricao": "Transporte rodoviário de carga, exceto produtos perigosos e mudanças, municipal"},
  {"codigo": "5320202", "descricao": "Serviços de entrega rápida"},
  {"codigo": "5611203", "descricao": "Lanchonetes, casas de chá, de sucos e similares"},
  {"codigo": "5620102", "descricao": "Serviços de alimentação para eventos e recepções - bufê"},
  {"codigo": "5620104", "descricao": "Fornecimento de alimentos preparados preponderantemente para consumo domiciliar"},
  {"codigo": "5911102", "descricao": "Produção de filmes para publicidade"},
  {"codigo": "5912099", "descricao": "Atividades de pós-produção cinematográfica, de vídeos e de programas de televisão não especificadas anteriormente"},
  {"codigo": "6209100", "descricao": "Suporte técnico, manutenção e outros serviços em tecnologia da informação"},
  {"codigo": "7319002", "descricao": "Promoção de vendas"},
  {"codigo": "7319003", "descricao": "Marketing direto"},
  {"codigo": "7420001", "descricao": "Atividades de produção fotográfica, exceto aérea e submarina"},
  {"codigo": "7490199", "descricao": "Outras atividades profissionais, científicas e técnicas não especificadas anteriormente"},
  {"codigo": "7721700", "descricao": "Aluguel de equipamentos recreativos e esportivos"},
  {"codigo": "7729202", "descricao": "Aluguel de móveis, utensílios e aparelhos de uso doméstico e pessoal; instrumentos musicais"},
  {"codigo": "7733100", "descricao": "Aluguel de máquinas e equipamentos para escritórios"},
  {"codigo": "7739099", "descricao": "Aluguel de outras máquinas e equipamentos comerciais e industriais não especificados anteriormente, sem operador"},
  {"codigo": "7911200", "descricao": "Agências de viagens"},
  {"codigo": "8121800", "descricao": "Limpeza em prédios e em domicílios"},
  {"codigo": "8129000", "descricao": "Atividades de limpeza não especificadas anteriormente"},
  {"codigo": "8130300", "descricao": "Atividades de paisagismo"},
  {"codigo": "8211300", "descricao": "Serviços combinados de escritório e apoio administrativo"},
  {"codigo": "8219901", "descricao": "Fotocópias"},
  {"codigo": "8219999", "descricao": "Preparação de documentos e serviços especializados de apoio administrativo não especificados anteriormente"},
  {"codigo": "8230001", "descricao": "Serviços de organização de feiras, congressos, exposições e festas"},
  {"codigo": "8592901", "descricao": "Ensino de dança"},
  {"codigo": "8592902", "descricao": "Ensino de artes cênicas, exceto dança"},
  {"codigo": "8592903", "descricao": "Ensino de música"},
  {"codigo": "8592999", "descricao": "Ensino de arte e cultura não especificado anteriormente"},
  {"codigo": "8593700", "descricao": "Ensino de idiomas"},
  {"codigo": "8599603", "descricao": "Treinamento em desenvolvimento profissional e gerencial"},
  {"codigo": "8599699", "descricao": "Outras atividades de ensino não especificadas anteriormente"},
  {"codigo": "9001901", "descricao": "Produção teatral"},
  {"codigo": "9001902", "descricao": "Produção musical"},
  {"codigo": "9001906", "descricao": "Atividades de sonorização e de iluminação"},
  {"codigo": "9329899", "descricao": "Outras atividades de recreação e lazer não especificadas anteriormente"},
  {"codigo": "9511800", "descricao": "Reparação e manutenção de computadores e de equipamentos periféricos"},
  {"codigo": "9512600", "descricao": "Reparação e manutenção de equipamentos de comunicação"},
  {"codigo": "9521500", "descricao": "Reparação e manutenção de aparelhos eletroeletrônicos de uso doméstico"},
  {"codigo": "9529102", "descricao": "Chaveiros"},
  {"codigo": "9529105", "descricao": "Reparação de artigos do vestuário e acessórios"},
  {"codigo": "9602501", "descricao": "Cabeleireiros, manicure e pedicure"},
  {"codigo": "9602502", "descricao": "Atividades de estética e outros serviços de cuidados com a beleza"},
  {"codigo": "9609709", "descricao": "Outras atividades de serviços pessoais não especificadas anteriormente"}
]

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
1.⁠ ⁠Comparação Direta: Compare os termos, verbos e substantivos do "Objeto" com a descrição exata de cada CNAE da lista.
2.⁠ ⁠Rejeição de Genéricos: Não selecione CNAEs de serviços gerais se o objeto exigir uma especialidade descrita em outro CNAE. Se nenhum CNAE da lista cobrir diretamente a atividade principal do objeto, retorne a lista de categorias vazia: "categorias": [].
3.⁠ ⁠Limite: Retorne no máximo 3 CNAEs, ordenados do mais específico (maior confiança) para o menos específico.
4.⁠ ⁠O resumo_simplificado deve ter no máximo 150 caracteres.
5.⁠ ⁠A justificativa deve explicar brevemente por que o CNAE escolhido é o encaixe perfeito para o objeto.
6. Retorne APENAS o JSON válido, sem qualquer tipo de formatação markdown (como ⁠ json) ou texto antes/depois do JSON.

Formato de Saída Obrigatório:
{
  "categorias": [
    {
      "codigo": "9511800",
      "descricao": "Reparação e manutenção de computadores e de equipamentos periféricos",
      "confianca": 0.95
    }
  ],
  "resumo_simplificado": "Resumo objetivo do edital com até 150 caracteres.",
  "justificativa": "Explicação do match direto entre o objeto e os CNAEs selecionados.",
  "status": "success"
}
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
            normalize_cnae(item["codigo"]): item["descricao"]
            for item in self.cnaes_mei
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