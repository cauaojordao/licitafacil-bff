"""
Testes de integração para as rotas de autenticação.

Usamos o TestClient do FastAPI/httpx que simula requisições HTTP
sem precisar subir um servidor real.

O mock do Supabase é feito com unittest.mock para isolar a lógica
da API do banco de dados durante os testes.
"""

from unittest.mock import MagicMock

import pytest
from api.db.supabase import get_supabase
from api.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def mock_db() -> MagicMock:
    """Cria um mock do cliente Supabase."""
    return MagicMock()


@pytest.fixture
def client(mock_db: MagicMock) -> TestClient:
    """Substitui a dependência do Supabase pelo mock e retorna o TestClient."""
    app.dependency_overrides[get_supabase] = lambda: mock_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_success(client: TestClient, mock_db: MagicMock) -> None:
    # Simula: usuário não existe ainda
    mock_result = mock_db.table.return_value.select.return_value.eq
    mock_result.return_value.maybe_single.return_value.execute.return_value.data = None
    # Simula: insert retorna o novo usuário com ID
    mock_db.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": "user-123"}
    ]

    response = client.post(
        "/api/v1/auth/register",
        json={"name": "João", "email": "joao@example.com", "password": "senha123"},
    )

    assert response.status_code == 201
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_register_duplicate_email(client: TestClient, mock_db: MagicMock) -> None:
    # Simula: e-mail já cadastrado
    mock_result = mock_db.table.return_value.select.return_value.eq
    mock_result.return_value.maybe_single.return_value.execute.return_value.data = {
        "id": "user-existing"
    }

    response = client.post(
        "/api/v1/auth/register",
        json={"name": "João", "email": "joao@example.com", "password": "senha123"},
    )

    assert response.status_code == 409


def test_login_invalid_credentials(client: TestClient, mock_db: MagicMock) -> None:
    # Simula: usuário não encontrado
    mock_result = mock_db.table.return_value.select.return_value.eq
    mock_result.return_value.maybe_single.return_value.execute.return_value.data = None

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "joao@example.com", "password": "errada"},
    )

    assert response.status_code == 401
