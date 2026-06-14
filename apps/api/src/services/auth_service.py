"""Service principal para autenticação e autorização."""

from datetime import datetime, timedelta, timezone

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
        """
        Solicita reset de senha e gera código de 4 dígitos.

        Args:
            email: Email do usuário

        Returns:
            Tuple com mensagem genérica e código (ou None se email não existe)
        """
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
        code = self.password_reset_repository.generate_code()
        expires_at = (
            datetime.now(timezone.utc) + timedelta(minutes=settings.RESET_CODE_EXPIRE_MINUTES)
        ).isoformat()

        self.password_reset_repository.upsert_code(user_id, code, expires_at)

        logger.info(
            "Código de reset de senha gerado",
            extra_fields={"user_id": user_id},
        )

        return (generic_response, code)

    def verify_reset_code(self, email: str, code: str) -> dict[str, str | int]:
        """
        Valida código de reset e retorna token de uso único.

        Args:
            email: Email do usuário
            code: Código de 4 dígitos

        Returns:
            Dict com reset_token e expires_in

        Raises:
            HTTPException: Se código inválido ou expirado
        """
        code_data = self.password_reset_repository.find_by_code_and_email(code, email)

        if not code_data or not self.password_reset_repository.is_code_valid(code_data):
            # Não loga dados sensíveis (código/email) para evitar exposição
            logger.warning("Tentativa de verificação com código inválido")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código inválido ou expirado",
            )

        user_id = code_data["user_id"]

        try:
            reset_token = self.password_reset_repository.mark_as_verified(code, user_id)
        except RuntimeError:
            logger.warning(
                "Código já foi verificado",
                extra_fields={"user_id": user_id},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código inválido ou expirado",
            ) from None

        logger.info(
            "Código verificado com sucesso",
            extra_fields={"user_id": user_id},
        )

        expires_at = datetime.fromisoformat(code_data["expires_at"])
        expires_in = int((expires_at - datetime.now(timezone.utc)).total_seconds())

        return {
            "reset_token": reset_token,
            "expires_in": max(expires_in, 0),
        }

    def resend_reset_code(self, email: str) -> tuple[MessageResponse, str | None]:
        """Reenvia código de reset de senha (mesmo fluxo de solicitação inicial)."""
        return self.request_password_reset(email)

    def reset_password(self, token: str, new_password: str) -> MessageResponse:
        """
        Redefine senha usando token de uso único.

        Args:
            token: Token retornado após verificação do código
            new_password: Nova senha

        Returns:
            Mensagem de sucesso

        Raises:
            HTTPException: Se token inválido ou expirado
        """
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
