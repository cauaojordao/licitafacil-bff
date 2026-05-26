"""Repository para gerenciamento de usuários."""

from datetime import UTC, datetime

from supabase import Client


class UserRepository:
    """Repository para operações de CRUD de usuários."""

    def __init__(self, db: Client):
        """
        Inicializa o repository com a conexão do banco.

        Args:
            db: Cliente Supabase para acesso ao banco de dados
        """
        self.db = db
        self.table = "users"

    def find_by_email(self, email: str) -> dict | None:
        """
        Busca um usuário pelo e-mail.

        Args:
            email: E-mail do usuário

        Returns:
            Dados do usuário ou None se não encontrado
        """
        result = (
            self.db.table(self.table)
            .select("*")
            .eq("email", email)
            .maybe_single()
            .execute()
        )
        return result.data if result else None

    def find_by_cnpj(self, cnpj: str) -> dict | None:
        """
        Busca um usuário pelo CNPJ.

        Args:
            cnpj: CNPJ alfanumérico do usuário (14 caracteres)

        Returns:
            Dados do usuário ou None se não encontrado
        """
        result = (
            self.db.table(self.table)
            .select("*")
            .eq("cnpj", cnpj)
            .maybe_single()
            .execute()
        )
        return result.data if result else None

    def find_by_id(self, user_id: str) -> dict | None:
        """
        Busca um usuário pelo ID.

        Args:
            user_id: ID do usuário

        Returns:
            Dados do usuário ou None se não encontrado
        """
        result = (
            self.db.table(self.table)
            .select("*")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        return result.data if result else None

    def create(self, name: str, email: str, password_hash: str) -> dict:
        """
        Cria um novo usuário (autenticação simples).

        Args:
            name: Nome do usuário
            email: E-mail do usuário
            password_hash: Hash da senha

        Returns:
            Dados do usuário criado
        """
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
        result = (
            self.db.table(self.table)
            .insert(
                {
                    "name": name,
                    "email": email,
                    "password_hash": password_hash,
                    "cnpj": cnpj,
                    "registration_complete": False,
                }
            )
            .execute()
        )
        if not result or not result.data:
            raise RuntimeError("Failed to create MEI user")
        return result.data[0]

    def link_interested_states(self, user_id: str, state_ids: list[str]) -> None:
        """
        Associa estados de interesse a um usuário.

        Args:
            user_id: ID do usuário
            state_ids: Lista de IDs IBGE dos estados
        """
        if not state_ids:
            return

        # Remove associações antigas
        self.db.table("user_interested_states").delete().eq(
            "user_id", user_id
        ).execute()

        # Cria novas associações
        user_states = [
            {"user_id": user_id, "state_id": state_id} for state_id in state_ids
        ]

        self.db.table("user_interested_states").insert(user_states).execute()

    def get_interested_states(self, user_id: str) -> list[str]:
        """
        Busca estados de interesse de um usuário.

        Args:
            user_id: ID do usuário

        Returns:
            Lista de IDs IBGE dos estados
        """
        result = (
            self.db.table("user_interested_states")
            .select("state_id")
            .eq("user_id", user_id)
            .execute()
        )

        if not result.data:
            return []

        return [item["state_id"] for item in result.data]

    def update_password(self, user_id: str, password_hash: str) -> None:
        """
        Atualiza a senha de um usuário.

        Args:
            user_id: ID do usuário
            password_hash: Novo hash da senha
        """
        self.db.table(self.table).update({"password_hash": password_hash}).eq(
            "id", user_id
        ).execute()

    def mark_registration_complete(self, user_id: str) -> None:
        """
        Marca o cadastro do usuário como completo.

        Args:
            user_id: ID do usuário
        """
        self.db.table(self.table).update(
            {
                "registration_complete": True,
                "onboarding_completed_at": datetime.now(UTC).isoformat(),
            }
        ).eq("id", user_id).execute()
