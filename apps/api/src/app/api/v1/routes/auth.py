import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from supabase import Client

from src.app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from src.app.services.email import send_reset_email
from src.core.config import settings
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from src.db.supabase import get_supabase

router = APIRouter()

RESET_TOKEN_EXPIRE_HOURS = settings.RESET_TOKEN_EXPIRE_HOURS


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest, db: Client = Depends(get_supabase)
) -> TokenResponse:
    """Cria uma nova conta e retorna tokens de acesso."""
    existing = (
        db.table("users")
        .select("id")
        .eq("email", body.email)
        .maybe_single()
        .execute()
    )
    if existing and existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado",
        )

    result = (
        db.table("users")
        .insert({
            "name": body.name,
            "email": body.email,
            "password_hash": hash_password(body.password),
        })
        .execute()
    )
    user_id: str = result.data[0]["id"]

    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest, db: Client = Depends(get_supabase)
) -> TokenResponse:
    """Autentica o usuário e retorna tokens de acesso."""
    result = (
        db.table("users")
        .select("id, password_hash")
        .eq("email", body.email)
        .maybe_single()
        .execute()
    )

    # Mensagem genérica para não revelar se o e-mail existe ou não
    if not result.data or not verify_password(
        body.password, result.data["password_hash"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos",
        )

    user_id: str = result.data["id"]
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest) -> TokenResponse:
    """Gera um novo par de tokens a partir de um refresh token válido."""
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Not a refresh token")
        user_id: str = payload["sub"]
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado",
        ) from None

    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    body: ForgotPasswordRequest, db: Client = Depends(get_supabase)
) -> MessageResponse:
    """Envia e-mail com link de redefinição de senha."""
    result = (
        db.table("users")
        .select("id")
        .eq("email", body.email)
        .maybe_single()
        .execute()
    )

    # Resposta sempre igual para evitar enumeração de e-mails
    generic_response = MessageResponse(
        message=(
            "Se este e-mail estiver cadastrado, "
            "você receberá as instruções em breve."
        )
    )

    if not result.data:
        return generic_response

    user_id: str = result.data["id"]
    reset_token = secrets.token_urlsafe(32)
    expires_at = (
        datetime.now(UTC)
        + timedelta(hours=RESET_TOKEN_EXPIRE_HOURS)
    ).isoformat()

    db.table("password_reset_tokens").upsert(
        {"user_id": user_id, "token": reset_token, "expires_at": expires_at}
    ).execute()

    await send_reset_email(body.email, reset_token)
    return generic_response


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    body: ResetPasswordRequest, db: Client = Depends(get_supabase)
) -> MessageResponse:
    """Redefine a senha usando o token recebido por e-mail."""
    result = (
        db.table("password_reset_tokens")
        .select("user_id, expires_at")
        .eq("token", body.token)
        .maybe_single()
        .execute()
    )

    invalid_error = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Token inválido ou expirado",
    )

    if not result.data:
        raise invalid_error

    expires_at = datetime.fromisoformat(result.data["expires_at"])
    if datetime.now(UTC) > expires_at:
        raise invalid_error

    user_id: str = result.data["user_id"]

    db.table("users").update(
        {"password_hash": hash_password(body.new_password)}
    ).eq("id", user_id).execute()

    # Token de reset é de uso único — remover após uso
    db.table("password_reset_tokens").delete().eq("token", body.token).execute()

    return MessageResponse(message="Senha atualizada com sucesso.")
