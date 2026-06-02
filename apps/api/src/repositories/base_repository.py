"""Repository base para operações CRUD reutilizáveis."""

from typing import Generic, TypeVar

from supabase import Client

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Repository base com operações CRUD genéricas."""

    def __init__(self, supabase: Client, table_name: str):
        self.supabase = supabase
        self.table_name = table_name

    def find_by_id(self, id: str) -> dict | None:
        response = (
            self.supabase.table(self.table_name)
            .select("*")
            .eq("id", id)
            .maybe_single()
            .execute()
        )
        return response.data if response.data else None

    def find_all(self, limit: int | None = None) -> list[dict]:
        query = self.supabase.table(self.table_name).select("*")

        if limit:
            query = query.limit(limit)

        response = query.execute()
        return response.data

    def create(self, data: dict) -> dict:
        response = self.supabase.table(self.table_name).insert(data).execute()

        if not response.data:
            raise RuntimeError(f"Failed to create {self.table_name} record")

        return response.data[0]

    def update(self, id: str, data: dict) -> dict:
        response = (
            self.supabase.table(self.table_name).update(data).eq("id", id).execute()
        )

        if not response.data:
            raise RuntimeError(f"Failed to update {self.table_name} record")

        return response.data[0]

    def delete(self, id: str) -> None:
        self.supabase.table(self.table_name).delete().eq("id", id).execute()

    def exists(self, field: str, value: str) -> bool:
        response = (
            self.supabase.table(self.table_name)
            .select("id")
            .eq(field, value)
            .maybe_single()
            .execute()
        )
        return response.data is not None
