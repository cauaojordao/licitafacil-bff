"""
Repositório de dados processados da camada Silver.
Persiste dados enriquecidos no PostgreSQL via Supabase.
"""

import re
import unicodedata
from typing import Any

from supabase import Client


def _slugify(value: str) -> str:
    value = value or "outros"
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "outros"


def _map_status(document: dict[str, Any]) -> str:
    status_raw = str(document.get("situacao_compra_nome") or "").lower()

    status_map = {
        "aberta": "aberto",
        "aberto": "aberto",
        "divulgada no pncp": "aberto",
        "recebendo proposta": "aberto",
        "encerrada": "encerrado",
        "encerrado": "encerrado",
        "suspensa": "suspenso",
        "suspenso": "suspenso",
        "cancelada": "cancelado",
        "cancelado": "cancelado",
    }

    return status_map.get(status_raw, "aberto")


def _map_document_to_row(document: dict[str, Any]) -> dict[str, Any]:
    orgao = document.get("orgao_entidade") or {}
    unidade = document.get("unidade_orgao") or {}

    return {
        "pncp_id": str(document.get("numero_controle_pncp") or ""),
        "pncp_url": document.get("link_sistema_origem"),
        "title": str(document.get("objeto_compra") or "")[:500],
        "description": document.get("resumo_simplificado"),
        "object_full": document.get("objeto_compra"),
        "modality": str(document.get("modalidade_nome") or "Não informado")[:100],
        "judgement_criterion": (
            str(document.get("criterio_julgamento_nome") or "")[:100]
            if document.get("criterio_julgamento_nome")
            else None
        ),
        "estimated_value": float(document.get("valor_total_estimado") or 0),
        "opening_date": (
            document.get("data_abertura_proposta")
            or document.get("data_publicacao_pncp")
        ),
        "closing_date": (
            document.get("data_encerramento_proposta")
            or document.get("data_publicacao_pncp")
        ),
        "proposals_opening_date": document.get("data_publicacao_pncp"),
        "status": _map_status(document),
        "agency_name": str(orgao.get("razao_social") or "Não informado"),
        "agency_cnpj": str(orgao.get("cnpj") or "")[:14],
        "agency_unit": unidade.get("nome_unidade"),
        "location_city": unidade.get("municipio_nome"),
        "location_state": str(unidade.get("uf_sigla") or "NA")[:2],
    }


class SilverRepository:
    """
    Repositório para persistência de dados enriquecidos na camada Silver.
    """

    def __init__(self, supabase: Client) -> None:
        self.supabase = supabase

    def create_indexes(self) -> None:
        pass

    def _get_opportunity_id(self, pncp_id: str) -> str | None:
        result = (
            self.supabase.table("opportunities")
            .select("id")
            .eq("pncp_id", pncp_id)
            .execute()
        )

        if not result.data:
            return None

        return result.data[0]["id"]

    def _get_or_create_category(self, category_name: str) -> str | None:
        category_name = category_name or "outros"
        slug = _slugify(category_name)

        result = (
            self.supabase.table("categories")
            .select("id")
            .eq("slug", slug)
            .execute()
        )

        if result.data:
            return result.data[0]["id"]

        created = (
            self.supabase.table("categories")
            .insert(
                {
                    "name": category_name,
                    "slug": slug,
                    "description": (
                        f"Categoria classificada automaticamente pela camada Silver: "
                        f"{category_name}"
                    ),
                }
            )
            .execute()
        )

        if not created.data:
            return None

        return created.data[0]["id"]

    def _link_opportunity_category(
        self,
        pncp_id: str,
        category_name: str,
        is_primary: bool = True,
    ) -> None:
        opportunity_id = self._get_opportunity_id(pncp_id)

        if not opportunity_id:
            print(f"⚠️ Opportunity não encontrada para PNCP {pncp_id}")
            return

        category_id = self._get_or_create_category(category_name)

        if not category_id:
            print(f"⚠️ Categoria não encontrada/criada: {category_name}")
            return

        self.supabase.table("opportunity_categories").upsert(
            {
                "opportunity_id": opportunity_id,
                "category_id": category_id,
                "is_primary": is_primary,
            },
            on_conflict="opportunity_id,category_id",
        ).execute()

    def upsert(self, document: dict[str, Any]) -> bool:
        try:
            row = _map_document_to_row(document)

            self.supabase.table("opportunities").upsert(
                row,
                on_conflict="pncp_id",
            ).execute()

            self._link_opportunity_category(
                pncp_id=row["pncp_id"],
                category_name=document.get("categoria_ia") or "outros",
                is_primary=True,
            )

            return True

        except Exception as e:
            print(
                f"❌ Erro ao fazer upsert de "
                f"{document.get('numero_controle_pncp')}: {e}"
            )
            return False

    def upsert_many(self, documents: list[dict[str, Any]]) -> int:
        if not documents:
            return 0

        unique_documents = {
            doc.get("numero_controle_pncp"): doc
            for doc in documents
            if doc.get("numero_controle_pncp")
        }

        documents = list(unique_documents.values())

        try:
            rows = [_map_document_to_row(doc) for doc in documents]

            self.supabase.table("opportunities").upsert(
                rows,
                on_conflict="pncp_id",
            ).execute()

            for doc in documents:
                self._link_opportunity_category(
                    pncp_id=str(doc.get("numero_controle_pncp")),
                    category_name=doc.get("categoria_ia") or "outros",
                    is_primary=True,
                )

            return len(rows)

        except Exception as e:
            print(f"❌ Erro ao fazer upsert em lote: {e}")

            processed = 0
            for doc in documents:
                if self.upsert(doc):
                    processed += 1

            return processed

    def close(self) -> None:
        pass