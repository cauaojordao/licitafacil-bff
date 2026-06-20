"""Repository para gerenciamento de usuários."""

from datetime import datetime, timedelta, timezone
from typing import Any, cast

from supabase import Client

from src.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    """Repository para operações de CRUD de usuários."""

    def __init__(self, db: Client):
        super().__init__(db, "users")

    def find_by_email(self, email: str) -> dict[str, Any] | None:
        result = (
            self.supabase.table(self.table_name)
            .select("*")
            .eq("email", email)
            .maybe_single()
            .execute()
        )
        return cast(dict[str, Any] | None, result.data if result else None)

    def find_by_cnpj(self, cnpj: str) -> dict[str, Any] | None:
        result = (
            self.supabase.table(self.table_name)
            .select("*")
            .eq("cnpj", cnpj)
            .maybe_single()
            .execute()
        )
        return cast(dict[str, Any] | None, result.data if result else None)

    # find_by_id já está no BaseRepository, não precisa duplicar

    def create_user(self, name: str, email: str, password_hash: str) -> dict[str, Any]:
        """
        Cria um novo usuário (autenticação simples).

        Args:
            name: Nome do usuário
            email: E-mail do usuário
            password_hash: Hash da senha

        Returns:
            Dados do usuário criado
        """
        return cast(
            dict[str, Any],
            self.create(
                {
                    "name": name,
                    "email": email,
                    "password_hash": password_hash,
                }
            ),
        )

    def create_mei(
        self,
        name: str,
        email: str,
        password_hash: str,
        cnpj: str,
        company_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Cria um novo usuário MEI (sem marcar como completo ainda).

        Args:
            name: Nome do usuário
            email: E-mail do usuário
            password_hash: Hash da senha
            cnpj: CNPJ alfanumérico do MEI (14 caracteres)
            company_name: Razão social obtida da Receita Federal

        Returns:
            Dados do usuário criado
        """
        data: dict = {
            "name": name,
            "email": email,
            "password_hash": password_hash,
            "cnpj": cnpj,
            "registration_complete": False,
        }
        if company_name is not None:
            data["company_name"] = company_name
        return cast(dict[str, Any], self.create(data))

    def link_interested_states(self, user_id: str, state_ids: list[str]) -> None:
        if not state_ids:
            return

        # Deduplica para evitar violação de PK
        unique_state_ids = list(dict.fromkeys(state_ids))

        self.supabase.table("user_interested_states").delete().eq(
            "user_id", user_id
        ).execute()

        user_states = [
            {"user_id": user_id, "state_id": state_id} for state_id in unique_state_ids
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
                "onboarding_completed_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    def update_cnpj(
        self, user_id: str, cnpj: str, company_name: str | None = None
    ) -> dict[str, Any]:
        data: dict = {"cnpj": cnpj}
        if company_name is not None:
            data["company_name"] = company_name
        return cast(dict[str, Any], self.update(user_id, data))

    def update_profile(self, user_id: str, name: str | None = None) -> dict[str, Any]:
        """Atualiza campos do perfil do usuário."""
        data: dict = {}
        if name is not None:
            data["name"] = name
        if not data:
            user = self.find_by_id(user_id)
            if not user:
                raise RuntimeError("Usuário não encontrado")
            return cast(dict[str, Any], user)
        return cast(dict[str, Any], self.update(user_id, data))

    def anonymize_user(self, user_id: str) -> dict[str, Any]:
        """Anonimiza usuário substituindo dados pessoais por valores irreversíveis.

        Compliance LGPD Art. 18 - Direito de exclusão de dados pessoais.
        Mantém integridade de auditoria sem reter dados identificáveis.
        """
        import hashlib

        timestamp = datetime.now(timezone.utc).isoformat()
        hash_suffix = hashlib.sha256(f"{user_id}{timestamp}".encode()).hexdigest()[:8]

        anonymized_data = {
            "name": f"ANONIMIZADO_{hash_suffix}",
            "email": f"anonimizado_{hash_suffix}@licitafacil",
            "cnpj": None,
            "company_name": None,
            "password_hash": f"ANONYMIZED_{hash_suffix}",
            "anonymized_at": timestamp,
        }

        self.supabase.table("user_interested_states").delete().eq(
            "user_id", user_id
        ).execute()

        self.supabase.table("user_cnaes").delete().eq("user_id", user_id).execute()

        return cast(dict[str, Any], self.update(user_id, anonymized_data))

    def is_account_locked(self, user: dict) -> bool:
        """Verifica se a conta está bloqueada por excesso de tentativas."""
        if not user.get("locked_until"):
            return False
        locked_until = datetime.fromisoformat(user["locked_until"])
        return datetime.now(timezone.utc) < locked_until

    def increment_failed_attempts(self, user_id: str) -> dict[str, Any]:
        """Incrementa contador de tentativas falhadas e bloqueia após limite."""
        user = self.find_by_id(user_id)
        if not user:
            raise RuntimeError("Usuário não encontrado")

        failed_attempts = user.get("failed_login_attempts", 0) + 1
        data: dict = {"failed_login_attempts": failed_attempts}

        if failed_attempts >= 10:
            lock_duration_minutes = 5
            locked_until = (
                datetime.now(timezone.utc) + timedelta(minutes=lock_duration_minutes)
            ).isoformat()
            data["locked_until"] = locked_until

        return cast(dict[str, Any], self.update(user_id, data))

    def reset_failed_attempts(self, user_id: str) -> dict[str, Any]:
        """Reseta contador de tentativas falhadas após login bem-sucedido."""
        return cast(
            dict[str, Any],
            self.update(user_id, {"failed_login_attempts": 0, "locked_until": None}),
        )
