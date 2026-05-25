"""Schemas de autenticação e autorização."""

from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    """Schema para requisição de registro de novo usuário."""

    name: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("A senha deve ter pelo menos 8 caracteres")
        return v


class LoginRequest(BaseModel):
    """Schema para requisição de login."""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Schema para requisição de renovação de token."""

    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """Schema para requisição de esqueci minha senha."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema para requisição de reset de senha."""

    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("A senha deve ter pelo menos 8 caracteres")
        return v


class TokenResponse(BaseModel):
    """Schema de resposta com tokens de autenticação."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """Schema de resposta genérica com mensagem."""

    message: str
