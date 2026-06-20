"""
Serviço de transformação de dados PNCP.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class TransformationService:
    """
    Serviço responsável por transformações de dados na camada Bronze.
    """

    def transform_batch(self, raw_data: list[dict]) -> list[dict[str, Any]]:
        """
        Transforma um lote de dados brutos.

        Args:
            raw_data: Lista de dados brutos da API PNCP.

        Returns:
            Lista de dados transformados.
        """
        transformed = []

        for raw_record in raw_data:
            try:
                transformed_record = self._transform_record(raw_record)
                if transformed_record:
                    transformed.append(transformed_record)
            except Exception as e:
                logger.warning("Erro ao transformar registro: %s", e)
                continue

        return transformed

    def _transform_record(self, raw_record: dict) -> dict[str, Any] | None:
        """
        Transforma um registro individual.

        Args:
            raw_record: Registro bruto da API.

        Returns:
            Registro transformado ou None se inválido.
        """
        # Validação básica
        pncp_id = raw_record.get("numeroControlePNCP")
        if not pncp_id:
            return None

        # Transformações básicas (limpeza, normalização)
        transformed = {
            "numero_controle_pncp": str(
                raw_record.get("numeroControlePNCP")
                or raw_record.get("numero_controle_pncp")
                or pncp_id
            ),
            "objeto_compra": self._clean_text(raw_record.get("objetoCompra", "")),
            "modalidade_nome": self._clean_text(
                raw_record.get("modalidadeNome")
                or raw_record.get("modalidade", {}).get("nome", "")
            ),
            "modalidade_id": (
                raw_record.get("modalidadeId")
                or raw_record.get("modalidade", {}).get("id")
            ),
            "situacao_compra_nome": self._clean_text(
                raw_record.get("situacaoCompraNome")
                or raw_record.get("situacaoCompra", {}).get("nome", "")
            ),
            "situacao_compra_id": raw_record.get("situacaoCompraId"),
            "valor_total_estimado": self._parse_float(
                raw_record.get("valorTotalEstimado")
            ),
            "valor_total_homologado": self._parse_float(
                raw_record.get("valorTotalHomologado")
            ),
            "data_publicacao_pncp": raw_record.get("dataPublicacaoPncp"),
            "data_abertura_proposta": raw_record.get("dataAberturaProposta"),
            "data_encerramento_proposta": raw_record.get("dataEncerramentoProposta"),
            "data_atualizacao": raw_record.get("dataAtualizacao"),
            "data_atualizacao_global": raw_record.get("dataAtualizacaoGlobal"),
            "data_inclusao": raw_record.get("dataInclusao"),
            "orgao_entidade": raw_record.get("orgaoEntidade", {}),
            "unidade_orgao": raw_record.get("unidadeOrgao", {}),
            "link_sistema_origem": raw_record.get("linkSistemaOrigem"),
            "link_processo_eletronico": raw_record.get("linkProcessoEletronico"),
            "criterio_julgamento_nome": self._clean_text(
                raw_record.get("criterioJulgamentoNome")
                or raw_record.get("criterioJulgamento", {}).get("nome", "")
            ),
            "informacao_complementar": self._clean_text(
                raw_record.get("informacaoComplementar", "")
            ),
            "resumo_simplificado": self._clean_text(
                raw_record.get("informacaoComplementar")
                or raw_record.get("informacaoAdicional")
                or raw_record.get("objetoCompra", "")
            ),
            "amparo_legal": raw_record.get("amparoLegal", {}),
            "ano_compra": raw_record.get("anoCompra"),
            "numero_compra": raw_record.get("numeroCompra"),
            "processo": raw_record.get("processo"),
            "sequencial_compra": raw_record.get("sequencialCompra"),
            "modo_disputa_id": raw_record.get("modoDisputaId"),
            "modo_disputa_nome": raw_record.get("modoDisputaNome"),
            "tipo_instrumento_convocatorio_codigo": raw_record.get(
                "tipoInstrumentoConvocatorioCodigo"
            ),
            "tipo_instrumento_convocatorio_nome": raw_record.get(
                "tipoInstrumentoConvocatorioNome"
            ),
            "srp": raw_record.get("srp"),
            "usuario_nome": raw_record.get("usuarioNome"),
            "fontes_orcamentarias": raw_record.get("fontesOrcamentarias", []),
            "processed_at": self._get_current_timestamp(),
            "source": "pncp_api",
        }

        return transformed

    def _clean_text(self, text: str | None) -> str:
        """Remove caracteres especiais e normaliza texto."""
        if not isinstance(text, str):
            return ""
        return text.strip()

    def _parse_float(self, value: Any) -> float:
        """Converte valor para float de forma segura."""
        try:
            return float(value) if value is not None else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _get_current_timestamp(self) -> str:
        """Retorna timestamp atual em formato ISO."""
        from datetime import datetime

        return datetime.now().isoformat()
