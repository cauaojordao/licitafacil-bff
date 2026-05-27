"""Entidade de usuário."""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    """Entidade representando um usuário no sistema."""

    id: str
    name: str
    email: EmailStr
    password_hash: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
