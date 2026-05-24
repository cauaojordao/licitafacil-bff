"""
Processador de editais da camada Silver.
Enriquece os dados com classificação e resumos via IA.
"""
from typing import Any
from pyspark.sql import Row

from src.silver.category_classifier import CategoryClassifier
from src.silver.summary_generator import SummaryGenerator


class EditalProcessor:
    """
    Processa e enriquece editais com informações de IA.
    """

    def __init__(self, gemini_api_key: str) -> None:
        """
        Inicializa o processador.

        Args:
            gemini_api_key: Chave da API Gemini.
        """
        self.classifier = CategoryClassifier(api_key=gemini_api_key)
        self.summarizer = SummaryGenerator(api_key=gemini_api_key)

    def process(self, row: Row) -> dict[str, Any]:
        """
        Processa um edital individual.

        Args:
            row: Linha do DataFrame Spark.

        Returns:
            Dicionário com dados enriquecidos.
        """
        objeto_compra = row.objeto_compra or ""

        # Classificação por CNAE
        classification = self.classifier.classify(objeto_compra)

        # Geração de resumo
        resumo = self.summarizer.generate(
            objeto_compra=objeto_compra,
            valor_estimado=row.valor_total_estimado,
            modalidade=row.modalidade_nome,
            orgao=row.orgao_entidade.razao_social if row.orgao_entidade else None,
        )

        # Monta documento enriquecido
        return {
            "numero_controle_pncp": row.numero_controle_pncp,
            "objeto_compra": objeto_compra,
            "valor_total_estimado": row.valor_total_estimado,
            "modalidade_nome": row.modalidade_nome,
            "data_encerramento_proposta": row.data_encerramento_proposta,
            "orgao_entidade": {
                "razao_social": row.orgao_entidade.razao_social if row.orgao_entidade else None,
                "cnpj": row.orgao_entidade.cnpj if row.orgao_entidade else None,
            },
            "unidade_orgao": {
                "uf_sigla": row.unidade_orgao.uf_sigla if row.unidade_orgao else None,
                "municipio_nome": row.unidade_orgao.municipio_nome if row.unidade_orgao else None,
            },
            "categorias_cnae": classification.get("categorias", []),
            "justificativa_categorizacao": classification.get("justificativa", ""),
            "resumo_simplificado": resumo,
            "processamento_status": classification.get("status", "unknown"),
        }
