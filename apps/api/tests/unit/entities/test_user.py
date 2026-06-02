"""Testes unitários para a entidade User."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.domain.entities.user import User


def test_user_creation_success() -> None:
    """Testa criação de User com dados válidos."""
    user = User(
        id="user-123",
        name="João Silva",
        email="joao@example.com",
        password_hash="$2b$12$hash",
        cnpj="12345678000190",
        company_name="Empresa LTDA",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    assert user.id == "user-123"
    assert user.name == "João Silva"
    assert user.email == "joao@example.com"
    assert user.cnpj == "12345678000190"
    assert user.anonymized_at is None


def test_user_creation_minimal() -> None:
    """Testa criação de User com campos mínimos."""
    user = User(
        id="user-123",
        name="João Silva",
        email="joao@example.com",
        password_hash="$2b$12$hash",
    )
    
    assert user.id == "user-123"
    assert user.cnpj is None
    assert user.company_name is None
    assert user.anonymized_at is None


def test_user_invalid_email() -> None:
    """Testa que email inválido levanta ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        User(
            id="user-123",
            name="João Silva",
            email="email-invalido",
            password_hash="$2b$12$hash",
        )
    
    assert "email" in str(exc_info.value)


def test_user_password_hash_excluded() -> None:
    """Testa que password_hash é excluído da serialização."""
    user = User(
        id="user-123",
        name="João Silva",
        email="joao@example.com",
        password_hash="$2b$12$hash",
    )
    
    user_dict = user.model_dump()
    assert "password_hash" not in user_dict


def test_user_anonymized() -> None:
    """Testa User anonimizado."""
    user = User(
        id="user-123",
        name="ANONIMIZADO_abc123",
        email="anonimizado_abc123@example.com",
        password_hash="ANONYMIZED_abc123",
        anonymized_at=datetime.now(),
    )
    
    assert user.anonymized_at is not None
    assert "ANONIMIZADO" in user.name
    assert user.cnpj is None
