"""Entidade de usuário."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class User(BaseModel):
    """Entidade representando um usuário no sistema."""

    model_config = ConfigDict()

    id: str
    name: str
    email: EmailStr
    password_hash: str = Field(exclude=True)
    cnpj: str | None = None
    company_name: str | None = None
    anonymized_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
