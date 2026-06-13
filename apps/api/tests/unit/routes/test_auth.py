"""Testes de integração para rotas de autenticação."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client() -> TestClient:
    """Cliente de teste do FastAPI."""
    return TestClient(app)


@patch("src.services.auth_service.AuthService.login")
def test_login_endpoint_success(
    mock_login: MagicMock,
    client: TestClient,
) -> None:
    """Testa endpoint de login com sucesso."""
    from src.domain.schemas.auth import TokenResponse

    mock_login.return_value = TokenResponse(
        access_token="access_token_123",
        refresh_token="refresh_token_456",
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "joao@example.com", "password": "senha123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@patch("src.services.auth_service.AuthService.login")
def test_login_endpoint_invalid_credentials(
    mock_login: MagicMock,
    client: TestClient,
) -> None:
    """Testa endpoint de login com credenciais inválidas."""
    from fastapi import HTTPException

    mock_login.side_effect = HTTPException(
        status_code=401,
        detail="Credenciais inválidas",
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "joao@example.com", "password": "senhaerrada"},
    )

    assert response.status_code == 401


@patch("src.services.auth_service.AuthService.refresh_tokens")
def test_refresh_endpoint_success(
    mock_refresh: MagicMock,
    client: TestClient,
) -> None:
    """Testa endpoint de refresh de tokens."""
    from src.domain.schemas.auth import TokenResponse

    mock_refresh.return_value = TokenResponse(
        access_token="new_access_token",
        refresh_token="new_refresh_token",
    )

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "old_refresh_token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "new_access_token"


@patch("src.services.auth_service.AuthService.request_password_reset")
@patch("src.integrations.email.send_reset_code_email")
async def test_request_password_reset_endpoint(
    mock_send_email: MagicMock,
    mock_request_reset: MagicMock,
    client: TestClient,
) -> None:
    """Testa endpoint de solicitação de reset de senha."""
    from src.domain.schemas.auth import MessageResponse

    mock_request_reset.return_value = (
        MessageResponse(message="Email enviado"),
        "1234",
    )

    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "joao@example.com"},
    )

    assert response.status_code == 202


@patch("src.services.auth_service.AuthService.verify_reset_code")
def test_verify_reset_code_endpoint(
    mock_verify: MagicMock,
    client: TestClient,
) -> None:
    """Testa endpoint de verificação de código de reset."""
    mock_verify.return_value = {
        "reset_token": "reset_token_abc",
        "expires_at": "2026-06-02T12:00:00Z",
    }

    response = client.post(
        "/api/v1/auth/password-reset/verify",
        json={"email": "joao@example.com", "code": "1234"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "reset_token" in data


@patch("src.services.auth_service.AuthService.reset_password")
def test_complete_password_reset_endpoint(
    mock_reset: MagicMock,
    client: TestClient,
) -> None:
    """Testa endpoint de conclusão de reset de senha."""
    from src.domain.schemas.auth import MessageResponse

    mock_reset.return_value = MessageResponse(message="Senha atualizada")

    response = client.post(
        "/api/v1/auth/password-reset/complete",
        json={"reset_token": "reset_token_abc", "new_password": "novasenha123"},
    )

    assert response.status_code == 200


@patch("src.core.dependencies.get_current_user")
def test_logout_endpoint(
    mock_get_user: MagicMock,
    client: TestClient,
    mock_user: Any,
) -> None:
    """Testa endpoint de logout."""
    mock_get_user.return_value = mock_user

    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_login_endpoint_missing_fields(client: TestClient) -> None:
    """Testa endpoint de login com campos faltando."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "joao@example.com"},
    )

    assert response.status_code == 422


def test_login_endpoint_invalid_email_format(client: TestClient) -> None:
    """Testa endpoint de login com email inválido."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "email-invalido", "password": "senha123"},
    )

    assert response.status_code == 422
