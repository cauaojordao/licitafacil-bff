"""Rotas de autenticação e autorização."""

from fastapi import APIRouter, Depends, status

from src.core.dependencies import get_auth_service, get_current_user
from src.domain.entities.user import User
from src.domain.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    TokenResponse,
)
from src.domain.schemas.password_reset import (
    ForgotPasswordRequest,
    ResendCodeRequest,
    ResetPasswordRequest,
    VerifyResetCodeRequest,
    VerifyResetCodeResponse,
)
from src.integrations.email import send_reset_code_email
from src.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Fazer login",
    description="Autentica um usuário e retorna tokens de acesso.",
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
    description="Gera novos tokens a partir de um refresh token válido.",
)
async def refresh(
    body: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return auth_service.refresh_tokens(body.refresh_token)


@router.post(
    "/password-reset/request",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Solicitar código de reset",
    description="Envia código de 4 dígitos por e-mail para reset de senha.",
)
async def request_password_reset(
    body: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Sempre retorna mesma mensagem para evitar enumeração de usuários."""
    response, code = auth_service.request_password_reset(body.email)

    if code:
        await send_reset_code_email(body.email, code)

    return response


@router.post(
    "/password-reset/verify",
    response_model=VerifyResetCodeResponse,
    summary="Verificar código de reset",
    description="Valida o código de 4 dígitos e retorna token de uso único.",
)
async def verify_reset_code(
    body: VerifyResetCodeRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> VerifyResetCodeResponse:
    result = auth_service.verify_reset_code(body.email, body.code)
    return VerifyResetCodeResponse(**result)


@router.post(
    "/password-reset/resend",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Reenviar código de reset",
    description="Reenvia código de 4 dígitos por e-mail.",
)
async def resend_reset_code(
    body: ResendCodeRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Sempre retorna mesma mensagem para evitar enumeração de usuários."""
    response, code = auth_service.resend_reset_code(body.email)

    if code:
        await send_reset_code_email(body.email, code)

    return response


@router.post(
    "/password-reset/complete",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Concluir reset de senha",
    description="Redefine a senha usando token de uso único.",
)
async def complete_password_reset(
    body: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    return auth_service.reset_password(body.reset_token, body.new_password)


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Fazer logout",
    description="Invalida a sessão atual do usuário.",
)
async def logout(
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    return MessageResponse(message="Logout realizado com sucesso")
