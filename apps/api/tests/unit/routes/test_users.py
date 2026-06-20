"""Testes de integração para rotas de usuários."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client() -> TestClient:
    """Cliente de teste do FastAPI."""
    return TestClient(app)


@patch("src.services.user_mei_service.UserMEIService.register_mei")
@patch("src.services.token_service.TokenService.create_access_token")
@patch("src.services.token_service.TokenService.create_refresh_token")
async def test_register_mei_endpoint_success(
    mock_refresh_token: MagicMock,
    mock_access_token: MagicMock,
    mock_register: MagicMock,
    client: TestClient,
    mock_user_data: dict[str, Any],
) -> None:
    """Testa endpoint de registro de MEI com sucesso."""
    mock_register.return_value = mock_user_data
    mock_access_token.return_value = "access_token"
    mock_refresh_token.return_value = "refresh_token"

    response = client.post(
        "/api/v1/users/register",
        json={
            "name": "João Silva",
            "email": "joao@example.com",
            "password": "senha12345678",
            "cnpj": "12345678000190",
            "interested_state_siglas": ["SP", "RJ"],
            "cnae_ids": ["4711302"],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_register_mei_endpoint_password_too_short(client: TestClient) -> None:
    """Testa endpoint de registro com senha muito curta."""
    response = client.post(
        "/api/v1/users/register",
        json={
            "name": "João Silva",
            "email": "joao@example.com",
            "password": "123",
            "cnpj": "12345678000190",
            "interested_state_siglas": ["SP"],
            "cnae_ids": ["4711302"],
        },
    )

    assert response.status_code == 422


@patch("src.services.user_mei_service.UserMEIService.check_email_availability")
def test_check_email_endpoint_available(
    mock_check: MagicMock,
    client: TestClient,
) -> None:
    """Testa endpoint de verificação de email disponível."""
    mock_check.return_value = True

    response = client.get("/api/v1/users/check-email?email=teste@example.com")

    assert response.status_code == 200
    data = response.json()
    assert data["available"] is True


@patch("src.core.dependencies.get_current_user")
@patch("src.services.user_profile_service.UserProfileService.get_user_profile")
def test_get_profile_endpoint(
    mock_get_profile: MagicMock,
    mock_get_user: MagicMock,
    client: TestClient,
    mock_user: Any,
) -> None:
    """Testa endpoint de obtenção de perfil."""
    mock_get_user.return_value = mock_user
    mock_get_profile.return_value = {
        "name": "João Silva",
        "email": "joao@example.com",
        "cnpj": "12345678000190",
        "company_name": "Empresa LTDA",
        "primary_cnae": {"id": "4711302", "description": "Comércio varejista"},
        "secondary_cnaes": [],
        "interested_states": [{"sigla": "SP"}],
    }

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "João Silva"


@patch("src.core.dependencies.get_current_user")
@patch("src.services.user_profile_service.UserProfileService.update_user_profile")
def test_update_profile_endpoint(
    mock_update: MagicMock,
    mock_get_user: MagicMock,
    client: TestClient,
    mock_user: Any,
) -> None:
    """Testa endpoint de atualização de perfil."""
    mock_get_user.return_value = mock_user
    mock_update.return_value = {
        "name": "Novo Nome",
        "email": "joao@example.com",
        "cnpj": "12345678000190",
        "company_name": "Empresa LTDA",
        "primary_cnae": None,
        "secondary_cnaes": [],
        "interested_states": [],
    }

    response = client.patch(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer fake_token"},
        json={"name": "Novo Nome"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Novo Nome"


@patch("src.core.dependencies.get_current_user")
@patch("src.services.user_profile_service.UserProfileService.update_user_cnpj")
async def test_update_cnpj_endpoint(
    mock_update_cnpj: MagicMock,
    mock_get_user: MagicMock,
    client: TestClient,
    mock_user: Any,
) -> None:
    """Testa endpoint de atualização de CNPJ."""
    mock_get_user.return_value = mock_user
    mock_update_cnpj.return_value = {
        "name": "João Silva",
        "email": "joao@example.com",
        "cnpj": "98765432000100",
        "company_name": "Nova Empresa",
        "primary_cnae": None,
        "secondary_cnaes": [],
        "interested_states": [],
    }

    response = client.patch(
        "/api/v1/users/me/cnpj",
        headers={"Authorization": "Bearer fake_token"},
        json={"cnpj": "98765432000100"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["cnpj"] == "98765432000100"


@patch("src.core.dependencies.get_current_user")
@patch("src.services.user_profile_service.UserProfileService.refresh_user_cnaes")
async def test_refresh_cnaes_endpoint(
    mock_refresh: MagicMock,
    mock_get_user: MagicMock,
    client: TestClient,
    mock_user: Any,
) -> None:
    """Testa endpoint de refresh de CNAEs."""
    mock_get_user.return_value = mock_user
    mock_refresh.return_value = {
        "name": "João Silva",
        "email": "joao@example.com",
        "cnpj": "12345678000190",
        "company_name": "Empresa LTDA",
        "primary_cnae": {"id": "4711302", "description": "Comércio"},
        "secondary_cnaes": [],
        "interested_states": [],
    }

    response = client.post(
        "/api/v1/users/me/refresh-cnaes",
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 200


@patch("src.core.dependencies.get_current_user")
@patch("src.services.user_profile_service.UserProfileService.anonymize_user")
def test_anonymize_user_endpoint(
    mock_anonymize: MagicMock,
    mock_get_user: MagicMock,
    client: TestClient,
    mock_user: Any,
) -> None:
    """Testa endpoint de anonimização de usuário."""
    mock_get_user.return_value = mock_user
    mock_anonymize.return_value = {
        "id": "user-123",
        "name": "ANONIMIZADO_abc123",
        "email": "anonimizado_abc123@example.com",
        "anonymized_at": "2026-06-02T10:00:00Z",
    }

    response = client.delete(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "anonymized_at" in data


def test_profile_endpoint_unauthorized(client: TestClient) -> None:
    """Testa endpoint de perfil sem autenticação."""
    response = client.get("/api/v1/users/me")

    assert response.status_code == 403
