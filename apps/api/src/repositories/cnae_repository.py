"""Repository para gerenciamento de CNAEs."""

from supabase import Client


class CNAERepository:
    """Repository para operações de CRUD de CNAEs."""

    def __init__(self, db: Client):
        """
        Inicializa o repository com a conexão do banco.

        Args:
            db: Cliente Supabase para acesso ao banco de dados
        """
        self.db = db
        self.table = "cnaes"

    def find_by_id(self, cnae_id: str) -> dict | None:
        """
        Busca um CNAE pelo código.

        Args:
            cnae_id: Código do CNAE

        Returns:
            Dados do CNAE ou None se não encontrado
        """
        result = (
            self.db.table(self.table)
            .select("*")
            .eq("id", cnae_id)
            .maybe_single()
            .execute()
        )
        return result.data

    def find_by_ids(self, cnae_ids: list[str]) -> list[dict]:
        """
        Busca múltiplos CNAEs pelos códigos.

        Args:
            cnae_ids: Lista de códigos CNAE

        Returns:
            Lista de CNAEs encontrados
        """
        if not cnae_ids:
            return []

        result = self.db.table(self.table).select("*").in_("id", cnae_ids).execute()
        return result.data or []

    def upsert(self, cnae_id: str, title: str) -> dict | None:
        """
        Cria ou atualiza um CNAE.

        Args:
            cnae_id: Código do CNAE
            title: Descrição da atividade

        Returns:
            Dados do CNAE criado/atualizado ou None se falhar
        """
        result = (
            self.db.table(self.table)
            .upsert(
                {
                    "id": cnae_id,
                    "title": title,
                }
            )
            .execute()
        )
        return result.data[0] if result.data else None

    def upsert_many(self, cnaes: list[dict]) -> list[dict]:
        """
        Cria ou atualiza múltiplos CNAEs.

        Args:
            cnaes: Lista de dicts com 'id' e 'title'

        Returns:
            Lista de CNAEs criados/atualizados
        """
        if not cnaes:
            return []

        result = self.db.table(self.table).upsert(cnaes).execute()
        return result.data or []

    def link_user_cnaes(self, user_id: str, cnae_ids: list[str]) -> None:
        """
        Associa CNAEs a um usuário.

        Args:
            user_id: ID do usuário
            cnae_ids: Lista de códigos CNAE
        """
        if not cnae_ids:
            return

        self.db.table("user_cnaes").delete().eq("user_id", user_id).execute()

        user_cnaes = [{"user_id": user_id, "cnae_id": cnae_id} for cnae_id in cnae_ids]

        self.db.table("user_cnaes").insert(user_cnaes).execute()

    def get_user_cnaes(self, user_id: str) -> list[dict]:
        """
        Busca CNAEs associados a um usuário.

        Args:
            user_id: ID do usuário

        Returns:
            Lista de CNAEs do usuário
        """
        result = (
            self.db.table("user_cnaes")
            .select("cnae_id, cnaes(id, title)")
            .eq("user_id", user_id)
            .execute()
        )

        if not result.data:
            return []

        return [
            {
                "id": item["cnaes"]["id"],
                "title": item["cnaes"]["title"],
            }
            for item in result.data
            if item.get("cnaes")
        ]
