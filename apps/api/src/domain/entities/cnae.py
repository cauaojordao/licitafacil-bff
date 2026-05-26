"""Entidade de CNAE (Classificação Nacional de Atividades Econômicas)."""

from datetime import datetime

from pydantic import BaseModel


class CNAE(BaseModel):
    """Entidade representando um código CNAE."""

    id: str
    title: str
    created_at: datetime | None = None
