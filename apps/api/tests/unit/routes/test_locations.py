"""Testes de integração para rotas de localidades (estados e cidades)."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client() -> TestClient:
    """Cliente de teste do FastAPI."""
    return TestClient(app)


@patch("src.integrations.ibge.IBGEClient.get_states")
async def test_get_states_endpoint(
    mock_get_states: AsyncMock,
    client: TestClient,
) -> None:
    """Testa endpoint de listagem de estados."""
    mock_get_states.return_value = [
        {"id": "35", "sigla": "SP", "nome": "São Paulo"},
        {"id": "33", "sigla": "RJ", "nome": "Rio de Janeiro"},
    ]

    response = client.get("/api/v1/locations/states")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["sigla"] == "SP"


@patch("src.integrations.ibge.IBGEClient.get_cities_by_state")
async def test_get_cities_by_state_endpoint(
    mock_get_cities: AsyncMock,
    client: TestClient,
) -> None:
    """Testa endpoint de listagem de cidades por estado."""
    mock_get_cities.return_value = [
        {"id": "3550308", "nome": "São Paulo"},
        {"id": "3509502", "nome": "Campinas"},
    ]

    response = client.get("/api/v1/locations/states/SP/cities")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["nome"] == "São Paulo"


@patch("src.integrations.ibge.IBGEClient.get_states")
async def test_get_states_endpoint_error(
    mock_get_states: AsyncMock,
    client: TestClient,
) -> None:
    """Testa endpoint de estados com erro na API do IBGE."""
    mock_get_states.side_effect = Exception("Erro na API do IBGE")

    response = client.get("/api/v1/locations/states")

    assert response.status_code == 500


@patch("src.integrations.ibge.IBGEClient.get_cities_by_state")
async def test_get_cities_endpoint_empty(
    mock_get_cities: AsyncMock,
    client: TestClient,
) -> None:
    """Testa endpoint de cidades sem resultados."""
    mock_get_cities.return_value = []

    response = client.get("/api/v1/locations/states/XX/cities")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0
