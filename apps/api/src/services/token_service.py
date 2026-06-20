"""Service para gerenciamento de tokens JWT."""

from datetime import datetime, timedelta, timezone
from typing import Any, cast

from jose import jwt

from src.core.config import settings
from src.domain.enums import TokenType


class TokenService:
    """Service para criação e validação de tokens JWT."""

    def __init__(self) -> None:
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

    def _create_token(self, data: dict, expires_delta: timedelta) -> str:
        payload = data.copy()
        payload["exp"] = datetime.now(timezone.utc) + expires_delta
        return cast(
            str,
            jwt.encode(payload, self.secret_key, algorithm=self.algorithm),
        )

    def create_access_token(self, user_id: str) -> str:
        return self._create_token(
            {"sub": user_id, "type": TokenType.ACCESS.value},
            timedelta(minutes=self.access_token_expire_minutes),
        )

    def create_refresh_token(self, user_id: str) -> str:
        return self._create_token(
            {"sub": user_id, "type": TokenType.REFRESH.value},
            timedelta(days=self.refresh_token_expire_days),
        )

    def decode_token(self, token: str) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            jwt.decode(token, self.secret_key, algorithms=[self.algorithm]),
        )

    def validate_access_token(self, token: str) -> str:
        payload = self.decode_token(token)
        if payload.get("type") != TokenType.ACCESS.value:
            raise ValueError("Token não é um access token")
        return cast(str, payload["sub"])

    def validate_refresh_token(self, token: str) -> str:
        payload = self.decode_token(token)
        if payload.get("type") != TokenType.REFRESH.value:
            raise ValueError("Token não é um refresh token")
        return cast(str, payload["sub"])
