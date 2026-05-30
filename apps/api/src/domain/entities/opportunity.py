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

    score: float  # 0-100
    label: str  # "Altamente Compatível", "Compatível", etc
    reasons: list[str]  # ["Atende ao CNAE principal", "Localização compatível"]


class Opportunity(BaseModel):
    """Entidade representando uma oportunidade/edital."""

    id: str
    pncp_id: str
    pncp_url: str | None = None

    # Informações básicas
    title: str
    description: str | None = None
    object_full: str | None = None

    # Modalidade
    modality: str
    judgement_criterion: str | None = None

    # Valores
    estimated_value: Decimal

    # Datas
    opening_date: datetime
    closing_date: datetime
    proposals_opening_date: datetime | None = None

    # Status
    status: str  # 'aberto', 'encerrado', 'suspenso', 'cancelado'

    # Órgão
    agency: OpportunityAgency

    # Localização
    location_city: str | None = None
    location_state: str

    # Metadados
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # Relacionamentos (podem ser carregados opcionalmente)
    categories: list[OpportunityCategory] = Field(default_factory=list)
    is_favorite: bool = False

    # Compatibilidade (calculada dinamicamente)
    compatibility: OpportunityCompatibility | None = None
    days_remaining: int | None = None  # Calculado a partir de closing_date
