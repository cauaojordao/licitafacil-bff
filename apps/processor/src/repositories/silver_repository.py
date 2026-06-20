"""
Repositório de dados processados da camada Silver.
Persiste dados enriquecidos no PostgreSQL via Supabase.
"""

import logging
import re
import unicodedata
from typing import Any, cast

from supabase import Client

logger = logging.getLogger(__name__)


def _slugify(value: str) -> str:
    value = value or "outros"
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "outros"


def _normalize_cnae(code: str) -> str:
    return re.sub(r"\D", "", code or "")


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
        "proposals_opening_date": (
            document.get("data_abertura_proposta")
            or document.get("data_publicacao_pncp")
        ),
        "status": _map_status(document),
        "agency_name": str(orgao.get("razao_social") or "Não informado"),
        "agency_cnpj": str(orgao.get("cnpj") or "")[:14],
        "agency_unit": unidade.get("nome_unidade"),
        "location_city": unidade.get("municipio_nome"),
        "location_state": str(unidade.get("uf_sigla") or "NA")[:2],
    }


class SilverRepository:
    def __init__(self, supabase: Client) -> None:
        self.supabase = supabase

    def create_indexes(self) -> None:
        pass

    def _get_opportunity_id(self, pncp_id: str) -> str | None:
        response = (
            self.supabase.table("opportunities")
            .select("id")
            .eq("pncp_id", pncp_id)
            .limit(1)
            .execute()
        )

        if response is None or not response.data:
            return None

        return cast(str | None, response.data[0].get("id"))

    def _get_or_create_category(self, name: str) -> str | None:
        name = name or "Outros"
        slug = _slugify(name)

        response = (
            self.supabase.table("categories")
            .select("id")
            .eq("slug", slug)
            .limit(1)
            .execute()
        )

        if response is not None and response.data:
            return cast(str | None, response.data[0].get("id"))

        insert_response = (
            self.supabase.table("categories")
            .insert(
                {
                    "name": name,
                    "slug": slug,
                    "description": name,
                }
            )
            .execute()
        )

        if insert_response is None or not insert_response.data:
            return None

        return cast(str | None, insert_response.data[0].get("id"))

    def _get_category_ids_by_cnae_ids(self, cnae_ids: list[str]) -> list[str]:
        if not cnae_ids:
            return []

        response = (
            self.supabase.table("cnae_categories")
            .select("category_id")
            .in_("cnae_id", cnae_ids)
            .execute()
        )

        if response is None or not response.data:
            return []

        return [row["category_id"] for row in response.data if row.get("category_id")]

    def _link_opportunity_category_by_id(
        self,
        opportunity_id: str,
        category_id: str,
        is_primary: bool = False,
    ) -> None:
        if not opportunity_id or not category_id:
            return

        response = (
            self.supabase.table("opportunity_categories")
            .upsert(
                {
                    "opportunity_id": opportunity_id,
                    "category_id": category_id,
                    "is_primary": is_primary,
                },
                on_conflict="opportunity_id,category_id",
            )
            .execute()
        )

        if response is None:
            logger.warning(
                "Supabase retornou None ao vincular categoria %s",
                category_id,
            )

    def _link_opportunity_categories_from_cnaes(
        self,
        pncp_id: str,
        categorias_cnae: list[dict],
    ) -> None:
        try:
            opportunity_id = self._get_opportunity_id(pncp_id)

            if not opportunity_id:
                logger.warning("Opportunity não encontrada para PNCP %s", pncp_id)
                return

            cnae_ids = []

            for item in categorias_cnae or []:
                codigo = _normalize_cnae(str(item.get("codigo") or ""))
                if codigo:
                    cnae_ids.append(codigo)

            cnae_ids = list(dict.fromkeys(cnae_ids))

            category_ids = self._get_category_ids_by_cnae_ids(cnae_ids)

            if not category_ids:
                category_name = (
                    str(categorias_cnae[0].get("descricao"))
                    if categorias_cnae
                    else "Outros"
                )

                category_id = self._get_or_create_category(category_name)

                if category_id:
                    self._link_opportunity_category_by_id(
                        opportunity_id=opportunity_id,
                        category_id=category_id,
                        is_primary=True,
                    )

                return

            for index, category_id in enumerate(category_ids):
                self._link_opportunity_category_by_id(
                    opportunity_id=opportunity_id,
                    category_id=category_id,
                    is_primary=index == 0,
                )

        except Exception as e:
            logger.error(
                "Erro ao vincular categorias CNAE de %s: %s",
                pncp_id,
                e,
            )

    def _upsert_attachments(
        self,
        pncp_id: str,
        document: dict[str, Any],
    ) -> None:
        opportunity_id = self._get_opportunity_id(pncp_id)

        if not opportunity_id:
            return

        attachments = (
            document.get("anexos")
            or document.get("documentos")
            or document.get("attachments")
            or []
        )

        if not isinstance(attachments, list) or not attachments:
            return

        rows = []

        for item in attachments:
            if not isinstance(item, dict):
                continue

            url = (
                item.get("url")
                or item.get("link")
                or item.get("uri")
                or item.get("linkDownload")
            )

            if not url:
                continue

            rows.append(
                {
                    "opportunity_id": opportunity_id,
                    "name": (
                        item.get("name")
                        or item.get("nome")
                        or item.get("titulo")
                        or "Anexo"
                    ),
                    "url": url,
                    "size_bytes": item.get("size_bytes") or item.get("tamanho"),
                    "mime_type": item.get("mime_type") or "application/pdf",
                }
            )

        if rows:
            self.supabase.table("opportunity_attachments").upsert(
                rows,
                on_conflict="opportunity_id,url",
            ).execute()

    def upsert(self, document: dict[str, Any]) -> bool:
        try:
            row = _map_document_to_row(document)

            if not row["pncp_id"]:
                return False

            self.supabase.table("opportunities").upsert(
                row,
                on_conflict="pncp_id",
            ).execute()

            self._link_opportunity_categories_from_cnaes(
                pncp_id=row["pncp_id"],
                categorias_cnae=document.get("categorias_cnae") or [],
            )

            self._upsert_attachments(
                pncp_id=row["pncp_id"],
                document=document,
            )

            return True

        except Exception as e:
            logger.error(
                "Erro ao fazer upsert de %s: %s",
                document.get("numero_controle_pncp"),
                e,
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
            rows = [row for row in rows if row.get("pncp_id")]

            if not rows:
                return 0

            self.supabase.table("opportunities").upsert(
                rows,
                on_conflict="pncp_id",
            ).execute()

            logger.info("Upsert opportunities OK: %s", len(rows))

            for doc in documents:
                pncp_id = str(doc.get("numero_controle_pncp") or "")

                if not pncp_id:
                    continue

                try:
                    self._link_opportunity_categories_from_cnaes(
                        pncp_id=pncp_id,
                        categorias_cnae=doc.get("categorias_cnae") or [],
                    )
                except Exception as e:
                    logger.error(
                        "Erro ao vincular CNAEs de %s: %s",
                        pncp_id,
                        e,
                    )

                try:
                    self._upsert_attachments(
                        pncp_id=pncp_id,
                        document=doc,
                    )
                except Exception as e:
                    logger.error(
                        "Erro ao salvar anexos de %s: %s",
                        pncp_id,
                        e,
                    )

            return len(rows)

        except Exception as e:
            logger.error("Erro ao fazer upsert em lote: %s", e)

            processed = 0

            for doc in documents:
                if self.upsert(doc):
                    processed += 1

            return processed

    def close(self) -> None:
        pass
