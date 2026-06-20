"""Schemas para recuperação de senha com código de 4 dígitos."""

from pydantic import BaseModel, EmailStr, field_validator

from src.utils.password_validator import validate_password_strength


class ForgotPasswordRequest(BaseModel):
    """Schema para requisição de esqueci minha senha."""

    email: EmailStr


class VerifyResetCodeRequest(BaseModel):
    """Schema para validação do código de reset."""

    email: EmailStr
    code: str

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 4:
            raise ValueError("O código deve conter exatamente 4 dígitos")
        return v


class VerifyResetCodeResponse(BaseModel):
    """Schema de resposta da validação do código."""

    reset_token: str
    expires_in: int  # segundos


class ResetPasswordRequest(BaseModel):
    """Schema para reset de senha com token."""

    reset_token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        validate_password_strength(v)
        return v


class ResendCodeRequest(BaseModel):
    """Schema para reenvio de código."""

    email: EmailStr
