"""Testes unitários para PasswordResetTokenRepository."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from src.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)


@pytest.fixture
def password_reset_repo(mock_supabase: MagicMock) -> PasswordResetTokenRepository:
    """Cria instância de PasswordResetTokenRepository com mock."""
    return PasswordResetTokenRepository(mock_supabase)


def test_generate_code(password_reset_repo: PasswordResetTokenRepository) -> None:
    """Testa geração de código de 4 dígitos."""
    code = password_reset_repo.generate_code()

    assert isinstance(code, str)
    assert len(code) == 4
    assert code.isdigit()
    assert 1000 <= int(code) <= 9999


def test_find_by_code_and_email_found(
    password_reset_repo: PasswordResetTokenRepository,
    mock_supabase: MagicMock,
) -> None:
    """Testa busca de código por email quando encontrado."""
    user_data = {"id": "user-123"}
    code_data = {
        "user_id": "user-123",
        "token": "1234",
        "expires_at": datetime.now().isoformat(),
        "verified_at": None,
    }

    mock_supabase.data = user_data
    mock_execute = MagicMock()
    mock_execute.data = code_data
    mock_supabase.execute.return_value = mock_execute

    result = password_reset_repo.find_by_code_and_email("1234", "test@example.com")

    assert result == code_data


def test_find_by_code_and_email_user_not_found(
    password_reset_repo: PasswordResetTokenRepository,
    mock_supabase: MagicMock,
) -> None:
    """Testa busca quando usuário não existe."""
    mock_supabase.data = None

    result = password_reset_repo.find_by_code_and_email(
        "1234", "nonexistent@example.com"
    )

    assert result is None


def test_upsert_code(
    password_reset_repo: PasswordResetTokenRepository,
    mock_supabase: MagicMock,
) -> None:
    """Testa criação/atualização de código."""
    password_reset_repo.upsert_code(
        "user-123",
        "1234",
        datetime.now().isoformat(),
    )

    mock_supabase.table.assert_called()


def test_mark_as_verified_success(
    password_reset_repo: PasswordResetTokenRepository,
    mock_supabase: MagicMock,
) -> None:
    """Testa marcação de código como verificado."""
    mock_supabase.data = [{"token": "reset_token_abc"}]

    reset_token = password_reset_repo.mark_as_verified("1234", "user-123")

    assert isinstance(reset_token, str)
    assert len(reset_token) > 20


def test_mark_as_verified_already_verified(
    password_reset_repo: PasswordResetTokenRepository,
    mock_supabase: MagicMock,
) -> None:
    """Testa erro ao verificar código já verificado."""
    mock_supabase.data = []

    with pytest.raises(RuntimeError) as exc_info:
        password_reset_repo.mark_as_verified("1234", "user-123")

    assert "já foi verificado" in str(exc_info.value)


def test_delete_by_token(
    password_reset_repo: PasswordResetTokenRepository,
    mock_supabase: MagicMock,
) -> None:
    """Testa remoção de token."""
    password_reset_repo.delete_by_token("reset_token_abc")

    mock_supabase.table.assert_called()


def test_is_code_valid_true(
    password_reset_repo: PasswordResetTokenRepository,
) -> None:
    """Testa validação de código válido."""
    code_data = {
        "user_id": "user-123",
        "token": "1234",
        "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
        "verified_at": None,
    }

    result = password_reset_repo.is_code_valid(code_data)

    assert result is True


def test_is_code_valid_expired(
    password_reset_repo: PasswordResetTokenRepository,
) -> None:
    """Testa validação de código expirado."""
    code_data = {
        "user_id": "user-123",
        "token": "1234",
        "expires_at": (datetime.now() - timedelta(hours=1)).isoformat(),
        "verified_at": None,
    }

    result = password_reset_repo.is_code_valid(code_data)

    assert result is False


def test_is_code_valid_already_verified(
    password_reset_repo: PasswordResetTokenRepository,
) -> None:
    """Testa validação de código já verificado."""
    code_data = {
        "user_id": "user-123",
        "token": "reset_token",
        "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
        "verified_at": datetime.now().isoformat(),
    }

    result = password_reset_repo.is_code_valid(code_data)

    assert result is False


def test_is_token_valid_true(
    password_reset_repo: PasswordResetTokenRepository,
) -> None:
    """Testa validação de token válido."""
    token_data = {
        "user_id": "user-123",
        "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
        "verified_at": datetime.now().isoformat(),
    }

    result = password_reset_repo.is_token_valid(token_data)

    assert result is True


def test_is_token_valid_not_verified(
    password_reset_repo: PasswordResetTokenRepository,
) -> None:
    """Testa validação de token não verificado."""
    token_data = {
        "user_id": "user-123",
        "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
        "verified_at": None,
    }

    result = password_reset_repo.is_token_valid(token_data)

    assert result is False


def test_find_by_token(
    password_reset_repo: PasswordResetTokenRepository,
    mock_supabase: MagicMock,
) -> None:
    """Testa busca de token."""
    token_data = {
        "user_id": "user-123",
        "expires_at": datetime.now().isoformat(),
        "verified_at": datetime.now().isoformat(),
    }
    mock_supabase.data = token_data

    result = password_reset_repo.find_by_token("reset_token_abc")

    assert result == token_data
