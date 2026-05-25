from functools import lru_cache

from supabase import Client, create_client

from src.core.config import settings


@lru_cache()
def get_supabase() -> Client:
    """
    Retorna uma instância singleton do cliente Supabase.

    O @lru_cache garante que o cliente seja criado apenas uma vez
    e reutilizado em todas as requisições.
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
