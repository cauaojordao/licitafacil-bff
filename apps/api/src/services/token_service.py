"""Service para gerenciamento de tokens JWT."""

from datetime import UTC, datetime, timedelta

from jose import jwt

from src.core.config import settings
from src.domain.enums import TokenType


class TokenService:
    """Service para criação e validação de tokens JWT."""

    def __init__(self) -> None:
        """Inicializa o service com as configurações."""
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

    def _create_token(self, data: dict, expires_delta: timedelta) -> str:
        """
        Cria um token JWT com prazo de expiração.

        Args:
            data: Dados a serem incluídos no token
            expires_delta: Tempo até a expiração

        Returns:
            Token JWT codificado
        """
        payload = data.copy()
        payload["exp"] = datetime.now(UTC) + expires_delta
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_access_token(self, user_id: str) -> str:
        """
        Cria um token de acesso para um usuário.

        Args:
            user_id: ID do usuário

        Returns:
            Token de acesso JWT
        """
        return self._create_token(
            {"sub": user_id, "type": TokenType.ACCESS.value},
            timedelta(minutes=self.access_token_expire_minutes),
        )

    def create_refresh_token(self, user_id: str) -> str:
        """
        Cria um token de renovação para um usuário.

        Args:
            user_id: ID do usuário

        Returns:
            Token de renovação JWT
        """
        return self._create_token(
            {"sub": user_id, "type": TokenType.REFRESH.value},
            timedelta(days=self.refresh_token_expire_days),
        )

    def decode_token(self, token: str) -> dict:
        """
        Decodifica e valida um JWT.

        Args:
            token: Token JWT a ser decodificado

        Returns:
            Payload do token decodificado

        Raises:
            JWTError: Se o token for inválido ou expirado
        """
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

    def validate_access_token(self, token: str) -> str:
        """
        Valida um token de acesso e retorna o user_id.

        Args:
            token: Token de acesso a ser validado

        Returns:
            ID do usuário

        Raises:
            ValueError: Se o token não for um access token válido
            JWTError: Se o token for inválido ou expirado
        """
        payload = self.decode_token(token)
        if payload.get("type") != TokenType.ACCESS.value:
            raise ValueError("Token não é um access token")
        return payload["sub"]

    def validate_refresh_token(self, token: str) -> str:
        """
        Valida um token de renovação e retorna o user_id.

        Args:
            token: Token de renovação a ser validado

        Returns:
            ID do usuário

        Raises:
            ValueError: Se o token não for um refresh token válido
            JWTError: Se o token for inválido ou expirado
        """
        payload = self.decode_token(token)
        if payload.get("type") != TokenType.REFRESH.value:
            raise ValueError("Token não é um refresh token")
        return payload["sub"]
