"""Schemas para CNAE e consultas de CNPJ."""

from pydantic import BaseModel, field_validator


class CNAEResponse(BaseModel):
    """Schema de resposta com dados de um CNAE."""

    id: str
    title: str


class CNPJCNAEsResponse(BaseModel):
    """Schema de resposta com CNAEs de um CNPJ."""

    cnpj: str
    razao_social: str | None = None
    primary_cnae: CNAEResponse | None = None
    secondary_cnaes: list[CNAEResponse] = []


class StateResponse(BaseModel):
    """Schema de resposta com dados de um estado."""

    id: str
    sigla: str
    nome: str


class RegisterUserRequest(BaseModel):
    """Schema para requisição de registro completo de MEI."""

    name: str
    email: str
    password: str
    cnpj: str
    interested_state_ids: list[str]
    cnae_ids: list[str]

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("A senha deve ter pelo menos 8 caracteres")
        return v

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v: str) -> str:
        # Remove formatação (pontos, barras, hífens)
        cnpj = v.replace(".", "").replace("/", "").replace("-", "").strip().upper()
        if len(cnpj) != 14:
            raise ValueError("CNPJ deve conter exatamente 14 caracteres")
        return cnpj

    @field_validator("interested_state_ids")
    @classmethod
    def validate_states(cls, v: list[str]) -> list[str]:
        if not v or len(v) == 0:
            raise ValueError("Selecione pelo menos um estado de interesse")
        return v

    @field_validator("cnae_ids")
    @classmethod
    def validate_cnaes(cls, v: list[str]) -> list[str]:
        if not v or len(v) == 0:
            raise ValueError("Selecione pelo menos um CNAE")
        return v


class CheckEmailResponse(BaseModel):
    """Schema de resposta para verificação de email."""

    available: bool
