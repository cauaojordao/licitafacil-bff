"""Rotas de oportunidades/editais."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client

from src.core.dependencies import (
    get_current_user,
    get_supabase_client,
)
from src.domain.entities.opportunity import Opportunity
from src.domain.entities.user import User
from src.domain.schemas.opportunity import (
    CategoryStatsResponse,
    FavoriteToggleResponse,
    MonthlyStatsResponse,
    OpportunityAgencyResponse,
    OpportunityCategoryResponse,
    OpportunityCompatibilityResponse,
    OpportunityDetailResponse,
    OpportunityResponse,
    OpportunitySearchResponse,
)
from src.repositories.opportunity_repository import OpportunityRepository
from src.services.opportunity_service import OpportunityService

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


def get_opportunity_service(
    supabase: Client = Depends(get_supabase_client),
) -> OpportunityService:
    repo = OpportunityRepository(supabase)
    return OpportunityService(repo)


@router.get("/recommended", response_model=OpportunitySearchResponse)
async def get_recommended_opportunities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    current_user: User = Depends(get_current_user),
    service: OpportunityService = Depends(get_opportunity_service),
) -> OpportunitySearchResponse:
    opportunities, total = await service.get_recommended(
        current_user.id, page, page_size
    )

    items = [_opp_to_response(opp) for opp in opportunities]

    return OpportunitySearchResponse(
        items=items, page=page, pageSize=page_size, total=total
    )


@router.get("/favorites/list", response_model=OpportunitySearchResponse)
async def get_favorite_opportunities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    month: str | None = Query(
        None,
        pattern=r"^\d{4}-\d{2}$",
        description="Filtro mensal no formato YYYY-MM",
    ),
    valid: bool | None = Query(
        None,
        description="Filtro de validade (true=válidos, false=expirados)",
    ),
    current_user: User = Depends(get_current_user),
    service: OpportunityService = Depends(get_opportunity_service),
) -> OpportunitySearchResponse:
    """Lista editais favoritos do usuário com filtros opcionais.

    Args:
        page: Número da página
        page_size: Itens por página
        month: Filtro mensal (YYYY-MM) - retorna favoritos criados naquele mês
        valid: Filtro de validade - true para válidos, false para expirados
    """
    opportunities, total = await service.get_favorites(
        current_user.id, page, page_size, month, valid
    )

    items = [_opp_to_response(opp) for opp in opportunities]

    return OpportunitySearchResponse(
        items=items, page=page, pageSize=page_size, total=total
    )


@router.get("/region", response_model=OpportunitySearchResponse)
async def get_opportunities_by_region(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    current_user: User = Depends(get_current_user),
    service: OpportunityService = Depends(get_opportunity_service),
) -> OpportunitySearchResponse:
    """Busca oportunidades nas regiões (estados) de interesse do usuário."""
    opportunities, total = await service.get_by_region(current_user.id, page, page_size)

    items = [_opp_to_response(opp) for opp in opportunities]

    return OpportunitySearchResponse(
        items=items, page=page, pageSize=page_size, total=total
    )


@router.get("/value", response_model=OpportunitySearchResponse)
async def get_opportunities_by_value(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    current_user: User = Depends(get_current_user),
    service: OpportunityService = Depends(get_opportunity_service),
) -> OpportunitySearchResponse:
    """Busca oportunidades ordenadas por valor (maior para menor)."""
    opportunities, total = await service.get_by_value(page, page_size, current_user.id)

    items = [_opp_to_response(opp) for opp in opportunities]

    return OpportunitySearchResponse(
        items=items, page=page, pageSize=page_size, total=total
    )


@router.get("/term", response_model=OpportunitySearchResponse)
async def get_opportunities_by_deadline(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    current_user: User = Depends(get_current_user),
    service: OpportunityService = Depends(get_opportunity_service),
) -> OpportunitySearchResponse:
    """Busca oportunidades ordenadas por prazo (mais urgente primeiro)."""
    opportunities, total = await service.get_by_deadline(
        page, page_size, current_user.id
    )

    items = [_opp_to_response(opp) for opp in opportunities]

    return OpportunitySearchResponse(
        items=items, page=page, pageSize=page_size, total=total
    )


@router.get("", response_model=OpportunitySearchResponse)
async def search_opportunities(
    search: str | None = Query(None),
    state: str | None = Query(None),
    category_id: str | None = Query(None, alias="categoryId"),
    min_value: float | None = Query(None, alias="minValue"),
    max_value: float | None = Query(None, alias="maxValue"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    current_user: User = Depends(get_current_user),
    service: OpportunityService = Depends(get_opportunity_service),
) -> OpportunitySearchResponse:
    opportunities, total = await service.search(
        search=search,
        state=state,
        category_id=category_id,
        min_value=min_value,
        max_value=max_value,
        page=page,
        page_size=page_size,
        user_id=current_user.id,
    )

    items = [_opp_to_response(opp) for opp in opportunities]

    return OpportunitySearchResponse(
        items=items, page=page, pageSize=page_size, total=total
    )


@router.patch("/{opportunity_id}/favorite", response_model=FavoriteToggleResponse)
async def toggle_favorite(
    opportunity_id: str,
    current_user: User = Depends(get_current_user),
    service: OpportunityService = Depends(get_opportunity_service),
) -> FavoriteToggleResponse:
    opportunity = await service.get_by_id(opportunity_id, current_user.id)
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Oportunidade não encontrada",
        )

    is_favorite = await service.toggle_favorite(current_user.id, opportunity_id)

    return FavoriteToggleResponse(id=opportunity_id, isFavorite=is_favorite)


@router.get("/{opportunity_id}", response_model=OpportunityDetailResponse)
async def get_opportunity_detail(
    opportunity_id: str,
    current_user: User = Depends(get_current_user),
    service: OpportunityService = Depends(get_opportunity_service),
) -> OpportunityDetailResponse:
    opportunity = await service.get_by_id(opportunity_id, current_user.id)

    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Oportunidade não encontrada",
        )

    return _opp_to_detail_response(opportunity)


@router.get("/stats/monthly", response_model=MonthlyStatsResponse)
async def get_monthly_stats(
    month: str = Query(
        ...,
        pattern=r"^\d{4}-\d{2}$",
        description="Mês no formato YYYY-MM",
    ),
    service: OpportunityService = Depends(get_opportunity_service),
) -> MonthlyStatsResponse:
    """Retorna estatísticas mensais de oportunidades.

    Args:
        month: Mês no formato YYYY-MM (ex: 2026-06)

    Returns:
        Estatísticas com total de novos editais, top 5 categorias e timestamp
    """
    stats = await service.get_monthly_stats(month)

    # Converter para schema de resposta
    top_categories = [
        CategoryStatsResponse(
            id=cat["id"],  # type: ignore
            name=cat["name"],  # type: ignore
            slug=cat["slug"],  # type: ignore
            count=cat["count"],  # type: ignore
        )
        for cat in stats["top_categories"]  # type: ignore
    ]

    return MonthlyStatsResponse(
        month=month,
        totalNewOpportunities=stats["total_new_opportunities"],  # type: ignore
        topCategories=top_categories,
        generatedAt=stats["generated_at"],  # type: ignore
    )


def _opp_to_response(opp: Opportunity) -> OpportunityResponse:
    location = (
        f"{opp.location_city}/{opp.location_state}"
        if opp.location_city
        else opp.location_state
    )

    compatibility_label = (
        opp.compatibility.label if opp.compatibility else "Não avaliado"
    )

    return OpportunityResponse(
        id=opp.id,
        title=opp.title,
        company=opp.agency.name,
        location=location,
        description=opp.description or opp.title,
        estimatedValue=opp.estimated_value,
        daysRemaining=opp.days_remaining or 0,
        compatibilityLabel=compatibility_label,
        isFavorite=opp.is_favorite,
    )


def _opp_to_detail_response(opp: Opportunity) -> OpportunityDetailResponse:
    location = (
        f"{opp.location_city}/{opp.location_state}"
        if opp.location_city
        else opp.location_state
    )

    agency = OpportunityAgencyResponse(
        name=opp.agency.name,
        cnpj=opp.agency.cnpj,
        unit=opp.agency.unit,
    )

    categories = [
        OpportunityCategoryResponse(id=cat.id, name=cat.name, slug=cat.slug)
        for cat in opp.categories
    ]

    compatibility = OpportunityCompatibilityResponse(
        score=opp.compatibility.score if opp.compatibility else 50.0,
        label=opp.compatibility.label if opp.compatibility else "Não avaliado",
        reasons=opp.compatibility.reasons if opp.compatibility else [],
    )

    return OpportunityDetailResponse(
        id=opp.id,
        title=opp.title,
        company=opp.agency.name,
        location=location,
        description=opp.description or opp.title,
        estimatedValue=opp.estimated_value,
        daysRemaining=opp.days_remaining or 0,
        compatibilityLabel=compatibility.label,
        isFavorite=opp.is_favorite,
        pncpId=opp.pncp_id,
        pncpUrl=opp.pncp_url or "",
        agency=agency,
        modality=opp.modality,
        objectFull=opp.object_full or "",
        judgementCriterion=opp.judgement_criterion or "",
        openingDate=opp.opening_date.isoformat(),
        closingDate=opp.closing_date.isoformat(),
        proposalsOpeningDate=(
            opp.proposals_opening_date.isoformat()
            if opp.proposals_opening_date
            else None
        ),
        categories=categories,
        compatibility=compatibility,
        status=opp.status,
    )
