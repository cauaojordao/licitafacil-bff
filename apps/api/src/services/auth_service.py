"""Service principal para autenticação e autorização."""

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from jose import JWTError

from src.core.config import settings
from src.core.logging import get_logger
from src.domain.schemas.auth import MessageResponse, TokenResponse
from src.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from src.services.token_service import TokenService
from src.services.user_service import UserService

logger = get_logger(__name__)


class AuthService:
    """Service para operações de autenticação e gerenciamento de senha."""

    def __init__(
        self,
        user_service: UserService,
        token_service: TokenService,
        password_reset_repository: PasswordResetTokenRepository,
    ):
        self.user_service = user_service
        self.token_service = token_service
        self.password_reset_repository = password_reset_repository

    def register(self, name: str, email: str, password: str) -> TokenResponse:
        user = self.user_service.register_user(name, email, password)
        user_id = user["id"]

        logger.info(
            "Usuário registrado com sucesso",
            extra_fields={"user_id": user_id},
        )

        return TokenResponse(
            access_token=self.token_service.create_access_token(user_id),
            refresh_token=self.token_service.create_refresh_token(user_id),
        )

    def login(self, email: str, password: str) -> TokenResponse:
        user = self.user_service.authenticate_user(email, password)
        user_id = user["id"]

        logger.info(
            "Login realizado com sucesso",
            extra_fields={"user_id": user_id},
        )

        return TokenResponse(
            access_token=self.token_service.create_access_token(user_id),
            refresh_token=self.token_service.create_refresh_token(user_id),
        )

    def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        try:
            user_id = self.token_service.validate_refresh_token(refresh_token)
        except (ValueError, JWTError) as e:
            logger.warning(
                "Tentativa de refresh com token inválido",
                extra_fields={"error": str(e)},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido ou expirado",
            ) from None

        logger.info("Tokens renovados com sucesso", extra_fields={"user_id": user_id})

        return TokenResponse(
            access_token=self.token_service.create_access_token(user_id),
            refresh_token=self.token_service.create_refresh_token(user_id),
        )

    def request_password_reset(self, email: str) -> tuple[MessageResponse, str | None]:
        """Sempre retorna mesma mensagem para evitar enumeração de usuários."""
        generic_response = MessageResponse(
            message=(
                "Se este e-mail estiver cadastrado, "
                "você receberá as instruções em breve."
            )
        )

        user = self.user_service.user_repository.find_by_email(email)
        if not user:
            logger.info("Solicitação de reset para email não cadastrado")
            return (generic_response, None)

        user_id = user["id"]
        reset_token = secrets.token_urlsafe(32)
        expires_at = (
            datetime.now(UTC) + timedelta(hours=settings.RESET_TOKEN_EXPIRE_HOURS)
        ).isoformat()

        self.password_reset_repository.upsert(user_id, reset_token, expires_at)

        logger.info(
            "Token de reset de senha gerado",
            extra_fields={"user_id": user_id},
        )

        return (generic_response, reset_token)

    def reset_password(self, token: str, new_password: str) -> MessageResponse:
        token_data = self.password_reset_repository.find_by_token(token)

        if not token_data or not self.password_reset_repository.is_token_valid(
            token_data
        ):
            logger.warning(
                "Tentativa de reset com token inválido",
                extra_fields={"token_prefix": token[:8]},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido ou expirado",
            )

        user_id = token_data["user_id"]
        self.user_service.update_user_password(user_id, new_password)
        self.password_reset_repository.delete_by_token(token)

        logger.info("Senha redefinida com sucesso", extra_fields={"user_id": user_id})

        return MessageResponse(message="Senha atualizada com sucesso.")
