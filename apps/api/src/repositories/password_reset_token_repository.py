"""Repository para gerenciamento de códigos de reset de senha."""

import secrets
from datetime import UTC, datetime

from supabase import Client


class PasswordResetTokenRepository:
    """Repository para operações com códigos de reset de senha."""

    def __init__(self, db: Client):
        self.db = db
        self.table = "password_reset_tokens"

    def generate_code(self) -> str:
        return str(secrets.randbelow(9000) + 1000)

    def find_by_code_and_email(self, code: str, email: str) -> dict | None:
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
        result = (
            self.db.table(self.table)
            .select("user_id, expires_at, verified_at")
            .eq("token", token)
            .maybe_single()
            .execute()
        )
        return result.data if result else None

    def upsert_code(self, user_id: str, code: str, expires_at: str) -> None:
        self.db.table(self.table).upsert(
            {
                "user_id": user_id,
                "token": code,
                "expires_at": expires_at,
                "verified_at": None,
            }
        ).execute()

    def mark_as_verified(self, code: str, user_id: str) -> str:
        """Marca código como verificado e retorna token de uso único.

        Raises:
            RuntimeError: Se o código já foi verificado ou não existe
        """
        reset_token = secrets.token_urlsafe(32)

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

        if not result.data or len(result.data) == 0:
            raise RuntimeError("Código já foi verificado ou não existe")

        return reset_token

    def delete_by_token(self, token: str) -> None:
        self.db.table(self.table).delete().eq("token", token).execute()

    def is_code_valid(self, code_data: dict) -> bool:
        if not code_data:
            return False

        if code_data.get("verified_at"):
            return False

        expires_at = datetime.fromisoformat(code_data["expires_at"])
        return datetime.now(UTC) <= expires_at

    def is_token_valid(self, token_data: dict) -> bool:
        if not token_data:
            return False

        if not token_data.get("verified_at"):
            return False

        expires_at = datetime.fromisoformat(token_data["expires_at"])
        return datetime.now(UTC) <= expires_at
