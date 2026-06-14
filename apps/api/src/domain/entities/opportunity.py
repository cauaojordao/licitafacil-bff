"""Entidade de Oportunidade (Edital)."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OpportunityCategory(BaseModel):
    """Categoria de um edital."""

    id: str
    name: str
    slug: str


class OpportunityAgency(BaseModel):
    """Dados do órgão responsável pelo edital."""

    name: str
    cnpj: str
    unit: str | None = None


class OpportunityCompatibility(BaseModel):
    """Score e razões de compatibilidade com o perfil do usuário."""

    score: float
    label: str
    reasons: list[str]


class Opportunity(BaseModel):
    """Entidade representando uma oportunidade/edital."""

    id: str
    pncp_id: str
    pncp_url: str | None = None


    title: str
    description: str | None = None
    object_full: str | None = None


    modality: str
    judgement_criterion: str | None = None


    estimated_value: Decimal


    opening_date: datetime
    closing_date: datetime
    proposals_opening_date: datetime | None = None


    status: str


    agency: OpportunityAgency


    location_city: str | None = None
    location_state: str


    created_at: datetime | None = None
    updated_at: datetime | None = None


    categories: list[OpportunityCategory] = Field(default_factory=list)
    is_favorite: bool = False


    compatibility: OpportunityCompatibility | None = None
    days_remaining: int | None = None
    is_expired: bool | None = None
