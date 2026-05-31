"""
FastMCP server exposing MongoDB data from the PNCP pipeline as tools.
Run standalone with:  python src/chat/mcp_server.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastmcp import FastMCP
from pymongo import MongoClient

from src.config.settings import Settings

mcp = FastMCP("LicitaFácil — Dados PNCP")


def _collection(name: str):
    client = MongoClient(Settings.MONGO_URI, serverSelectionTimeoutMS=5_000)
    return client[Settings.MONGO_DATABASE][name]


@mcp.tool()
def query_licitacoes(limit: int = 10, filtro_objeto: str = "") -> list[dict]:
    """
    Consulta licitações da camada Bronze (dados brutos do PNCP).
    Retorna contratos com campos como objetoCompra, orgaoEntidade, valorTotalEstimado.
    """
    try:
        col = _collection(Settings.MONGO_COLLECTION)
        query = {}
        if filtro_objeto:
            query["objetoCompra"] = {"$regex": filtro_objeto, "$options": "i"}
        return list(col.find(query, {"_id": 0}).limit(limit))
    except Exception as e:
        return [{"erro": str(e)}]


@mcp.tool()
def query_editais_silver(limit: int = 10, categoria: str = "") -> list[dict]:
    """
    Consulta editais enriquecidos da camada Silver.
    Inclui categorias CNAE, resumos gerados pelo Gemini e metadados extras.
    """
    try:
        col = _collection(Settings.MONGO_SILVER_COLLECTION)
        query = {}
        if categoria:
            query["categorias_cnae.descricao"] = {"$regex": categoria, "$options": "i"}
        return list(col.find(query, {"_id": 0}).limit(limit))
    except Exception as e:
        return [{"erro": str(e)}]


@mcp.tool()
def get_estatisticas() -> dict:
    """
    Retorna estatísticas gerais dos dados: totais por camada e top-10 categorias CNAE.
    """
    try:
        bronze = _collection(Settings.MONGO_COLLECTION)
        silver = _collection(Settings.MONGO_SILVER_COLLECTION)
        pipeline = [
            {"$unwind": "$categorias_cnae"},
            {"$group": {"_id": "$categorias_cnae.descricao", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]
        top_cats = list(silver.aggregate(pipeline))
        return {
            "total_bronze": bronze.count_documents({}),
            "total_silver": silver.count_documents({}),
            "top_categorias": [
                {"categoria": c["_id"], "total": c["count"]} for c in top_cats
            ],
        }
    except Exception as e:
        return {"erro": str(e)}


@mcp.tool()
def buscar_por_orgao(nome_orgao: str, limit: int = 10) -> list[dict]:
    """
    Busca licitações pelo nome (parcial) do órgão público licitante.
    """
    try:
        col = _collection(Settings.MONGO_COLLECTION)
        query = {"orgaoEntidade.razaoSocial": {"$regex": nome_orgao, "$options": "i"}}
        return list(col.find(query, {"_id": 0}).limit(limit))
    except Exception as e:
        return [{"erro": str(e)}]


@mcp.tool()
def buscar_por_periodo(data_inicio: str, data_fim: str, limit: int = 20) -> list[dict]:
    """
    Busca licitações por período de encerramento de propostas.
    Datas no formato YYYY-MM-DD (ex: '2024-01-01').
    """
    try:
        col = _collection(Settings.MONGO_COLLECTION)
        query = {
            "dataEncerramentoPropostas": {"$gte": data_inicio, "$lte": data_fim}
        }
        return list(col.find(query, {"_id": 0}).limit(limit))
    except Exception as e:
        return [{"erro": str(e)}]


if __name__ == "__main__":
    mcp.run()
