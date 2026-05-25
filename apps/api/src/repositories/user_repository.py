"""Repository para gerenciamento de usuários."""

from supabase import Client


class UserRepository:
    """Repository para operações de CRUD de usuários."""

    def __init__(self, db: Client):
        self.db = db
        self.table = "users"

    def find_by_email(self, email: str) -> dict | None:
        result = (
            self.db.table(self.table)
            .select("*")
            .eq("email", email)
            .maybe_single()
            .execute()
        )
        return result.data if result else None

    def find_by_id(self, user_id: str) -> dict | None:
        result = (
            self.db.table(self.table)
            .select("*")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        return result.data if result else None

    def create(self, name: str, email: str, password_hash: str) -> dict:
        result = (
            self.db.table(self.table)
            .insert(
                {
                    "name": name,
                    "email": email,
                    "password_hash": password_hash,
                }
            )
            .execute()
        )
        if not result or not result.data:
            raise RuntimeError("Failed to create user")
        return result.data[0]

    def update_password(self, user_id: str, password_hash: str) -> None:
        self.db.table(self.table).update({"password_hash": password_hash}).eq(
            "id", user_id
        ).execute()
