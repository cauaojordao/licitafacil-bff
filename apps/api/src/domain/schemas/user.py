"""Schemas para CNAE e consultas de CNPJ."""

from pydantic import BaseModel, Field, field_validator

from src.utils.cnpj import clean_cnpj as _clean_cnpj


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
    interested_state_siglas: list[str]
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
        return _clean_cnpj(v)

    @field_validator("cnae_ids")
    @classmethod
    def validate_cnaes(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("Selecione pelo menos um CNAE")
        return v


class CheckEmailResponse(BaseModel):
    """Schema de resposta para verificação de email."""

    available: bool


class CNAEDetailResponse(BaseModel):
    """Schema de resposta com detalhes de CNAE."""

    id: str
    description: str


class InterestedStateResponse(BaseModel):
    """Schema de resposta com estado de interesse do usuário."""

    sigla: str


class UserProfileResponse(BaseModel):
    """Schema de resposta com perfil completo do usuário."""

    name: str
    company_name: str | None = None
    cnpj: str | None = None
    email: str
    primary_cnae: CNAEDetailResponse | None = None
    secondary_cnaes: list[CNAEDetailResponse] = Field(default_factory=list)
    interested_states: list[InterestedStateResponse] = Field(default_factory=list)


class UpdateUserCNPJRequest(BaseModel):
    """Schema para requisição de atualização de CNPJ."""

    cnpj: str

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v: str) -> str:
        return _clean_cnpj(v)


class UpdateUserProfileRequest(BaseModel):
    """Schema para requisição de atualização de perfil do usuário."""

    name: str | None = None
    interested_state_siglas: list[str] | None = None
    cnae_ids: list[str] | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Nome não pode ser vazio")
        return v

    @field_validator("cnae_ids")
    @classmethod
    def validate_cnaes(cls, v: list[str] | None) -> list[str] | None:
        if v is not None and len(v) == 0:
            raise ValueError("Selecione pelo menos um CNAE")
        return v


class RefreshCNAEsRequest(BaseModel):
    """Schema para requisição de refresh de CNAEs via Receita Federal."""

    pass


class AnonymizeUserResponse(BaseModel):
    """Schema de resposta para anonimização de usuário."""

    message: str
    anonymized_at: str

