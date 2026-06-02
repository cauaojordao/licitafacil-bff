"""Testes unitários para UserMEIService."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from src.services.user_mei_service import UserMEIService


@pytest.fixture
def user_mei_service(
    mock_user_repository: MagicMock,
    mock_cnae_repository: MagicMock,
    mock_opencnpj_client: AsyncMock,
) -> UserMEIService:
    """Cria instância de UserMEIService com mocks."""
    return UserMEIService(
        user_repository=mock_user_repository,
        cnae_repository=mock_cnae_repository,
        opencnpj_client=mock_opencnpj_client,
    )


@pytest.mark.asyncio
async def test_register_mei_success(
    user_mei_service: UserMEIService,
    mock_user_repository: MagicMock,
    mock_cnae_repository: MagicMock,
    mock_opencnpj_client: AsyncMock,
    mock_user_data: dict[str, Any],
    mock_cnae_data: dict[str, Any],
) -> None:
    """Testa registro de MEI com sucesso."""
    mock_user_repository.find_by_email.return_value = None
    mock_opencnpj_client.get_cnpj_data.return_value = {
        "company": {"name": "Empresa LTDA"},
    }
    mock_opencnpj_client.parse_cnaes_from_data.return_value = mock_cnae_data
    mock_user_repository.create_mei.return_value = mock_user_data
    mock_user_repository.find_by_id.return_value = mock_user_data
    
    result = await user_mei_service.register_mei(
        name="João Silva",
        email="joao@example.com",
        password="senha12345678",
        cnpj="12345678000190",
        interested_state_siglas=["SP", "RJ"],
        cnae_ids=["4711302"],
    )
    
    assert result["id"] == "user-123-456"
    mock_user_repository.create_mei.assert_called_once()
    mock_cnae_repository.link_user_cnaes.assert_called_once()
    mock_user_repository.link_interested_states.assert_called_once()


@pytest.mark.asyncio
async def test_register_mei_email_already_exists(
    user_mei_service: UserMEIService,
    mock_user_repository: MagicMock,
    mock_user_data: dict[str, Any],
) -> None:
    """Testa registro com email já cadastrado."""
    mock_user_repository.find_by_email.return_value = mock_user_data
    
    with pytest.raises(HTTPException) as exc_info:
        await user_mei_service.register_mei(
            name="João Silva",
            email="joao@example.com",
            password="senha12345678",
            cnpj="12345678000190",
            interested_state_siglas=["SP"],
            cnae_ids=["4711302"],
        )
    
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_register_mei_cnpj_api_error(
    user_mei_service: UserMEIService,
    mock_user_repository: MagicMock,
    mock_cnae_repository: MagicMock,
    mock_opencnpj_client: AsyncMock,
    mock_user_data: dict[str, Any],
) -> None:
    """Testa registro quando API de CNPJ falha (continua registro)."""
    mock_user_repository.find_by_email.return_value = None
    mock_opencnpj_client.get_cnpj_data.side_effect = Exception("API Error")
    mock_user_repository.create_mei.return_value = mock_user_data
    mock_user_repository.find_by_id.return_value = mock_user_data
    
    result = await user_mei_service.register_mei(
        name="João Silva",
        email="joao@example.com",
        password="senha12345678",
        cnpj="12345678000190",
        interested_state_siglas=["SP"],
        cnae_ids=["4711302"],
    )
    
    assert result["id"] == "user-123-456"
    mock_user_repository.create_mei.assert_called_once()


def test_check_email_availability_available(
    user_mei_service: UserMEIService,
    mock_user_repository: MagicMock,
) -> None:
    """Testa verificação de email disponível."""
    mock_user_repository.find_by_email.return_value = None
    
    result = user_mei_service.check_email_availability("teste@example.com")
    
    assert result is True


def test_check_email_availability_taken(
    user_mei_service: UserMEIService,
    mock_user_repository: MagicMock,
    mock_user_data: dict[str, Any],
) -> None:
    """Testa verificação de email já cadastrado."""
    mock_user_repository.find_by_email.return_value = mock_user_data
    
    result = user_mei_service.check_email_availability("joao@example.com")
    
    assert result is False
