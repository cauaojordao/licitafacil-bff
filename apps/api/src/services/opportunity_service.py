"""Service para lógica de negócio de oportunidades."""

from datetime import UTC, datetime
from decimal import Decimal

from src.core.logging import get_logger, set_user_id
from src.domain.entities.opportunity import (
    Opportunity,
    OpportunityCompatibility,
)
from src.repositories.opportunity_repository import OpportunityRepository

logger = get_logger(__name__)

# Pesos do algoritmo de compatibilidade (somam 100 pontos)
_SCORE_CATEGORIES_MAX = 60
_SCORE_LOCATION_MAX = 30
_SCORE_URGENCY_MAX = 10

# Thresholds de classificação (score ≥ threshold → label)
_LABEL_HIGH = 80
_LABEL_MEDIUM = 60
_LABEL_LOW = 40

# Janelas de urgência em dias
_URGENCY_CRITICAL_DAYS = 3
_URGENCY_HIGH_DAYS = 7
_URGENCY_MEDIUM_DAYS = 14

_UNAUTHENTICATED_COMPATIBILITY = OpportunityCompatibility(
    score=50.0,
    label="Não avaliado",
    reasons=["Faça login para ver compatibilidade"],
)


class OpportunityService:
    """Service para gerenciar oportunidades com lógica de compatibilidade."""

    def __init__(self, opportunity_repo: OpportunityRepository):
        self.opportunity_repo = opportunity_repo

    async def get_recommended(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[Opportunity], int]:
        # removed duplicate call

        opportunities, total = await self.opportunity_repo.find_recommended_for_user(
            user_id, page, page_size
        )

        user_profile = await self.opportunity_repo.get_user_profile(user_id)

        for opp in opportunities:
            self._calculate_compatibility(opp, user_profile)
            self._calculate_days_remaining(opp)

        opportunities.sort(
            key=lambda o: o.compatibility.score if o.compatibility else 0, reverse=True
        )

        logger.info(
            "Oportunidades recomendadas carregadas",
            extra_fields={"count": len(opportunities), "total": total, "page": page},
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
        # removed duplicate call

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

        user_profile = (
            await self.opportunity_repo.get_user_profile(user_id) if user_id else None
        )

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
        set_user_id(user_id or "anonymous")  #
        # removed duplicate call

        opportunity = await self.opportunity_repo.find_by_id(opportunity_id, user_id)

        if not opportunity:
            logger.warning(
                "Oportunidade não encontrada",
                extra_fields={"opportunity_id": opportunity_id},
            )
            return None

        user_profile = (
            await self.opportunity_repo.get_user_profile(user_id) if user_id else None
        )

        self._apply_compatibility(opportunity, user_profile)
        self._calculate_days_remaining(opportunity)

        logger.info(
            "Detalhes de oportunidade carregados",
            extra_fields={"opportunity_id": opportunity_id},
        )

        return opportunity

    async def get_favorites(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[Opportunity], int]:
        # removed duplicate call

        opportunities, total = await self.opportunity_repo.find_favorites(
            user_id, page, page_size
        )

        user_profile = await self.opportunity_repo.get_user_profile(user_id)

        for opp in opportunities:
            self._calculate_compatibility(opp, user_profile)
            self._calculate_days_remaining(opp)

        logger.info(
            "Favoritos carregados",
            extra_fields={"count": len(opportunities), "total": total},
        )

        return opportunities, total

    async def toggle_favorite(self, user_id: str, opportunity_id: str) -> bool:
        # removed duplicate call

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
        # removed duplicate call

        opportunities, total = await self.opportunity_repo.find_by_user_region(
            user_id, page, page_size
        )

        user_profile = await self.opportunity_repo.get_user_profile(user_id)

        for opp in opportunities:
            self._calculate_compatibility(opp, user_profile)
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
        set_user_id(user_id or "anonymous")  #
        # removed duplicate call

        opportunities, total = await self.opportunity_repo.find_by_value(
            page, page_size, user_id
        )

        user_profile = (
            await self.opportunity_repo.get_user_profile(user_id) if user_id else None
        )

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
        set_user_id(user_id or "anonymous")  #
        # removed duplicate call

        opportunities, total = await self.opportunity_repo.find_by_deadline(
            page, page_size, user_id
        )

        user_profile = (
            await self.opportunity_repo.get_user_profile(user_id) if user_id else None
        )

        for opp in opportunities:
            self._apply_compatibility(opp, user_profile)
            self._calculate_days_remaining(opp)

        logger.info(
            "Oportunidades por prazo carregadas",
            extra_fields={"count": len(opportunities), "total": total},
        )

        return opportunities, total

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
        now = datetime.now(UTC)
        closing = opportunity.closing_date

        if closing.tzinfo is None:
            closing = closing.replace(tzinfo=UTC)

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
        now = datetime.now(UTC)
        closing = opportunity.closing_date

        if closing.tzinfo is None:
            closing = closing.replace(tzinfo=UTC)

        delta = (closing - now).days
        opportunity.days_remaining = max(0, delta)
