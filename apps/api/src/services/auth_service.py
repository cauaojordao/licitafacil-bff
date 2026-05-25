"""Service principal para autenticação e autorização."""

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status

from src.core.config import settings
from src.domain.schemas.auth import MessageResponse, TokenResponse
from src.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from src.services.token_service import TokenService
from src.services.user_service import UserService


class AuthService:
    """
    Service para operações de autenticação e gerenciamento de senha.

    Coordena operações entre UserService, TokenService e repositórios.
    """

    def __init__(
        self,
        user_service: UserService,
        token_service: TokenService,
        password_reset_repository: PasswordResetTokenRepository,
    ):
        """
        Inicializa o service com suas dependências.

        Args:
            user_service: Service de usuários
            token_service: Service de tokens
            password_reset_repository: Repository de tokens de reset
        """
        self.user_service = user_service
        self.token_service = token_service
        self.password_reset_repository = password_reset_repository

    def register(self, name: str, email: str, password: str) -> TokenResponse:
        """
        Registra um novo usuário e retorna tokens de acesso.

        Args:
            name: Nome do usuário
            email: E-mail do usuário
            password: Senha em texto plano

        Returns:
            Tokens de acesso e renovação
        """
        user = self.user_service.register_user(name, email, password)
        user_id = user["id"]

        return TokenResponse(
            access_token=self.token_service.create_access_token(user_id),
            refresh_token=self.token_service.create_refresh_token(user_id),
        )

    def login(self, email: str, password: str) -> TokenResponse:
        """
        Autentica um usuário e retorna tokens de acesso.

        Args:
            email: E-mail do usuário
            password: Senha em texto plano

        Returns:
            Tokens de acesso e renovação
        """
        user = self.user_service.authenticate_user(email, password)
        user_id = user["id"]

        return TokenResponse(
            access_token=self.token_service.create_access_token(user_id),
            refresh_token=self.token_service.create_refresh_token(user_id),
        )

    def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """
        Gera novos tokens a partir de um refresh token válido.

        Args:
            refresh_token: Token de renovação

        Returns:
            Novos tokens de acesso e renovação

        Raises:
            HTTPException: Se o refresh token for inválido
        """
        try:
            user_id = self.token_service.validate_refresh_token(refresh_token)
        except (ValueError, Exception):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido ou expirado",
            ) from None

        return TokenResponse(
            access_token=self.token_service.create_access_token(user_id),
            refresh_token=self.token_service.create_refresh_token(user_id),
        )

    def request_password_reset(self, email: str) -> MessageResponse:
        """
        Inicia o processo de reset de senha gerando um token.

        Args:
            email: E-mail do usuário

        Returns:
            Mensagem genérica (sempre a mesma para evitar enumeração)

        Note:
            Retorna sempre a mesma mensagem independente do e-mail existir
            para evitar enumeração de usuários.
        """
        generic_response = MessageResponse(
            message=(
                "Se este e-mail estiver cadastrado, "
                "você receberá as instruções em breve."
            )
        )

        user = self.user_service.user_repository.find_by_email(email)
        if not user:
            return generic_response

        user_id = user["id"]
        reset_token = secrets.token_urlsafe(32)
        expires_at = (
            datetime.now(UTC)
            + timedelta(hours=settings.RESET_TOKEN_EXPIRE_HOURS)
        ).isoformat()

        self.password_reset_repository.upsert(user_id, reset_token, expires_at)

        return generic_response

    def reset_password(self, token: str, new_password: str) -> MessageResponse:
        """
        Redefine a senha usando um token válido.

        Args:
            token: Token de reset recebido por e-mail
            new_password: Nova senha em texto plano

        Returns:
            Mensagem de sucesso

        Raises:
            HTTPException: Se o token for inválido ou expirado
        """
        token_data = self.password_reset_repository.find_by_token(token)

        if not token_data or not self.password_reset_repository.is_token_valid(
            token_data
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido ou expirado",
            )

        user_id = token_data["user_id"]
        self.user_service.update_user_password(user_id, new_password)

        # Token de reset é de uso único
        self.password_reset_repository.delete_by_token(token)

        return MessageResponse(message="Senha atualizada com sucesso.")
