"""Testes de integração para rotas de oportunidades."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client() -> TestClient:
    """Cliente de teste do FastAPI."""
    return TestClient(app)


@patch("src.core.dependencies.get_current_user")
@patch("src.services.opportunity_service.OpportunityService.list_opportunities")
def test_list_opportunities_endpoint(
    mock_list: MagicMock,
    mock_get_user: MagicMock,
    client: TestClient,
    mock_user: Any,
    mock_opportunity_data: dict[str, Any],
) -> None:
    """Testa endpoint de listagem de oportunidades."""
    mock_get_user.return_value = mock_user
    mock_list.return_value = {
        "opportunities": [mock_opportunity_data],
        "pagination": {
            "page": 1,
            "page_size": 20,
            "total": 1,
            "total_pages": 1,
        },
    }

    response = client.get(
        "/api/v1/opportunities",
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "opportunities" in data
    assert "pagination" in data
    assert len(data["opportunities"]) == 1


@patch("src.core.dependencies.get_current_user")
@patch("src.services.opportunity_service.OpportunityService.list_opportunities")
def test_list_opportunities_with_filters(
    mock_list: MagicMock,
    mock_get_user: MagicMock,
    client: TestClient,
    mock_user: Any,
) -> None:
    """Testa endpoint de listagem com filtros."""
    mock_get_user.return_value = mock_user
    mock_list.return_value = {
        "opportunities": [],
        "pagination": {
            "page": 1,
            "page_size": 20,
            "total": 0,
            "total_pages": 0,
        },
    }

    response = client.get(
        "/api/v1/opportunities?state=SP&modality=PREGAO_ELETRONICO&page=1&page_size=10",
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 200


@patch("src.core.dependencies.get_current_user")
@patch(
    "src.services.opportunity_service.OpportunityService.list_opportunities_by_compatibility"
)
def test_list_opportunities_by_compatibility(
    mock_list: MagicMock,
    mock_get_user: MagicMock,
    client: TestClient,
    mock_user: Any,
    mock_opportunity_data: dict[str, Any],
) -> None:
    """Testa endpoint de listagem por compatibilidade."""
    mock_get_user.return_value = mock_user
    opp_with_score = mock_opportunity_data.copy()
    opp_with_score["compatibility_score"] = 85
    opp_with_score["compatibility_label"] = "ALTA"

    mock_list.return_value = {
        "opportunities": [opp_with_score],
        "pagination": {
            "page": 1,
            "page_size": 20,
            "total": 1,
            "total_pages": 1,
        },
    }

    response = client.get(
        "/api/v1/opportunities/by-compatibility",
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["opportunities"]) == 1
    assert "compatibility_score" in data["opportunities"][0]


@patch("src.core.dependencies.get_current_user")
@patch("src.services.opportunity_service.OpportunityService.get_opportunity_detail")
def test_get_opportunity_detail(
    mock_get: MagicMock,
    mock_get_user: MagicMock,
    client: TestClient,
    mock_user: Any,
    mock_opportunity_data: dict[str, Any],
) -> None:
    """Testa endpoint de detalhes de oportunidade."""
    mock_get_user.return_value = mock_user
    mock_get.return_value = mock_opportunity_data

    response = client.get(
        "/api/v1/opportunities/opp-123",
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "opp-123"


def test_list_opportunities_unauthorized(client: TestClient) -> None:
    """Testa endpoint de oportunidades sem autenticação."""
    response = client.get("/api/v1/opportunities")

    assert response.status_code == 403
