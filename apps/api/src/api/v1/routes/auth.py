"""Rotas de autenticação e autorização."""

from fastapi import APIRouter, Depends, status
from supabase import Client

from src.core.dependencies import (
    get_auth_service,
)
from src.db.session import get_supabase
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
    description="Cria uma nova conta de usuário e retorna tokens de autenticação.",
)
async def register(
    body: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Registra um novo usuário no sistema.

    Args:
        body: Dados do novo usuário (nome, email, senha)
        auth_service: Service de autenticação (injetado)

    Returns:
        Tokens de acesso e renovação

    Raises:
        HTTPException 409: Se o e-mail já estiver cadastrado
    """
    return auth_service.register(body.name, body.email, body.password)


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
    """
    Autentica um usuário no sistema.

    Args:
        body: Credenciais de login (email, senha)
        auth_service: Service de autenticação (injetado)

    Returns:
        Tokens de acesso e renovação

    Raises:
        HTTPException 401: Se as credenciais forem inválidas
    """
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
    """
    Renova os tokens de autenticação.

    Args:
        body: Refresh token atual
        auth_service: Service de autenticação (injetado)

    Returns:
        Novos tokens de acesso e renovação

    Raises:
        HTTPException 401: Se o refresh token for inválido ou expirado
    """
    return auth_service.refresh_tokens(body.refresh_token)


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Solicitar reset de senha",
    description="Envia e-mail com link para redefinição de senha.",
)
async def forgot_password(
    body: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """
    Inicia processo de recuperação de senha.

    Args:
        body: E-mail do usuário
        auth_service: Service de autenticação (injetado)

    Returns:
        Mensagem genérica (sempre igual para evitar enumeração)

    Note:
        Sempre retorna a mesma mensagem, independente do e-mail existir,
        para evitar enumeração de usuários cadastrados.
    """
    response = auth_service.request_password_reset(body.email)

    user_service = auth_service.user_service
    user = user_service.user_repository.find_by_email(body.email)

    if user:
        db: Client = get_supabase()
        token_data = (
            db.table("password_reset_tokens")
            .select("token")
            .eq("user_id", user["id"])
            .order("created_at", desc=True)
            .limit(1)
            .maybe_single()
            .execute()
        )

        if token_data and token_data.data:
            await send_reset_email(body.email, token_data.data["token"])

    return response


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Redefinir senha",
    description="Redefine a senha usando o token recebido por e-mail.",
)
async def reset_password(
    body: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """
    Redefine a senha do usuário.

    Args:
        body: Token de reset e nova senha
        auth_service: Service de autenticação (injetado)

    Returns:
        Mensagem de sucesso

    Raises:
        HTTPException 400: Se o token for inválido ou expirado
    """
    return auth_service.reset_password(body.token, body.new_password)
