"""Schemas de autenticação e autorização."""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Schema para requisição de login."""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Schema para requisição de renovação de token."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Schema de resposta com tokens de autenticação."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """Schema de resposta genérica com mensagem."""

    message: str
