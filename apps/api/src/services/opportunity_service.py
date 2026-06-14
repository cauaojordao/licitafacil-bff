"""Service para lógica de negócio de oportunidades."""

from datetime import datetime, timezone
from decimal import Decimal

from src.core.logging import get_logger, set_user_id
from src.domain.entities.opportunity import (
    Opportunity,
    OpportunityCompatibility,
)
from src.repositories.opportunity_repository import OpportunityRepository

logger = get_logger(__name__)


_SCORE_CATEGORIES_MAX = 60
_SCORE_LOCATION_MAX = 30
_SCORE_URGENCY_MAX = 10


_LABEL_HIGH = 80
_LABEL_MEDIUM = 60
_LABEL_LOW = 40


_URGENCY_CRITICAL_DAYS = 3
_URGENCY_HIGH_DAYS = 7
_URGENCY_MEDIUM_DAYS = 14

_UNAUTHENTICATED_COMPATIBILITY = OpportunityCompatibility(
    score=50.0,
    label="Não avaliado",
    reasons=["Faça login para ver compatibilidade"],
)


class OpportunityService:
    """
    Service para gerenciar oportunidades com lógica de compatibilidade.
    """

    def __init__(self, opportunity_repo: OpportunityRepository):
        self.opportunity_repo = opportunity_repo
        self._user_profile_cache: dict[str, dict] = {}

    async def _get_user_profile_cached(self, user_id: str | None) -> dict | None:
        """Busca perfil do usuário com cache para otimizar requisições."""
        if not user_id:
            return None

        if user_id not in self._user_profile_cache:
            self._user_profile_cache[user_id] = (
                await self.opportunity_repo.get_user_profile(user_id)
            )

        return self._user_profile_cache[user_id]

    async def get_recommended(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[Opportunity], int]:
        """Retorna oportunidades ordenadas por score de compatibilidade.

        Busca todas as oportunidades abertas, calcula o score de compatibilidade
        para cada uma baseado no perfil do usuário (CNAEs, estados, urgência),
        ordena por score (maior primeiro) e retorna a página solicitada.

        Args:
            user_id: ID do usuário
            page: Número da página
            page_size: Tamanho da página

        Returns:
            Tupla com lista de oportunidades da página e total geral
        """
        all_opportunities = await self.opportunity_repo.find_recommended_for_user(
            user_id, limit=1000
        )

        user_profile = await self._get_user_profile_cached(user_id)

        for opp in all_opportunities:
            self._apply_compatibility(opp, user_profile)
            self._calculate_days_remaining(opp)


        all_opportunities.sort(
            key=lambda o: o.compatibility.score if o.compatibility else 0, reverse=True
        )


        total = len(all_opportunities)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        opportunities = all_opportunities[start_idx:end_idx]

        logger.info(
            "Oportunidades recomendadas carregadas",
            extra_fields={
                "count": len(opportunities),
                "total": total,
                "page": page,
                "page_size": page_size,
            },
        )

        return opportunities, total

    async def search(
        self,
        search: str | None = None,
        state: str | None = None,
        category_id: str | None = None,
        min_value: float | None = None,
        max_value: float | None = None,
        page: int = 1,
        page_size: int = 20,
        user_id: str | None = None,
    ) -> tuple[list[Opportunity], int]:


        opportunities, total = await self.opportunity_repo.search(
            search=search,
            state=state,
            category_id=category_id,
            min_value=Decimal(str(min_value)) if min_value else None,
            max_value=Decimal(str(max_value)) if max_value else None,
            page=page,
            page_size=page_size,
            user_id=user_id,
        )

        user_profile = await self._get_user_profile_cached(user_id)

        for opp in opportunities:
            self._apply_compatibility(opp, user_profile)
            self._calculate_days_remaining(opp)

        logger.info(
            "Busca de oportunidades realizada",
            extra_fields={
                "count": len(opportunities),
                "total": total,
                "has_filters": any([search, state, category_id, min_value, max_value]),
            },
        )

        return opportunities, total

    async def get_by_id(
        self, opportunity_id: str, user_id: str | None = None
    ) -> Opportunity | None:
        set_user_id(user_id or "anonymous")


        opportunity = await self.opportunity_repo.find_by_id(opportunity_id, user_id)

        if not opportunity:
            logger.warning(
                "Oportunidade não encontrada",
                extra_fields={"opportunity_id": opportunity_id},
            )
            return None

        user_profile = await self._get_user_profile_cached(user_id)

        self._apply_compatibility(opportunity, user_profile)
        self._calculate_days_remaining(opportunity)

        logger.info(
            "Detalhes de oportunidade carregados",
            extra_fields={"opportunity_id": opportunity_id},
        )

        return opportunity

    async def get_favorites(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        month: str | None = None,
        valid: bool | None = None,
    ) -> tuple[list[Opportunity], int]:

        opportunities, total = await self.opportunity_repo.find_favorites(
            user_id, page, page_size, month, valid
        )

        user_profile = await self._get_user_profile_cached(user_id)

        for opp in opportunities:
            self._apply_compatibility(opp, user_profile)
            self._calculate_days_remaining(opp)

        logger.info(
            "Favoritos carregados",
            extra_fields={"count": len(opportunities), "total": total},
        )

        return opportunities, total

    async def toggle_favorite(self, user_id: str, opportunity_id: str) -> bool:


        is_favorite = await self.opportunity_repo.toggle_favorite(
            user_id, opportunity_id
        )

        logger.info(
            "Favorito %s" % ("adicionado" if is_favorite else "removido"),
            extra_fields={"opportunity_id": opportunity_id, "is_favorite": is_favorite},
        )

        return is_favorite

    async def get_by_region(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[Opportunity], int]:
        """Retorna oportunidades nas regiões de interesse do usuário."""


        opportunities, total = await self.opportunity_repo.find_by_user_region(
            user_id, page, page_size
        )

        user_profile = await self._get_user_profile_cached(user_id)

        for opp in opportunities:
            self._apply_compatibility(opp, user_profile)
            self._calculate_days_remaining(opp)

        logger.info(
            "Oportunidades por região carregadas",
            extra_fields={"count": len(opportunities), "total": total},
        )

        return opportunities, total

    async def get_by_value(
        self, page: int = 1, page_size: int = 20, user_id: str | None = None
    ) -> tuple[list[Opportunity], int]:
        """Retorna oportunidades ordenadas por valor (maior para menor)."""
        set_user_id(user_id or "anonymous")


        opportunities, total = await self.opportunity_repo.find_by_value(
            page, page_size, user_id
        )

        user_profile = await self._get_user_profile_cached(user_id)

        for opp in opportunities:
            self._apply_compatibility(opp, user_profile)
            self._calculate_days_remaining(opp)

        logger.info(
            "Oportunidades por valor carregadas",
            extra_fields={"count": len(opportunities), "total": total},
        )

        return opportunities, total

    async def get_by_deadline(
        self, page: int = 1, page_size: int = 20, user_id: str | None = None
    ) -> tuple[list[Opportunity], int]:
        """Retorna oportunidades ordenadas por prazo (mais próximo do vencimento)."""
        set_user_id(user_id or "anonymous")


        opportunities, total = await self.opportunity_repo.find_by_deadline(
            page, page_size, user_id
        )

        user_profile = await self._get_user_profile_cached(user_id)

        for opp in opportunities:
            self._apply_compatibility(opp, user_profile)
            self._calculate_days_remaining(opp)

        logger.info(
            "Oportunidades por prazo carregadas",
            extra_fields={"count": len(opportunities), "total": total},
        )

        return opportunities, total

    async def get_monthly_stats(self, month: str) -> dict[str, int | list[dict] | str]:
        """Retorna estatísticas mensais de oportunidades.

        Args:
            month: Mês no formato YYYY-MM

        Returns:
            dict com total_new_opportunities (int),
            top_categories (list) e generated_at (str)
        """
        stats = await self.opportunity_repo.get_monthly_stats(month)


        result: dict[str, int | list[dict] | str] = {
            "total_new_opportunities": stats["total_new_opportunities"],
            "top_categories": stats["top_categories"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        top_categories = result["top_categories"]
        logger.info(
            "Estatísticas mensais calculadas",
            extra_fields={
                "month": month,
                "total": result["total_new_opportunities"],
                "categories_count": len(top_categories) if isinstance(top_categories, list) else 0,
            },
        )

        return result

    def _apply_compatibility(
        self, opportunity: Opportunity, user_profile: dict | None
    ) -> None:
        """Aplica o score de compatibilidade à oportunidade.

        Se o perfil não estiver disponível (usuário não autenticado), usa o valor padrão
        """
        if not user_profile:
            opportunity.compatibility = _UNAUTHENTICATED_COMPATIBILITY.model_copy(
                deep=True
            )
            return
        self._calculate_compatibility(opportunity, user_profile)

    def _calculate_compatibility(
        self, opportunity: Opportunity, user_profile: dict
    ) -> None:
        """Calcula compatibilidade da oportunidade com o perfil do usuário.

        Algoritmo: 60pts categorias + 30pts estado + 10pts urgência.
        """
        score = 0.0
        reasons: list[str] = []

        score, reasons = self._score_categories(
            opportunity, user_profile, score, reasons
        )
        score, reasons = self._score_location(opportunity, user_profile, score, reasons)
        score, reasons = self._score_urgency(opportunity, score, reasons)

        score = min(100.0, max(0.0, score))

        if not reasons:
            reasons.append("Não possui categorias ou estados compatíveis")

        opportunity.compatibility = OpportunityCompatibility(
            score=round(score, 2),
            label=self._get_compatibility_label(score),
            reasons=reasons,
        )

    def _score_categories(
        self,
        opportunity: Opportunity,
        user_profile: dict,
        score: float,
        reasons: list[str],
    ) -> tuple[float, list[str]]:
        user_categories: set[str] = user_profile.get("categories", set())
        opp_categories = {cat.id for cat in opportunity.categories}

        if opp_categories and user_categories:
            matching = opp_categories & user_categories
            if matching:
                score += (len(matching) / len(opp_categories)) * _SCORE_CATEGORIES_MAX
                reasons.append(
                    f"Atende a {len(matching)} categorias compatíveis com seu perfil"
                )

        return score, reasons

    def _score_location(
        self,
        opportunity: Opportunity,
        user_profile: dict,
        score: float,
        reasons: list[str],
    ) -> tuple[float, list[str]]:
        user_states: set[str] = user_profile.get("states", set())

        if opportunity.location_state in user_states:
            score += _SCORE_LOCATION_MAX
            reasons.append(
                f"Localizado em {opportunity.location_state}, seu estado de interesse"
            )

        return score, reasons

    def _score_urgency(
        self, opportunity: Opportunity, score: float, reasons: list[str]
    ) -> tuple[float, list[str]]:
        now = datetime.now(timezone.utc)
        closing = opportunity.closing_date

        if closing.tzinfo is None:
            closing = closing.replace(tzinfo=timezone.utc)

        days = max(0, (closing - now).days)

        if days <= _URGENCY_CRITICAL_DAYS:
            score += _SCORE_URGENCY_MAX
            reasons.append(f"Prazo urgente ({_URGENCY_CRITICAL_DAYS} dias ou menos)")
        elif days <= _URGENCY_HIGH_DAYS:
            score += 7
            reasons.append(f"Prazo curto (até {_URGENCY_HIGH_DAYS} dias)")
        elif days <= _URGENCY_MEDIUM_DAYS:
            score += 5
            reasons.append(f"Prazo próximo (até {_URGENCY_MEDIUM_DAYS} dias)")

        return score, reasons

    def _get_compatibility_label(self, score: float) -> str:
        if score >= _LABEL_HIGH:
            return "Altamente Compatível"
        if score >= _LABEL_MEDIUM:
            return "Compatível"
        if score >= _LABEL_LOW:
            return "Parcialmente Compatível"
        return "Baixa Compatibilidade"

    def _calculate_days_remaining(self, opportunity: Opportunity) -> None:
        """Calcula dias restantes até o fechamento da oportunidade."""
        now = datetime.now(timezone.utc)
        closing = opportunity.closing_date

        if closing.tzinfo is None:
            closing = closing.replace(tzinfo=timezone.utc)

        delta = (closing - now).days
        opportunity.days_remaining = max(0, delta)
