"""Fixtures compartilhadas para todos os testes."""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.domain.entities.user import User
from src.main import app


@pytest.fixture
def mock_supabase() -> MagicMock:
    """Mock do cliente Supabase."""
    mock = MagicMock()
    mock.table.return_value = mock
    mock.select.return_value = mock
    mock.insert.return_value = mock
    mock.update.return_value = mock
    mock.delete.return_value = mock
    mock.eq.return_value = mock
    mock.is_.return_value = mock
    mock.maybe_single.return_value = mock
    mock.limit.return_value = mock
    mock.order.return_value = mock
    mock.execute.return_value = mock
    return mock


@pytest.fixture
def mock_user_data() -> dict[str, Any]:
    """Dados de mock de um usuário."""
    return {
        "id": "user-123-456",
        "name": "João Silva",
        "email": "joao@example.com",
        "password_hash": "$2b$12$hashedpassword",
        "cnpj": "12345678000190",
        "company_name": "Empresa Teste LTDA",
        "anonymized_at": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@pytest.fixture
def mock_user(mock_user_data: dict[str, Any]) -> User:
    """Entidade User de mock."""
    return User(**mock_user_data)


@pytest.fixture
def mock_opportunity_data() -> dict[str, Any]:
    """Dados de mock de uma oportunidade."""
    return {
        "id": "opp-123",
        "identifier": "EDITAL-2026-001",
        "title": "Fornecimento de Material de Escritório",
        "modality": "PREGAO_ELETRONICO",
        "estimated_value": 50000.0,
        "status": "OPEN",
        "bid_opening_date": "2026-07-15T10:00:00Z",
        "deadline_date": "2026-07-10T23:59:59Z",
        "days_until_deadline": 38,
        "state_sigla": "SP",
        "city_name": "São Paulo",
        "description": "Aquisição de material de escritório",
        "source_url": "https://example.com",
        "created_at": datetime.now().isoformat(),
    }


@pytest.fixture
def mock_token() -> str:
    """Token JWT de mock."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsImV4cCI6OTk5OTk5OTk5OX0.signature"


@pytest.fixture
def client() -> TestClient:
    """Cliente de teste do FastAPI."""
    return TestClient(app)


@pytest.fixture
def mock_user_repository() -> MagicMock:
    """Mock do UserRepository."""
    return MagicMock()


@pytest.fixture
def mock_cnae_repository() -> MagicMock:
    """Mock do CNAERepository."""
    return MagicMock()


@pytest.fixture
def mock_opportunity_repository() -> MagicMock:
    """Mock do OpportunityRepository."""
    return MagicMock()


@pytest.fixture
def mock_password_reset_repository() -> MagicMock:
    """Mock do PasswordResetTokenRepository."""
    return MagicMock()


@pytest.fixture
def mock_opencnpj_client() -> AsyncMock:
    """Mock do OpenCNPJClient."""
    mock = MagicMock()
    mock.get_cnpj_data = AsyncMock()
    mock.parse_cnaes_from_data = MagicMock()
    mock.clean_cnpj = MagicMock()
    mock.format_cnpj = MagicMock()
    return mock


@pytest.fixture
def mock_ibge_client() -> AsyncMock:
    """Mock do IBGEClient."""
    mock = MagicMock()
    mock.get_states = AsyncMock()
    mock.get_cities_by_state = AsyncMock()
    return mock


@pytest.fixture
def mock_email_sender() -> AsyncMock:
    """Mock da função de envio de email."""
    return AsyncMock()


@pytest.fixture
def mock_cnae_data() -> dict[str, Any]:
    """Dados de mock de CNAEs."""
    return {
        "primary": {"id": "4711302", "title": "Comércio varejista de mercadorias em geral"},
        "secondary": [
            {"id": "4712100", "title": "Comércio varejista de mercadorias em lojas de conveniência"},
        ],
    }
