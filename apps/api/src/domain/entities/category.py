"""Entidade de Categoria de CNAEs."""

from datetime import datetime

from pydantic import BaseModel


class Category(BaseModel):
    """Categoria hierárquica para organização de CNAEs."""

    id: str
    name: str
    description: str | None = None
    parent_id: str | None = None
    slug: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
