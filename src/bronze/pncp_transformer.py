from typing import Any


class PNCPTransformer:
    """
    Classe responsável por transformar os dados brutos retornados
    pela API do PNCP em documentos tratados para persistência.
    """

    @staticmethod
    def _clean_text(value: Any) -> str | None:
        """
        Limpa campos de texto, removendo espaços em branco extras.

        Args:
            value: Valor a ser limpo.

        Returns:
            Texto limpo ou None.
        """
        if value is None:
            return None

        text = str(value).strip()
        return text if text else None

    def transform(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Transforma os registros brutos em documentos padronizados.

        Args:
            records: Lista de registros extraídos da API.

        Returns:
            Lista de documentos tratados.
        """
        transformed_records: list[dict[str, Any]] = []

        for item in records:
            orgao = item.get("orgaoEntidade", {}) or {}
            unidade = item.get("unidadeOrgao", {}) or {}
            amparo = item.get("amparoLegal", {}) or {}

            document = {
                "numero_controle_pncp": self._clean_text(item.get("numeroControlePNCP")),
                "ano_compra": item.get("anoCompra"),
                "sequencial_compra": item.get("sequencialCompra"),
                "numero_compra": self._clean_text(item.get("numeroCompra")),
                "processo": self._clean_text(item.get("processo")),
                "objeto_compra": self._clean_text(item.get("objetoCompra")),
                "valor_total_estimado": item.get("valorTotalEstimado"),
                "valor_total_homologado": item.get("valorTotalHomologado"),
                "modalidade_id": item.get("modalidadeId"),
                "modalidade_nome": self._clean_text(item.get("modalidadeNome")),
                "modo_disputa_id": item.get("modoDisputaId"),
                "modo_disputa_nome": self._clean_text(item.get("modoDisputaNome")),
                "situacao_compra_id": item.get("situacaoCompraId"),
                "situacao_compra_nome": self._clean_text(item.get("situacaoCompraNome")),
                "tipo_instrumento_codigo": item.get("tipoInstrumentoConvocatorioCodigo"),
                "tipo_instrumento_nome": self._clean_text(item.get("tipoInstrumentoConvocatorioNome")),
                "data_inclusao": item.get("dataInclusao"),
                "data_publicacao_pncp": item.get("dataPublicacaoPncp"),
                "data_atualizacao": item.get("dataAtualizacao"),
                "data_atualizacao_global": item.get("dataAtualizacaoGlobal"),
                "data_abertura_proposta": item.get("dataAberturaProposta"),
                "data_encerramento_proposta": item.get("dataEncerramentoProposta"),
                "link_sistema_origem": self._clean_text(item.get("linkSistemaOrigem")),
                "link_processo_eletronico": self._clean_text(item.get("linkProcessoEletronico")),
                "informacao_complementar": self._clean_text(item.get("informacaoComplementar")),
                "justificativa_presencial": self._clean_text(item.get("justificativaPresencial")),
                "usuario_nome": self._clean_text(item.get("usuarioNome")),
                "srp": item.get("srp"),
                "orgao_entidade": {
                    "cnpj": self._clean_text(orgao.get("cnpj")),
                    "razao_social": self._clean_text(orgao.get("razaoSocial")),
                    "poder_id": self._clean_text(orgao.get("poderId")),
                    "esfera_id": self._clean_text(orgao.get("esferaId")),
                },
                "unidade_orgao": {
                    "uf_nome": self._clean_text(unidade.get("ufNome")),
                    "uf_sigla": self._clean_text(unidade.get("ufSigla")),
                    "codigo_unidade": self._clean_text(unidade.get("codigoUnidade")),
                    "municipio_nome": self._clean_text(unidade.get("municipioNome")),
                    "nome_unidade": self._clean_text(unidade.get("nomeUnidade")),
                    "codigo_ibge": self._clean_text(unidade.get("codigoIbge")),
                },
                "amparo_legal": {
                    "codigo": amparo.get("codigo"),
                    "nome": self._clean_text(amparo.get("nome")),
                    "descricao": self._clean_text(amparo.get("descricao")),
                },
            }

            transformed_records.append(document)

        return transformed_records