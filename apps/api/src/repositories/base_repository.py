"""Repository base para operações CRUD reutilizáveis."""

from typing import Generic, TypeVar

from supabase import Client

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Repository base com operações CRUD genéricas.

    Reduz duplicação de código entre repositories específicos.
    """

    def __init__(self, supabase: Client, table_name: str):
        """
        Inicializa o repository base.

        Args:
            supabase: Cliente Supabase
            table_name: Nome da tabela no banco
        """
        self.supabase = supabase
        self.table_name = table_name

    def find_by_id(self, id: str) -> dict | None:
        """Busca registro por ID."""
        response = (
            self.supabase.table(self.table_name)
            .select("*")
            .eq("id", id)
            .maybe_single()
            .execute()
        )
        return response.data if response.data else None

    def find_all(self, limit: int | None = None) -> list[dict]:
        """Retorna todos os registros."""
        query = self.supabase.table(self.table_name).select("*")

        if limit:
            query = query.limit(limit)

        response = query.execute()
        return response.data

    def create(self, data: dict) -> dict:
        """Cria um novo registro."""
        response = self.supabase.table(self.table_name).insert(data).execute()

        if not response.data:
            raise RuntimeError(f"Failed to create {self.table_name} record")

        return response.data[0]

    def update(self, id: str, data: dict) -> dict:
        """Atualiza um registro."""
        response = (
            self.supabase.table(self.table_name).update(data).eq("id", id).execute()
        )

        if not response.data:
            raise RuntimeError(f"Failed to update {self.table_name} record")

        return response.data[0]

    def delete(self, id: str) -> None:
        """Remove um registro."""
        self.supabase.table(self.table_name).delete().eq("id", id).execute()

    def exists(self, field: str, value: str) -> bool:
        """Verifica se existe registro com campo/valor específico."""
        response = (
            self.supabase.table(self.table_name)
            .select("id")
            .eq(field, value)
            .maybe_single()
            .execute()
        )
        return response.data is not None
