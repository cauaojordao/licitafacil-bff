"""Gerenciamento de sessão de banco de dados."""

from functools import lru_cache

from supabase import Client, create_client

from src.core.config import settings


@lru_cache
def get_supabase() -> Client:
    """Retorna instância singleton do cliente Supabase (lru_cache)."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
