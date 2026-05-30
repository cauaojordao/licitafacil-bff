"""Repository para gerenciamento de usuários."""

from datetime import UTC, datetime

from supabase import Client

from src.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    """Repository para operações de CRUD de usuários."""

    def __init__(self, db: Client):
        super().__init__(db, "users")

    def find_by_email(self, email: str) -> dict | None:
        result = (
            self.supabase.table(self.table_name)
            .select("*")
            .eq("email", email)
            .maybe_single()
            .execute()
        )
        return result.data if result else None

    def find_by_cnpj(self, cnpj: str) -> dict | None:
        result = (
            self.supabase.table(self.table_name)
            .select("*")
            .eq("cnpj", cnpj)
            .maybe_single()
            .execute()
        )
        return result.data if result else None

    # find_by_id já está no BaseRepository, não precisa duplicar

    def create_user(self, name: str, email: str, password_hash: str) -> dict:
        """
        Cria um novo usuário (autenticação simples).

        Args:
            name: Nome do usuário
            email: E-mail do usuário
            password_hash: Hash da senha

        Returns:
            Dados do usuário criado
        """
        return self.create(
            {
                "name": name,
                "email": email,
                "password_hash": password_hash,
            }
        )

    def create_mei(
        self,
        name: str,
        email: str,
        password_hash: str,
        cnpj: str,
    ) -> dict:
        """
        Cria um novo usuário MEI (sem marcar como completo ainda).

        Args:
            name: Nome do usuário
            email: E-mail do usuário
            password_hash: Hash da senha
            cnpj: CNPJ alfanumérico do MEI (14 caracteres)

        Returns:
            Dados do usuário criado
        """
        return self.create(
            {
                "name": name,
                "email": email,
                "password_hash": password_hash,
                "cnpj": cnpj,
                "registration_complete": False,
            }
        )

    def link_interested_states(self, user_id: str, state_ids: list[str]) -> None:
        if not state_ids:
            return

        self.supabase.table("user_interested_states").delete().eq(
            "user_id", user_id
        ).execute()

        user_states = [
            {"user_id": user_id, "state_id": state_id} for state_id in state_ids
        ]
        self.supabase.table("user_interested_states").insert(user_states).execute()

    def get_interested_states(self, user_id: str) -> list[str]:
        result = (
            self.supabase.table("user_interested_states")
            .select("state_id")
            .eq("user_id", user_id)
            .execute()
        )
        return [item["state_id"] for item in result.data] if result.data else []

    def update_password(self, user_id: str, password_hash: str) -> None:
        """
        Atualiza a senha de um usuário.

        Args:
            user_id: ID do usuário
            password_hash: Novo hash da senha
        """
        self.update(user_id, {"password_hash": password_hash})

    def mark_registration_complete(self, user_id: str) -> None:
        """
        Marca o cadastro do usuário como completo.

        Args:
            user_id: ID do usuário
        """
        self.update(
            user_id,
            {
                "registration_complete": True,
                "onboarding_completed_at": datetime.now(UTC).isoformat(),
            },
        )

    def update_cnpj(
        self, user_id: str, cnpj: str, company_name: str | None = None
    ) -> dict:
        data: dict = {"cnpj": cnpj}
        if company_name is not None:
            data["company_name"] = company_name
        return self.update(user_id, data)
