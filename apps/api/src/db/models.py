"""Modelos de dados do banco (estruturas de tabelas)."""

from typing import TypedDict

USERS_TABLE = "users"
PASSWORD_RESET_TOKENS_TABLE = "password_reset_tokens"


class UserModel(TypedDict, total=False):
    """
    Modelo representando a estrutura da tabela users.

    Attributes:
        id: ID único do usuário (UUID)
        name: Nome completo do usuário
        email: Endereço de e-mail único
        password_hash: Hash bcrypt da senha
        created_at: Timestamp de criação do registro
        updated_at: Timestamp de última atualização
    """

    id: str
    name: str
    email: str
    password_hash: str
    created_at: str
    updated_at: str


class PasswordResetTokenModel(TypedDict, total=False):
    """
    Modelo representando a estrutura da tabela password_reset_tokens.

    Attributes:
        user_id: ID do usuário (FK para users.id)
        token: Token seguro para reset de senha
        expires_at: Timestamp de expiração do token
        created_at: Timestamp de criação do registro
    """

    user_id: str
    token: str
    expires_at: str
    created_at: str
