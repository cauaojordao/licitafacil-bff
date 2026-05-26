"""Repository para gerenciamento de códigos de reset de senha."""

import secrets
from datetime import UTC, datetime

from supabase import Client


class PasswordResetTokenRepository:
    """Repository para operações com códigos de reset de senha."""

    def __init__(self, db: Client):
        """
        Inicializa o repository com a conexão do banco.

        Args:
            db: Cliente Supabase para acesso ao banco de dados
        """
        self.db = db
        self.table = "password_reset_tokens"

    def generate_code(self) -> str:
        """
        Gera um código de 4 dígitos criptograficamente seguro.

        Returns:
            Código de 4 dígitos como string
        """
        return str(secrets.randbelow(9000) + 1000)

    def find_by_code_and_email(self, code: str, email: str) -> dict | None:
        """
        Busca um código de reset pelo valor e email do usuário.

        Args:
            code: Código de reset (4 dígitos)
            email: Email do usuário

        Returns:
            Dados do código ou None se não encontrado
        """
        # Primeiro busca o usuário pelo email para evitar colisões de código
        user = (
            self.db.table("users")
            .select("id")
            .eq("email", email)
            .maybe_single()
            .execute()
        )

        if not user or not user.data:
            return None

        user_id = user.data["id"]

        # Agora busca o código específico desse usuário
        result = (
            self.db.table(self.table)
            .select("user_id, token, expires_at, verified_at")
            .eq("user_id", user_id)
            .eq("token", code)
            .maybe_single()
            .execute()
        )

        return result.data if result and result.data else None

    def find_by_token(self, token: str) -> dict | None:
        """
        Busca um token de reset pelo valor.

        Args:
            token: Token de reset

        Returns:
            Dados do token ou None se não encontrado
        """
        result = (
            self.db.table(self.table)
            .select("user_id, expires_at, verified_at")
            .eq("token", token)
            .maybe_single()
            .execute()
        )
        return result.data if result else None

    def upsert_code(self, user_id: str, code: str, expires_at: str) -> None:
        """
        Cria ou atualiza um código de reset para um usuário.

        Args:
            user_id: ID do usuário
            code: Código de reset gerado (4 dígitos)
            expires_at: Data/hora de expiração no formato ISO
        """
        self.db.table(self.table).upsert(
            {
                "user_id": user_id,
                "token": code,
                "expires_at": expires_at,
                "verified_at": None,
            }
        ).execute()

    def mark_as_verified(self, code: str, user_id: str) -> str:
        """
        Marca um código como verificado e retorna token de uso único.

        Args:
            code: Código de 4 dígitos verificado
            user_id: ID do usuário (para evitar race conditions)

        Returns:
            Token alfanumérico de uso único para reset final

        Raises:
            RuntimeError: Se o código já foi verificado ou não existe
        """
        reset_token = secrets.token_urlsafe(32)

        # Update com condição para evitar race condition
        result = (
            self.db.table(self.table)
            .update(
                {
                    "verified_at": datetime.now(UTC).isoformat(),
                    "token": reset_token,
                }
            )
            .eq("user_id", user_id)
            .eq("token", code)
            .is_("verified_at", "null")
            .execute()
        )

        # Verifica se o update realmente afetou alguma linha
        if not result.data or len(result.data) == 0:
            raise RuntimeError("Código já foi verificado ou não existe")

        return reset_token

    def delete_by_token(self, token: str) -> None:
        """
        Remove um token de reset após uso.

        Args:
            token: Token a ser removido
        """
        self.db.table(self.table).delete().eq("token", token).execute()

    def is_code_valid(self, code_data: dict) -> bool:
        """
        Verifica se um código ainda é válido (não expirou e não foi verificado).

        Args:
            code_data: Dados do código retornados por find_by_code_and_email

        Returns:
            True se válido, False se expirado ou já verificado
        """
        if not code_data:
            return False

        # Código já foi verificado (convertido em token)
        if code_data.get("verified_at"):
            return False

        expires_at = datetime.fromisoformat(code_data["expires_at"])
        return datetime.now(UTC) <= expires_at

    def is_token_valid(self, token_data: dict) -> bool:
        """
        Verifica se um token ainda é válido (não expirou).

        Args:
            token_data: Dados do token retornados por find_by_token

        Returns:
            True se válido, False se expirado
        """
        if not token_data:
            return False

        # Token deve ter sido verificado
        if not token_data.get("verified_at"):
            return False

        expires_at = datetime.fromisoformat(token_data["expires_at"])
        return datetime.now(UTC) <= expires_at
