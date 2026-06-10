"""Validação de força de senha."""

import re

COMMON_PASSWORDS = {
    "123456",
    "password",
    "123456789",
    "12345678",
    "12345",
    "1234567",
    "senha",
    "123123",
    "qwerty",
    "abc123",
    "password123",
    "admin",
    "letmein",
    "welcome",
    "monkey",
    "1234567890",
    "senha123",
    "admin123",
}

MIN_PASSWORD_LENGTH = 8


class PasswordValidationError(ValueError):
    pass


def validate_password_strength(password: str) -> None:
    """
    Valida força da senha conforme requisitos de segurança.

    Requirements:
        - Mínimo 8 caracteres
        - Pelo menos uma letra maiúscula
        - Pelo menos uma letra minúscula
        - Pelo menos um número
        - Pelo menos um caractere especial
        - Não pode ser senha comum

    Args:
        password: Senha a ser validada

    Raises:
        PasswordValidationError: Se senha não atender aos requisitos
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordValidationError(
            f"A senha deve ter pelo menos {MIN_PASSWORD_LENGTH} caracteres"
        )

    if not re.search(r"[A-Z]", password):
        raise PasswordValidationError(
            "A senha deve conter pelo menos uma letra maiúscula"
        )

    if not re.search(r"[a-z]", password):
        raise PasswordValidationError(
            "A senha deve conter pelo menos uma letra minúscula"
        )

    if not re.search(r"\d", password):
        raise PasswordValidationError("A senha deve conter pelo menos um número")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;`~]', password):
        raise PasswordValidationError(
            "A senha deve conter pelo menos um caractere especial válido"
        )

    if password.lower() in COMMON_PASSWORDS:
        raise PasswordValidationError(
            "Esta senha é muito comum. Escolha uma senha mais segura"
        )
