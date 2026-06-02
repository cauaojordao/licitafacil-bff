"""Testes unitários para AuthService."""

from datetime import datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from jose import JWTError

from src.domain.schemas.auth import MessageResponse, TokenResponse
from src.services.auth_service import AuthService


@pytest.fixture
def mock_user_service() -> MagicMock:
    """Mock do UserService."""
    mock = MagicMock()
    mock.user_repository = MagicMock()
    return mock


@pytest.fixture
def mock_token_service() -> MagicMock:
    """Mock do TokenService."""
    return MagicMock()


@pytest.fixture
def auth_service(
    mock_user_service: MagicMock,
    mock_token_service: MagicMock,
    mock_password_reset_repository: MagicMock,
) -> AuthService:
    """Cria instância de AuthService com mocks."""
    return AuthService(
        user_service=mock_user_service,
        token_service=mock_token_service,
        password_reset_repository=mock_password_reset_repository,
    )


def test_login_success(
    auth_service: AuthService,
    mock_user_service: MagicMock,
    mock_token_service: MagicMock,
    mock_user_data: dict[str, Any],
) -> None:
    """Testa login com credenciais válidas."""
    mock_user_service.authenticate_user.return_value = mock_user_data
    mock_token_service.create_access_token.return_value = "access_token"
    mock_token_service.create_refresh_token.return_value = "refresh_token"
    
    result = auth_service.login("joao@example.com", "senha123")
    
    assert isinstance(result, TokenResponse)
    assert result.access_token == "access_token"
    assert result.refresh_token == "refresh_token"
    mock_user_service.authenticate_user.assert_called_once_with("joao@example.com", "senha123")


def test_login_invalid_credentials(
    auth_service: AuthService,
    mock_user_service: MagicMock,
) -> None:
    """Testa login com credenciais inválidas."""
    mock_user_service.authenticate_user.side_effect = HTTPException(
        status_code=401, detail="Credenciais inválidas"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        auth_service.login("joao@example.com", "senhaerrada")
    
    assert exc_info.value.status_code == 401


def test_refresh_tokens_success(
    auth_service: AuthService,
    mock_token_service: MagicMock,
) -> None:
    """Testa refresh de tokens com token válido."""
    mock_token_service.validate_refresh_token.return_value = "user-123"
    mock_token_service.create_access_token.return_value = "new_access_token"
    mock_token_service.create_refresh_token.return_value = "new_refresh_token"
    
    result = auth_service.refresh_tokens("valid_refresh_token")
    
    assert isinstance(result, TokenResponse)
    assert result.access_token == "new_access_token"
    assert result.refresh_token == "new_refresh_token"


def test_refresh_tokens_invalid_token(
    auth_service: AuthService,
    mock_token_service: MagicMock,
) -> None:
    """Testa refresh com token inválido."""
    mock_token_service.validate_refresh_token.side_effect = JWTError("Invalid token")
    
    with pytest.raises(HTTPException) as exc_info:
        auth_service.refresh_tokens("invalid_token")
    
    assert exc_info.value.status_code == 401


def test_request_password_reset_user_exists(
    auth_service: AuthService,
    mock_user_service: MagicMock,
    mock_password_reset_repository: MagicMock,
    mock_user_data: dict[str, Any],
) -> None:
    """Testa solicitação de reset para usuário existente."""
    mock_user_service.user_repository.find_by_email.return_value = mock_user_data
    mock_password_reset_repository.generate_code.return_value = "1234"
    
    response, code = auth_service.request_password_reset("joao@example.com")
    
    assert isinstance(response, MessageResponse)
    assert code == "1234"
    mock_password_reset_repository.upsert_code.assert_called_once()


def test_request_password_reset_user_not_exists(
    auth_service: AuthService,
    mock_user_service: MagicMock,
) -> None:
    """Testa solicitação de reset para usuário inexistente."""
    mock_user_service.user_repository.find_by_email.return_value = None
    
    response, code = auth_service.request_password_reset("naoexiste@example.com")
    
    assert isinstance(response, MessageResponse)
    assert code is None


def test_verify_reset_code_success(
    auth_service: AuthService,
    mock_password_reset_repository: MagicMock,
) -> None:
    """Testa verificação de código válido."""
    code_data = {
        "user_id": "user-123",
        "token": "1234",
        "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
        "verified_at": None,
    }
    mock_password_reset_repository.find_by_code_and_email.return_value = code_data
    mock_password_reset_repository.is_code_valid.return_value = True
    mock_password_reset_repository.mark_as_verified.return_value = "reset_token_abc"
    
    result = auth_service.verify_reset_code("joao@example.com", "1234")
    
    assert result["reset_token"] == "reset_token_abc"
    assert "expires_at" in result


def test_verify_reset_code_invalid(
    auth_service: AuthService,
    mock_password_reset_repository: MagicMock,
) -> None:
    """Testa verificação de código inválido."""
    mock_password_reset_repository.find_by_code_and_email.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        auth_service.verify_reset_code("joao@example.com", "9999")
    
    assert exc_info.value.status_code == 400


def test_reset_password_success(
    auth_service: AuthService,
    mock_password_reset_repository: MagicMock,
    mock_user_service: MagicMock,
) -> None:
    """Testa redefinição de senha com token válido."""
    token_data = {
        "user_id": "user-123",
        "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
        "verified_at": datetime.now().isoformat(),
    }
    mock_password_reset_repository.find_by_token.return_value = token_data
    mock_password_reset_repository.is_token_valid.return_value = True
    
    result = auth_service.reset_password("reset_token_abc", "novasenha123")
    
    assert isinstance(result, MessageResponse)
    mock_user_service.update_user_password.assert_called_once()
    mock_password_reset_repository.delete_by_token.assert_called_once()


def test_reset_password_invalid_token(
    auth_service: AuthService,
    mock_password_reset_repository: MagicMock,
) -> None:
    """Testa redefinição de senha com token inválido."""
    mock_password_reset_repository.find_by_token.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        auth_service.reset_password("invalid_token", "novasenha123")
    
    assert exc_info.value.status_code == 400


def test_resend_reset_code(
    auth_service: AuthService,
    mock_user_service: MagicMock,
    mock_password_reset_repository: MagicMock,
    mock_user_data: dict[str, Any],
) -> None:
    """Testa reenvio de código de reset."""
    mock_user_service.user_repository.find_by_email.return_value = mock_user_data
    mock_password_reset_repository.generate_code.return_value = "5678"
    
    response, code = auth_service.resend_reset_code("joao@example.com")
    
    assert isinstance(response, MessageResponse)
    assert code == "5678"
