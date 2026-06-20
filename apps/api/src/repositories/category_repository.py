"""Repository para operações com categorias de CNAEs."""

from supabase import Client

from src.domain.entities.category import Category


class CategoryRepository:
    """Repository para gerenciar categorias."""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def find_all(self) -> list[Category]:
        """Retorna todas as categorias."""
        response = self.supabase.table("categories").select("*").execute()
        return [Category(**row) for row in response.data]

    async def find_by_slug(self, slug: str) -> Category | None:
        """Busca categoria por slug."""
        response = (
            self.supabase.table("categories")
            .select("*")
            .eq("slug", slug)
            .maybe_single()
            .execute()
        )
        return Category(**response.data) if response.data else None

    async def find_by_parent_id(self, parent_id: str | None) -> list[Category]:
        """Retorna categorias filhas de uma categoria pai."""
        if parent_id is None:
            response = (
                self.supabase.table("categories")
                .select("*")
                .is_("parent_id", "null")
                .execute()
            )
        else:
            response = (
                self.supabase.table("categories")
                .select("*")
                .eq("parent_id", parent_id)
                .execute()
            )
        return [Category(**row) for row in response.data]

    async def create(
        self,
        name: str,
        slug: str,
        description: str | None = None,
        parent_id: str | None = None,
    ) -> Category:
        """Cria uma nova categoria."""
        response = (
            self.supabase.table("categories")
            .insert(
                {
                    "name": name,
                    "slug": slug,
                    "description": description,
                    "parent_id": parent_id,
                }
            )
            .execute()
        )
        return Category(**response.data[0])

    async def link_cnae_to_category(self, cnae_id: str, category_id: str) -> None:
        """Vincula um CNAE a uma categoria."""
        self.supabase.table("cnae_categories").insert(
            {"cnae_id": cnae_id, "category_id": category_id}
        ).execute()

    async def get_categories_by_cnae(self, cnae_id: str) -> list[Category]:
        """Retorna categorias vinculadas a um CNAE."""
        response = (
            self.supabase.table("cnae_categories")
            .select("categories(*)")
            .eq("cnae_id", cnae_id)
            .execute()
        )

        categories = []
        for row in response.data:
            if row.get("categories"):
                categories.append(Category(**row["categories"]))

        return categories
