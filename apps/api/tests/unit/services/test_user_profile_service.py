"""Testes unitários para UserProfileService."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from src.domain.entities.user import User
from src.services.user_profile_service import UserProfileService


@pytest.fixture
def user_profile_service(
    mock_cnae_repository: MagicMock,
    mock_opencnpj_client: AsyncMock,
    mock_user_repository: MagicMock,
) -> UserProfileService:
    """Cria instância de UserProfileService com mocks."""
    return UserProfileService(
        cnae_repository=mock_cnae_repository,
        opencnpj_client=mock_opencnpj_client,
        user_repository=mock_user_repository,
    )


def test_get_user_profile(
    user_profile_service: UserProfileService,
    mock_user: User,
    mock_cnae_repository: MagicMock,
    mock_user_repository: MagicMock,
) -> None:
    """Testa obtenção de perfil completo do usuário."""
    mock_cnae_repository.get_user_cnaes.return_value = [
        {"id": "4711302", "title": "Comércio varejista"},
        {"id": "4712100", "title": "Lojas de conveniência"},
    ]
    mock_user_repository.get_interested_states.return_value = ["SP", "RJ"]
    
    result = user_profile_service.get_user_profile(mock_user)
    
    assert result["name"] == mock_user.name
    assert result["email"] == mock_user.email
    assert result["cnpj"] == mock_user.cnpj
    assert result["primary_cnae"]["id"] == "4711302"
    assert len(result["secondary_cnaes"]) == 1
    assert len(result["interested_states"]) == 2


@pytest.mark.asyncio
async def test_update_user_cnpj_success(
    user_profile_service: UserProfileService,
    mock_user: User,
    mock_opencnpj_client: AsyncMock,
    mock_cnae_repository: MagicMock,
    mock_user_repository: MagicMock,
    mock_cnae_data: dict[str, Any],
) -> None:
    """Testa atualização de CNPJ com sucesso."""
    mock_opencnpj_client.get_cnpj_data.return_value = {
        "company": {"name": "Nova Empresa LTDA"},
    }
    mock_opencnpj_client.parse_cnaes_from_data.return_value = mock_cnae_data
    mock_cnae_repository.get_user_cnaes.return_value = []
    mock_user_repository.get_interested_states.return_value = []
    
    result = await user_profile_service.update_user_cnpj(mock_user, "98765432000100")
    
    assert result["cnpj"] == "98765432000100"
    mock_cnae_repository.upsert_many.assert_called_once()
    mock_user_repository.update_cnpj.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_cnpj_not_found(
    user_profile_service: UserProfileService,
    mock_user: User,
    mock_opencnpj_client: AsyncMock,
) -> None:
    """Testa atualização de CNPJ não encontrado."""
    mock_opencnpj_client.get_cnpj_data.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        await user_profile_service.update_user_cnpj(mock_user, "00000000000000")
    
    assert exc_info.value.status_code == 404


def test_update_user_profile(
    user_profile_service: UserProfileService,
    mock_user: User,
    mock_user_repository: MagicMock,
    mock_cnae_repository: MagicMock,
) -> None:
    """Testa atualização de perfil do usuário."""
    mock_cnae_repository.get_user_cnaes.return_value = []
    mock_user_repository.get_interested_states.return_value = []
    
    result = user_profile_service.update_user_profile(
        mock_user,
        name="Novo Nome",
        interested_state_siglas=["SP", "MG"],
        cnae_ids=["4711302"],
    )
    
    mock_user_repository.update_profile.assert_called_once()
    mock_user_repository.link_interested_states.assert_called_once()
    mock_cnae_repository.link_user_cnaes.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_user_cnaes_success(
    user_profile_service: UserProfileService,
    mock_user: User,
    mock_opencnpj_client: AsyncMock,
    mock_cnae_repository: MagicMock,
    mock_user_repository: MagicMock,
    mock_cnae_data: dict[str, Any],
) -> None:
    """Testa refresh de CNAEs com sucesso."""
    mock_opencnpj_client.get_cnpj_data.return_value = {"company": {}}
    mock_opencnpj_client.parse_cnaes_from_data.return_value = mock_cnae_data
    mock_cnae_repository.get_user_cnaes.return_value = []
    mock_user_repository.get_interested_states.return_value = []
    
    result = await user_profile_service.refresh_user_cnaes(mock_user)
    
    mock_cnae_repository.upsert_many.assert_called_once()
    mock_cnae_repository.link_user_cnaes.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_user_cnaes_no_cnpj(
    user_profile_service: UserProfileService,
    mock_user: User,
) -> None:
    """Testa refresh de CNAEs sem CNPJ cadastrado."""
    mock_user.cnpj = None
    
    with pytest.raises(HTTPException) as exc_info:
        await user_profile_service.refresh_user_cnaes(mock_user)
    
    assert exc_info.value.status_code == 400


def test_anonymize_user(
    user_profile_service: UserProfileService,
    mock_user: User,
    mock_user_repository: MagicMock,
) -> None:
    """Testa anonimização de usuário."""
    anonymized_data = {
        "id": "user-123",
        "name": "ANONIMIZADO_abc123",
        "email": "anonimizado_abc123@example.com",
        "anonymized_at": "2026-06-02T10:00:00Z",
    }
    mock_user_repository.anonymize_user.return_value = anonymized_data
    
    result = user_profile_service.anonymize_user(mock_user)
    
    assert "ANONIMIZADO" in result["name"]
    assert result["anonymized_at"] is not None
    mock_user_repository.anonymize_user.assert_called_once_with(mock_user.id)
