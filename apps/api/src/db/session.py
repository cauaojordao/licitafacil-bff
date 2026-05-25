"""Gerenciamento de sessão de banco de dados."""

from functools import lru_cache

from supabase import Client, create_client

from src.core.config import settings


@lru_cache()
def get_supabase() -> Client:
    """
    Retorna uma instância singleton do cliente Supabase.

    O @lru_cache garante que o cliente seja criado apenas uma vez
    e reutilizado em todas as requisições.

    Returns:
        Cliente Supabase configurado

    Note:
        Esta função é uma dependência do FastAPI e pode ser
        injetada em rotas usando Depends(get_supabase)
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
