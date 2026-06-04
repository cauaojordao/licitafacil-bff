"""Repository para operações com oportunidades/editais."""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Any

from supabase import Client

from src.core.logging import get_logger
from src.domain.entities.opportunity import (
    Opportunity,
    OpportunityAgency,
    OpportunityCategory,
)

logger = get_logger(__name__)


class OpportunityRepository:
    """Repository para gerenciar oportunidades."""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    @staticmethod
    def _normalize_pagination(page: int, page_size: int) -> tuple[int, int, int]:
        """Normaliza parâmetros de paginação e devolve (page, page_size, offset)."""
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        offset = (page - 1) * page_size
        return page, page_size, offset

    @staticmethod
    def _sanitize_filter_value(value: str) -> str:
        """Escapa caracteres especiais de ilike e da sintaxe de filtro PostgREST."""
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    async def _execute(self, query: Any) -> Any:
        """Executa uma query síncrona do Supabase em thread pool."""
        return await asyncio.to_thread(query.execute)

    async def _fetch_categories_batch(
        self, opportunity_ids: list[str]
    ) -> dict[str, list[OpportunityCategory]]:
        """Busca categorias de múltiplas oportunidades em uma única query."""
        if not opportunity_ids:
            return {}

        response = await self._execute(
            self.supabase.table("opportunity_categories")
            .select("opportunity_id, categories(id, name, slug)")
            .in_("opportunity_id", opportunity_ids)
        )

        result: dict[str, list[OpportunityCategory]] = {
            opp_id: [] for opp_id in opportunity_ids
        }
        for row in response.data:
            if row.get("categories"):
                result[row["opportunity_id"]].append(
                    OpportunityCategory(**row["categories"])
                )

        return result

    async def _fetch_favorites_batch(
        self, opportunity_ids: list[str], user_id: str
    ) -> set[str]:
        """Retorna o conjunto de IDs de editais favoritados pelo usuário."""
        if not opportunity_ids:
            return set()

        response = await self._execute(
            self.supabase.table("user_favorite_opportunities")
            .select("opportunity_id")
            .eq("user_id", user_id)
            .in_("opportunity_id", opportunity_ids)
        )
        return {row["opportunity_id"] for row in response.data}

    async def _build_opportunities_from_rows(
        self,
        rows: list[dict],
        user_id: str | None = None,
        all_favorites: bool = False,
    ) -> list[Opportunity]:
        """Monta objetos Opportunity a partir de linhas do banco, carregando
        categorias e favoritos em queries em lote para evitar N+1.
        """
        if not rows:
            return []

        opp_ids = [row["id"] for row in rows]
        categories_by_id = await self._fetch_categories_batch(opp_ids)

        favorites: set[str] = set()
        if all_favorites:
            favorites = set(opp_ids)
        elif user_id:
            favorites = await self._fetch_favorites_batch(opp_ids, user_id)

        return [
            self._row_to_opportunity(
                row,
                categories=categories_by_id.get(row["id"], []),
                is_favorite=row["id"] in favorites,
            )
            for row in rows
        ]

    async def find_by_id(
        self, opportunity_id: str, user_id: str | None = None
    ) -> Opportunity | None:
        try:
            response = await self._execute(
                self.supabase.table("opportunities")
                .select("*")
                .eq("id", opportunity_id)
                .maybe_single()
            )

            if not response or not response.data:
                return None

            opportunities = await self._build_opportunities_from_rows(
                [response.data], user_id=user_id
            )
            return opportunities[0] if opportunities else None

        except Exception:
            logger.error(
                "Erro ao buscar oportunidade",
                extra_fields={"opportunity_id": opportunity_id},
                exc_info=True,
            )
            return None

    async def search(
        self,
        search: str | None = None,
        state: str | None = None,
        category_id: str | None = None,
        min_value: Decimal | None = None,
        max_value: Decimal | None = None,
        status: str | None = "aberto",
        page: int = 1,
        page_size: int = 20,
        user_id: str | None = None,
    ) -> tuple[list[Opportunity], int]:
        page, page_size, offset = self._normalize_pagination(page, page_size)

        query = self.supabase.table("opportunities").select("*", count="exact")

        if status:
            query = query.eq("status", status)
        if state:
            query = query.eq("location_state", state)
        if min_value is not None:
            query = query.gte("estimated_value", float(min_value))
        if max_value is not None:
            query = query.lte("estimated_value", float(max_value))
        if search:
            safe = self._sanitize_filter_value(search)
            query = query.or_(
                f"title.ilike.%{safe}%,description.ilike.%{safe}%,object_full.ilike.%{safe}%"
            )
        if category_id:
            opp_cat_response = await self._execute(
                self.supabase.table("opportunity_categories")
                .select("opportunity_id")
                .eq("category_id", category_id)
            )
            ids = [row["opportunity_id"] for row in opp_cat_response.data]
            if not ids:
                return [], 0
            query = query.in_("id", ids)

        response = await self._execute(
            query.order("closing_date", desc=False).range(
                offset, offset + page_size - 1
            )
        )

        opportunities = await self._build_opportunities_from_rows(
            response.data, user_id=user_id
        )
        return opportunities, response.count or 0

    async def find_recommended_for_user(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Opportunity], int]:
        page, page_size, offset = self._normalize_pagination(page, page_size)

        user_cnaes_response = await self._execute(
            self.supabase.table("user_cnaes").select("cnae_id").eq("user_id", user_id)
        )
        user_cnae_ids = [row["cnae_id"] for row in user_cnaes_response.data]
        if not user_cnae_ids:
            return [], 0

        cnae_cats_response = await self._execute(
            self.supabase.table("cnae_categories")
            .select("category_id")
            .in_("cnae_id", user_cnae_ids)
        )
        user_category_ids = {row["category_id"] for row in cnae_cats_response.data}
        if not user_category_ids:
            return [], 0

        user_states_response = await self._execute(
            self.supabase.table("user_interested_states")
            .select("state_id")
            .eq("user_id", user_id)
        )
        user_state_ids = [row["state_id"] for row in user_states_response.data]

        opp_cats_response = await self._execute(
            self.supabase.table("opportunity_categories")
            .select("opportunity_id")
            .in_("category_id", list(user_category_ids))
        )
        opportunity_ids = {row["opportunity_id"] for row in opp_cats_response.data}
        if not opportunity_ids:
            return [], 0

        query = (
            self.supabase.table("opportunities")
            .select("*", count="exact")
            .in_("id", list(opportunity_ids))
            .eq("status", "aberto")
        )
        if user_state_ids:
            query = query.in_("location_state", user_state_ids)

        response = await self._execute(
            query.order("closing_date", desc=False).range(
                offset, offset + page_size - 1
            )
        )

        opportunities = await self._build_opportunities_from_rows(
            response.data, user_id=user_id
        )
        return opportunities, response.count or 0

    async def find_favorites(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        month: str | None = None,
        valid: bool | None = None,
    ) -> tuple[list[Opportunity], int]:
        """Busca favoritos do usuário com filtros opcionais.

        Args:
            user_id: ID do usuário
            page: Número da página
            page_size: Itens por página
            month: Filtro mensal no formato YYYY-MM (baseado em created_at do favorito)
            valid: Filtro de validade (True=válidos, False=expirados, None=todos)
        """
        page, page_size, offset = self._normalize_pagination(page, page_size)

        fav_response = await self._execute(
            self.supabase.table("user_favorite_opportunities")
            .select("opportunity_id", count="exact")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + page_size - 1)
        )
        total = fav_response.count or 0
        if total == 0:
            return [], 0

        opportunity_ids = [row["opportunity_id"] for row in fav_response.data]

        query = (
            self.supabase.table("opportunities")
            .select("*")
            .in_("id", opportunity_ids)
        )

        # Filtro mensal: baseado no created_at da oportunidade
        if month:
            # Formato YYYY-MM -> range de datas
            start_date = f"{month}-01"
            # Último dia do mês (aproximado, usa próximo mês dia 01)
            year, month_num = month.split("-")
            next_month = int(month_num) + 1
            next_year = year
            if next_month > 12:
                next_month = 1
                next_year = str(int(year) + 1)
            end_date = f"{next_year}-{next_month:02d}-01"

            query = query.gte("created_at", start_date).lt("created_at", end_date)

        # Filtro de validade: baseado no closing_date
        if valid is not None:
            from datetime import UTC, datetime

            now = datetime.now(UTC).isoformat()
            if valid:
                # Válidos: closing_date >= now
                query = query.gte("closing_date", now)
            else:
                # Expirados: closing_date < now
                query = query.lt("closing_date", now)

        response = await self._execute(query.order("closing_date", desc=False))

        opportunities = await self._build_opportunities_from_rows(
            response.data, all_favorites=True
        )
        return opportunities, total

    async def toggle_favorite(self, user_id: str, opportunity_id: str) -> bool:
        try:
            response = await self._execute(
                self.supabase.table("user_favorite_opportunities")
                .select("opportunity_id")
                .eq("user_id", user_id)
                .eq("opportunity_id", opportunity_id)
                .maybe_single()
            )

            if response and response.data:
                await self._execute(
                    self.supabase.table("user_favorite_opportunities")
                    .delete()
                    .eq("user_id", user_id)
                    .eq("opportunity_id", opportunity_id)
                )
                logger.info(
                    "Favorito removido",
                    extra_fields={"opportunity_id": opportunity_id},
                )
                return False

            await self._execute(
                self.supabase.table("user_favorite_opportunities").insert(
                    {"user_id": user_id, "opportunity_id": opportunity_id}
                )
            )
            logger.info(
                "Favorito adicionado",
                extra_fields={"opportunity_id": opportunity_id},
            )
            return True

        except Exception:
            logger.error(
                "Erro ao alternar favorito",
                extra_fields={"opportunity_id": opportunity_id},
                exc_info=True,
            )
            raise

    async def find_by_user_region(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Opportunity], int]:
        """Busca oportunidades nas regiões (estados) de interesse do usuário."""
        page, page_size, offset = self._normalize_pagination(page, page_size)

        user_states_response = await self._execute(
            self.supabase.table("user_interested_states")
            .select("state_id")
            .eq("user_id", user_id)
        )
        user_state_ids = [row["state_id"] for row in user_states_response.data]
        if not user_state_ids:
            return [], 0

        response = await self._execute(
            self.supabase.table("opportunities")
            .select("*", count="exact")
            .in_("location_state", user_state_ids)
            .eq("status", "aberto")
            .order("created_at", desc=True)
            .range(offset, offset + page_size - 1)
        )

        opportunities = await self._build_opportunities_from_rows(
            response.data, user_id=user_id
        )
        return opportunities, response.count or 0

    async def find_by_value(
        self,
        page: int = 1,
        page_size: int = 20,
        user_id: str | None = None,
    ) -> tuple[list[Opportunity], int]:
        """Busca oportunidades ordenadas por valor (maior para menor)."""
        page, page_size, offset = self._normalize_pagination(page, page_size)

        response = await self._execute(
            self.supabase.table("opportunities")
            .select("*", count="exact")
            .eq("status", "aberto")
            .order("estimated_value", desc=True)
            .range(offset, offset + page_size - 1)
        )

        opportunities = await self._build_opportunities_from_rows(
            response.data, user_id=user_id
        )
        return opportunities, response.count or 0

    async def find_by_deadline(
        self,
        page: int = 1,
        page_size: int = 20,
        user_id: str | None = None,
    ) -> tuple[list[Opportunity], int]:
        """Busca oportunidades ordenadas por prazo"""
        page, page_size, offset = self._normalize_pagination(page, page_size)

        response = await self._execute(
            self.supabase.table("opportunities")
            .select("*", count="exact")
            .eq("status", "aberto")
            .order("closing_date", desc=False)
            .range(offset, offset + page_size - 1)
        )

        opportunities = await self._build_opportunities_from_rows(
            response.data, user_id=user_id
        )
        return opportunities, response.count or 0

    async def get_user_profile(self, user_id: str) -> dict:
        """Retorna perfil resumido do usuário para cálculo de compatibilidade.

        Retorna {"categories": set[str], "states": set[str]}.
        """
        user_cnaes_task = self._execute(
            self.supabase.table("user_cnaes").select("cnae_id").eq("user_id", user_id)
        )
        user_states_task = self._execute(
            self.supabase.table("user_interested_states")
            .select("state_id")
            .eq("user_id", user_id)
        )
        
        user_cnaes_response, user_states_response = await asyncio.gather(
            user_cnaes_task, user_states_task
        )
        
        user_cnae_ids = [row["cnae_id"] for row in user_cnaes_response.data]
        user_states: set[str] = {row["state_id"] for row in user_states_response.data}

        user_categories: set[str] = set()
        if user_cnae_ids:
            cnae_cats_response = await self._execute(
                self.supabase.table("cnae_categories")
                .select("category_id")
                .in_("cnae_id", user_cnae_ids)
            )
            user_categories = {row["category_id"] for row in cnae_cats_response.data}

        return {"categories": user_categories, "states": user_states}

    async def get_monthly_stats(
        self, month: str
    ) -> dict[str, int | list[dict[str, str | int]]]:
        """Retorna estatísticas mensais de oportunidades.

        Args:
            month: Mês no formato YYYY-MM

        Returns:
            dict com total_new_opportunities e top_categories
        """
        year, month_num = month.split("-")
        start_date = f"{month}-01"
        next_month = int(month_num) + 1
        next_year = year
        if next_month > 12:
            next_month = 1
            next_year = str(int(year) + 1)
        end_date = f"{next_year}-{next_month:02d}-01"

        count_response = await self._execute(
            self.supabase.table("opportunities")
            .select("*", count="exact")
            .gte("created_at", start_date)
            .lt("created_at", end_date)
        )
        total_new = count_response.count or 0

        opps_response = await self._execute(
            self.supabase.table("opportunities")
            .select("id")
            .gte("created_at", start_date)
            .lt("created_at", end_date)
        )
        opportunity_ids = [row["id"] for row in opps_response.data]

        top_categories: list[dict[str, str | int]] = []
        if opportunity_ids:
            cat_response = await self._execute(
                self.supabase.table("opportunity_categories")
                .select("category_id, categories(id, name, slug)")
                .in_("opportunity_id", opportunity_ids)
            )

            category_counts: dict[str, dict[str, str | int]] = {}
            for row in cat_response.data:
                if row.get("categories"):
                    cat_id = row["categories"]["id"]
                    if cat_id not in category_counts:
                        category_counts[cat_id] = {
                            "id": cat_id,
                            "name": row["categories"]["name"],
                            "slug": row["categories"]["slug"],
                            "count": 0,
                        }
                    # Incrementar count com cast explícito
                    current_count = category_counts[cat_id]["count"]
                    category_counts[cat_id]["count"] = int(current_count) + 1  # type: ignore

            # Ordenar por count e pegar top 5
            sorted_cats = sorted(
                category_counts.values(),
                key=lambda x: int(x["count"]),  # type: ignore
                reverse=True,
            )
            top_categories = sorted_cats[:5]

        return {"total_new_opportunities": total_new, "top_categories": top_categories}

    def _row_to_opportunity(
        self,
        row: dict,
        categories: list[OpportunityCategory],
        is_favorite: bool,
    ) -> Opportunity:
        agency = OpportunityAgency(
            name=row["agency_name"],
            cnpj=row["agency_cnpj"],
            unit=row.get("agency_unit"),
        )

        return Opportunity(
            id=row["id"],
            pncp_id=row["pncp_id"],
            pncp_url=row.get("pncp_url"),
            title=row["title"],
            description=row.get("description"),
            object_full=row.get("object_full"),
            modality=row["modality"],
            judgement_criterion=row.get("judgement_criterion"),
            estimated_value=Decimal(str(row["estimated_value"])),
            opening_date=datetime.fromisoformat(row["opening_date"]),
            closing_date=datetime.fromisoformat(row["closing_date"]),
            proposals_opening_date=(
                datetime.fromisoformat(row["proposals_opening_date"])
                if row.get("proposals_opening_date")
                else None
            ),
            status=row["status"],
            agency=agency,
            location_city=row.get("location_city"),
            location_state=row["location_state"],
            created_at=(
                datetime.fromisoformat(row["created_at"])
                if row.get("created_at")
                else None
            ),
            updated_at=(
                datetime.fromisoformat(row["updated_at"])
                if row.get("updated_at")
                else None
            ),
            categories=categories,
            is_favorite=is_favorite,
        )
