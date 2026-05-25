"""Repository para gerenciamento de tokens de reset de senha."""

from datetime import UTC, datetime

from supabase import Client


class PasswordResetTokenRepository:
    """Repository para operações com tokens de reset de senha."""

    def __init__(self, db: Client):
        """
        Inicializa o repository com a conexão do banco.

        Args:
            db: Cliente Supabase para acesso ao banco de dados
        """
        self.db = db
        self.table = "password_reset_tokens"

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
            .select("user_id, expires_at")
            .eq("token", token)
            .maybe_single()
            .execute()
        )
        return result.data if result else None

    def upsert(self, user_id: str, token: str, expires_at: str) -> None:
        """
        Cria ou atualiza um token de reset para um usuário.

        Args:
            user_id: ID do usuário
            token: Token de reset gerado
            expires_at: Data/hora de expiração no formato ISO
        """
        self.db.table(self.table).upsert(
            {"user_id": user_id, "token": token, "expires_at": expires_at}
        ).execute()

    def delete_by_token(self, token: str) -> None:
        """
        Remove um token de reset após uso.

        Args:
            token: Token a ser removido
        """
        self.db.table(self.table).delete().eq("token", token).execute()

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

        expires_at = datetime.fromisoformat(token_data["expires_at"])
        return datetime.now(UTC) <= expires_at
