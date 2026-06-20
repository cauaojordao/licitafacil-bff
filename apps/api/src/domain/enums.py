"""Enumerações do domínio."""

from enum import Enum


class TokenType(Enum):
    """Tipos de token suportados pelo sistema."""

    ACCESS = "access"
    REFRESH = "refresh"
