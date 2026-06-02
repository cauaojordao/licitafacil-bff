"""Testes unitários para TokenService."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from jose import JWTError, jwt

from src.core.config import settings
from src.services.token_service import TokenService


@pytest.fixture
def token_service() -> TokenService:
    """Cria instância de TokenService."""
    return TokenService()


def test_create_access_token(token_service: TokenService) -> None:
    """Testa criação de access token."""
    user_id = "user-123"
    
    token = token_service.create_access_token(user_id)
    
    assert isinstance(token, str)
    
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == user_id
    assert payload["type"] == "access"


def test_create_refresh_token(token_service: TokenService) -> None:
    """Testa criação de refresh token."""
    user_id = "user-123"
    
    token = token_service.create_refresh_token(user_id)
    
    assert isinstance(token, str)
    
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"


def test_validate_access_token_valid(token_service: TokenService) -> None:
    """Testa validação de access token válido."""
    user_id = "user-123"
    token = token_service.create_access_token(user_id)
    
    validated_user_id = token_service.validate_access_token(token)
    
    assert validated_user_id == user_id


def test_validate_access_token_expired(token_service: TokenService) -> None:
    """Testa validação de access token expirado."""
    user_id = "user-123"
    
    expired_payload = {
        "sub": user_id,
        "type": "access",
        "exp": datetime.utcnow() - timedelta(hours=1),
    }
    expired_token = jwt.encode(
        expired_payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    
    with pytest.raises(ValueError) as exc_info:
        token_service.validate_access_token(expired_token)
    
    assert "expirado" in str(exc_info.value).lower()


def test_validate_access_token_wrong_type(token_service: TokenService) -> None:
    """Testa validação de token com tipo errado."""
    user_id = "user-123"
    refresh_token = token_service.create_refresh_token(user_id)
    
    with pytest.raises(ValueError) as exc_info:
        token_service.validate_access_token(refresh_token)
    
    assert "tipo inválido" in str(exc_info.value).lower()


def test_validate_refresh_token_valid(token_service: TokenService) -> None:
    """Testa validação de refresh token válido."""
    user_id = "user-123"
    token = token_service.create_refresh_token(user_id)
    
    validated_user_id = token_service.validate_refresh_token(token)
    
    assert validated_user_id == user_id


def test_validate_refresh_token_invalid(token_service: TokenService) -> None:
    """Testa validação de refresh token inválido."""
    invalid_token = "invalid.token.here"
    
    with pytest.raises(JWTError):
        token_service.validate_refresh_token(invalid_token)


def test_validate_access_token_missing_subject(token_service: TokenService) -> None:
    """Testa validação de token sem subject."""
    payload = {
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=15),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    with pytest.raises(ValueError) as exc_info:
        token_service.validate_access_token(token)
    
    assert "subject" in str(exc_info.value).lower() or "usuário" in str(exc_info.value).lower()
