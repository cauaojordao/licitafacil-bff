"""Testes unitários para UserRepository."""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.repositories.user_repository import UserRepository


@pytest.fixture
def user_repository(mock_supabase: MagicMock) -> UserRepository:
    """Cria instância de UserRepository com mock."""
    return UserRepository(mock_supabase)


def test_find_by_email_found(
    user_repository: UserRepository,
    mock_supabase: MagicMock,
    mock_user_data: dict[str, Any],
) -> None:
    """Testa busca de usuário por email quando encontrado."""
    mock_supabase.data = mock_user_data

    result = user_repository.find_by_email("joao@example.com")

    assert result == mock_user_data
    mock_supabase.table.assert_called_with("users")


def test_find_by_email_not_found(
    user_repository: UserRepository, mock_supabase: MagicMock
) -> None:
    """Testa busca de usuário por email quando não encontrado."""
    mock_supabase.data = None

    result = user_repository.find_by_email("naoexiste@example.com")

    assert result is None


def test_find_by_cnpj_found(
    user_repository: UserRepository,
    mock_supabase: MagicMock,
    mock_user_data: dict[str, Any],
) -> None:
    """Testa busca de usuário por CNPJ quando encontrado."""
    mock_supabase.data = mock_user_data

    result = user_repository.find_by_cnpj("12345678000190")

    assert result == mock_user_data


def test_create_user(
    user_repository: UserRepository,
    mock_supabase: MagicMock,
    mock_user_data: dict[str, Any],
) -> None:
    """Testa criação de usuário simples."""
    mock_supabase.data = [mock_user_data]

    result = user_repository.create_user(
        name="João Silva",
        email="joao@example.com",
        password_hash="$2b$12$hash",
    )

    assert result == mock_user_data


def test_create_mei(
    user_repository: UserRepository,
    mock_supabase: MagicMock,
    mock_user_data: dict[str, Any],
) -> None:
    """Testa criação de usuário MEI."""
    mock_supabase.data = [mock_user_data]

    result = user_repository.create_mei(
        name="João Silva",
        email="joao@example.com",
        password_hash="$2b$12$hash",
        cnpj="12345678000190",
        company_name="Empresa LTDA",
    )

    assert result == mock_user_data


def test_update_password(
    user_repository: UserRepository,
    mock_supabase: MagicMock,
    mock_user_data: dict[str, Any],
) -> None:
    """Testa atualização de senha."""
    mock_supabase.data = [mock_user_data]

    user_repository.update_password("user-123", "$2b$12$newhash")

    mock_supabase.table.assert_called()


def test_update_profile(
    user_repository: UserRepository,
    mock_supabase: MagicMock,
    mock_user_data: dict[str, Any],
) -> None:
    """Testa atualização de perfil."""
    mock_supabase.data = [mock_user_data]

    result = user_repository.update_profile("user-123", name="Novo Nome")

    assert result == mock_user_data


def test_update_cnpj(
    user_repository: UserRepository,
    mock_supabase: MagicMock,
    mock_user_data: dict[str, Any],
) -> None:
    """Testa atualização de CNPJ."""
    mock_supabase.data = [mock_user_data]

    result = user_repository.update_cnpj(
        "user-123",
        "98765432000100",
        company_name="Nova Empresa",
    )

    assert result == mock_user_data


def test_anonymize_user(
    user_repository: UserRepository, mock_supabase: MagicMock
) -> None:
    """Testa anonimização de usuário."""
    anonymized_data = {
        "id": "user-123",
        "name": "ANONIMIZADO_abc123",
        "email": "anonimizado_abc123@example.com",
        "anonymized_at": datetime.now().isoformat(),
    }
    mock_supabase.data = [anonymized_data]

    result = user_repository.anonymize_user("user-123")

    assert "ANONIMIZADO" in result["name"]
    assert "anonimizado" in result["email"]
    assert result["anonymized_at"] is not None


def test_link_interested_states(
    user_repository: UserRepository, mock_supabase: MagicMock
) -> None:
    """Testa vinculação de estados de interesse."""
    user_repository.link_interested_states("user-123", ["SP", "RJ", "MG"])

    mock_supabase.table.assert_called()


def test_get_interested_states(
    user_repository: UserRepository, mock_supabase: MagicMock
) -> None:
    """Testa busca de estados de interesse."""
    mock_supabase.data = [
        {"state_id": "SP"},
        {"state_id": "RJ"},
    ]

    result = user_repository.get_interested_states("user-123")

    assert result == ["SP", "RJ"]


def test_mark_registration_complete(
    user_repository: UserRepository,
    mock_supabase: MagicMock,
    mock_user_data: dict[str, Any],
) -> None:
    """Testa marcação de cadastro completo."""
    mock_supabase.data = [mock_user_data]

    user_repository.mark_registration_complete("user-123")

    mock_supabase.table.assert_called()
