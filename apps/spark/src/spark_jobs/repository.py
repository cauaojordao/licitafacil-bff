"""
Repositório de dados processados da camada Silver.
Persiste dados enriquecidos no PostgreSQL via Supabase.
"""

from typing import Any

from supabase import Client


class SilverRepository:
    """
    Repositório para persistência de dados enriquecidos na camada Silver.
    Utiliza a tabela public.opportunities do PostgreSQL via Supabase.
    """

    def __init__(self, supabase: Client) -> None:
        """
        Inicializa o repository com cliente Supabase.

        Args:
            supabase: Cliente Supabase já configurado.
        """
        self.supabase = supabase

    def create_indexes(self) -> None:
        """
        Os índices já são criados via DDL no banco.
        Este método existe apenas para manter compatibilidade com a interface anterior.
        """
        pass

    def _map_document_to_row(self, document: dict[str, Any]) -> dict[str, Any]:
        """
        Mapeia documento enriquecido para schema da tabela opportunities.

        Args:
            document: Documento enriquecido da camada Silver.

        Returns:
            Dicionário com campos mapeados para o schema PostgreSQL.
        """
        orgao = document.get("orgao_entidade") or {}
        unidade = document.get("unidade_orgao") or {}

        # Mapeia status para valores aceitos pela constraint
        status_raw = str(document.get("situacao_compra_nome") or "aberto").lower()
        status_map = {
            "aberta": "aberto",
            "aberto": "aberto",
            "encerrada": "encerrado",
            "encerrado": "encerrado",
            "suspensa": "suspenso",
            "suspenso": "suspenso",
            "cancelada": "cancelado",
            "cancelado": "cancelado",
        }
        status = status_map.get(status_raw, "aberto")

        return {
            "pncp_id": str(document.get("numero_controle_pncp") or ""),
            "pncp_url": document.get("link_sistema_origem"),
            "title": str(document.get("objeto_compra") or "")[:500],
            "description": document.get("resumo_simplificado"),
            "object_full": document.get("objeto_compra"),
            "modality": str(document.get("modalidade_nome") or "")[:100],
            "judgement_criterion": (
                str(document.get("criterio_julgamento_nome") or "")[:100]
                if document.get("criterio_julgamento_nome")
                else None
            ),
            "estimated_value": float(document.get("valor_total_estimado") or 0),
            "opening_date": document.get("data_abertura_proposta"),
            "closing_date": document.get("data_encerramento_proposta"),
            "proposals_opening_date": document.get("data_publicacao_pncp"),
            "status": status,
            "agency_name": str(orgao.get("razao_social") or ""),
            "agency_cnpj": str(orgao.get("cnpj") or "")[:14],
            "agency_unit": unidade.get("nome_unidade"),
            "location_city": unidade.get("municipio_nome"),
            "location_state": str(unidade.get("uf_sigla") or "")[:2],
        }

    def upsert(self, document: dict[str, Any]) -> bool:
        """
        Insere ou atualiza um registro na tabela opportunities.

        Args:
            document: Documento enriquecido a ser persistido.

        Returns:
            True se a operação foi bem-sucedida.
        """
        try:
            row = self._map_document_to_row(document)

            # Upsert usando Supabase (on_conflict usa a constraint unique pncp_id)
            self.supabase.table("opportunities").upsert(
                row, on_conflict="pncp_id"
            ).execute()

            return True
        except Exception as e:
            print(
                f"❌ Erro ao fazer upsert de {document.get('numero_controle_pncp')}: {e}"
            )
            return False

    def upsert_many(self, documents: list[dict[str, Any]]) -> int:
        """
        Insere ou atualiza múltiplos registros.

        Args:
            documents: Lista de documentos enriquecidos.

        Returns:
            Quantidade de documentos processados com sucesso.
        """
        if not documents:
            return 0

        try:
            rows = [self._map_document_to_row(doc) for doc in documents]

            # Batch upsert usando Supabase
            self.supabase.table("opportunities").upsert(
                rows, on_conflict="pncp_id"
            ).execute()

            return len(rows)
        except Exception as e:
            print(f"❌ Erro ao fazer upsert em lote: {e}")
            # Fallback: tenta um por um
            processed = 0
            for doc in documents:
                if self.upsert(doc):
                    processed += 1
            return processed

    def close(self) -> None:
        """
        Fecha a conexão com o banco de dados.
        Nota: O cliente Supabase gerencia conexões automaticamente.
        """
        pass
