"""Rotas de autenticação e autorização."""

from fastapi import APIRouter, Depends, status

from src.core.dependencies import get_auth_service
from src.domain.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from src.integrations.email import send_reset_email
from src.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novo usuário",
)
async def register(
    body: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return auth_service.register(body.name, body.email, body.password)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Fazer login",
)
async def login(
    body: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return auth_service.login(body.email, body.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar tokens",
)
async def refresh(
    body: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return auth_service.refresh_tokens(body.refresh_token)


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Solicitar reset de senha",
)
async def forgot_password(
    body: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Retorna sempre a mesma mensagem para evitar enumeração de usuários."""
    response, reset_token = auth_service.request_password_reset(body.email)

    if reset_token:
        await send_reset_email(body.email, reset_token)

    return response


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Redefinir senha",
)
async def reset_password(
    body: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    return auth_service.reset_password(body.token, body.new_password)
