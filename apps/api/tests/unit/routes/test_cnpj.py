"""Testes de integração para rotas de consulta CNPJ."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client() -> TestClient:
    """Cliente de teste do FastAPI."""
    return TestClient(app)


@patch("src.integrations.opencnpj.OpenCNPJClient.get_cnpj_data")
@patch("src.integrations.opencnpj.OpenCNPJClient.parse_cnaes_from_data")
@patch("src.integrations.opencnpj.OpenCNPJClient.clean_cnpj")
@patch("src.integrations.opencnpj.OpenCNPJClient.format_cnpj")
async def test_get_cnpj_cnaes_endpoint_success(
    mock_format: MagicMock,
    mock_clean: MagicMock,
    mock_parse: MagicMock,
    mock_get_data: AsyncMock,
    client: TestClient,
    mock_cnae_data: dict[str, Any],
) -> None:
    """Testa endpoint de consulta de CNAEs com sucesso."""
    mock_get_data.return_value = {"company": {"name": "Empresa LTDA"}}
    mock_parse.return_value = mock_cnae_data
    mock_clean.return_value = "12345678000190"
    mock_format.return_value = "12.345.678/0001-90"

    response = client.get("/api/v1/cnpj/cnaes?cnpj=12345678000190")

    assert response.status_code == 200
    data = response.json()
    assert "cnpj" in data
    assert "razao_social" in data
    assert "primary_cnae" in data
    assert "secondary_cnaes" in data


@patch("src.integrations.opencnpj.OpenCNPJClient.get_cnpj_data")
async def test_get_cnpj_cnaes_not_found(
    mock_get_data: AsyncMock,
    client: TestClient,
) -> None:
    """Testa endpoint de consulta de CNPJ não encontrado."""
    mock_get_data.return_value = None

    response = client.get("/api/v1/cnpj/cnaes?cnpj=00000000000000")

    assert response.status_code == 404


@patch("src.integrations.opencnpj.OpenCNPJClient.clean_cnpj")
def test_get_cnpj_cnaes_invalid_format(
    mock_clean: MagicMock,
    client: TestClient,
) -> None:
    """Testa endpoint com CNPJ em formato inválido."""
    mock_clean.side_effect = ValueError("CNPJ inválido")

    response = client.get("/api/v1/cnpj/cnaes?cnpj=123")

    assert response.status_code == 400


def test_get_cnpj_cnaes_missing_param(client: TestClient) -> None:
    """Testa endpoint sem parâmetro cnpj."""
    response = client.get("/api/v1/cnpj/cnaes")

    assert response.status_code == 422
