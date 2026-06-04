"""Schemas para APIs de oportunidades/editais."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

# --- Response Schemas ---


class OpportunityCompatibilityResponse(BaseModel):
    """Schema de compatibilidade para resposta."""

    score: float = Field(..., ge=0, le=100)
    label: str
    reasons: list[str]


class OpportunityCategoryResponse(BaseModel):
    """Schema de categoria para resposta."""

    id: str
    name: str
    slug: str


class OpportunityResponse(BaseModel):
    """Schema resumido para lista de oportunidades."""

    id: str
    title: str
    company: str  # nome do órgão (agency_name)
    location: str  # "Cidade/UF"
    description: str  # resumo curto
    estimated_value: Decimal = Field(..., alias="estimatedValue")
    days_remaining: int = Field(..., alias="daysRemaining")
    compatibility_label: str = Field(..., alias="compatibilityLabel")
    is_favorite: bool = Field(..., alias="isFavorite")

    model_config = ConfigDict(populate_by_name=True)


class OpportunityAgencyResponse(BaseModel):
    """Schema de órgão para resposta."""

    name: str
    cnpj: str
    unit: str | None = None


class OpportunityDetailResponse(OpportunityResponse):
    """Schema completo para detalhe de oportunidade."""

    # Campos adicionais do detalhe
    pncp_id: str = Field(..., alias="pncpId")
    pncp_url: str = Field(..., alias="pncpUrl")

    agency: OpportunityAgencyResponse

    modality: str
    object_full: str = Field(..., alias="objectFull")
    judgement_criterion: str = Field(..., alias="judgementCriterion")

    opening_date: str = Field(..., alias="openingDate")  # ISO 8601
    closing_date: str = Field(..., alias="closingDate")
    proposals_opening_date: str | None = Field(None, alias="proposalsOpeningDate")

    categories: list[OpportunityCategoryResponse]

    compatibility: OpportunityCompatibilityResponse

    status: str

    model_config = ConfigDict(populate_by_name=True)


class OpportunitySearchResponse(BaseModel):
    """Schema para resposta paginada de busca."""

    items: list[OpportunityResponse]
    page: int
    page_size: int = Field(..., alias="pageSize")
    total: int

    model_config = ConfigDict(populate_by_name=True)


class FavoriteToggleResponse(BaseModel):
    """Schema para resposta de toggle de favorito."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    is_favorite: bool = Field(..., alias="isFavorite")


# --- Request Schemas (Query Parameters) ---


class OpportunitySearchParams(BaseModel):
    """Parâmetros de busca/filtros para oportunidades."""

    search: str | None = None  # texto livre
    state: str | None = None  # UF
    city: str | None = None
    modality: str | None = None
    min_value: Decimal | None = Field(None, alias="minValue")
    max_value: Decimal | None = Field(None, alias="maxValue")
    compatibility: int | None = Field(None, ge=0, le=100)  # score mínimo
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100, alias="pageSize")

    model_config = ConfigDict(populate_by_name=True)


class CategoryStatsResponse(BaseModel):
    """Schema para estatísticas de uma categoria."""

    id: str
    name: str
    slug: str
    count: int


class MonthlyStatsResponse(BaseModel):
    """Schema para estatísticas mensais de oportunidades."""

    month: str
    total_new_opportunities: int = Field(..., alias="totalNewOpportunities")
    top_categories: list[CategoryStatsResponse] = Field(..., alias="topCategories")
    generated_at: str = Field(..., alias="generatedAt")

    model_config = ConfigDict(populate_by_name=True)
