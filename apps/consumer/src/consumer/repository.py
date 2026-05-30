"""
Repositório de dados brutos da camada Bronze.
Persiste dados no MongoDB.
"""

from typing import Any

from pymongo import MongoClient


class RawRepository:
    """
    Repositório para persistência de dados brutos no MongoDB.
    """

    def __init__(self, uri: str, database_name: str, collection_name: str) -> None:
        """
        Inicializa a conexão com o MongoDB.

        Args:
            uri: String de conexão do MongoDB.
            database_name: Nome do banco de dados.
            collection_name: Nome da collection.
        """
        self.client: MongoClient = MongoClient(uri)
        self.database = self.client[database_name]
        self.collection = self.database[collection_name]

    def create_indexes(self) -> None:
        """
        Cria índices para otimizar consultas.
        """
        self.collection.create_index("numero_controle_pncp", unique=True)
        self.collection.create_index("data_publicacao_pncp")
        self.collection.create_index("orgao_entidade.cnpj")

    def upsert(self, document: dict[str, Any]) -> bool:
        """
        Insere ou atualiza um documento.

        Args:
            document: Documento a ser persistido.

        Returns:
            True se a operação foi bem-sucedida.
        """
        result = self.collection.update_one(
            {"numero_controle_pncp": document["numero_controle_pncp"]},
            {"$set": document},
            upsert=True,
        )
        return result.acknowledged

    def upsert_many(self, documents: list[dict[str, Any]]) -> int:
        """
        Insere ou atualiza múltiplos documentos.

        Args:
            documents: Lista de documentos.

        Returns:
            Quantidade de documentos processados.
        """
        if not documents:
            return 0
"""
Repositório de dados brutos da camada Bronze.
Persiste dados no MongoDB sem transformações complexas.
"""

from typing import Any

from pymongo import MongoClient


class RawRepository:
    """
    Repositório para persistência de dados brutos no MongoDB (camada Bronze).
    """

    def __init__(self, uri: str, database_name: str, collection_name: str) -> None:
        """
        Inicializa a conexão com o MongoDB.

        Args:
            uri: String de conexão do MongoDB.
            database_name: Nome do banco de dados.
            collection_name: Nome da collection.
        """
        self.client: MongoClient = MongoClient(uri)
        self.database = self.client[database_name]
        self.collection = self.database[collection_name]

    def create_indexes(self) -> None:
        """
        Cria índices para otimizar consultas.
        """
        self.collection.create_index("numero_controle_pncp", unique=True)
        self.collection.create_index("data_publicacao_pncp")
        self.collection.create_index("modalidade_id")

    def upsert(self, document: dict[str, Any]) -> bool:
        """
        Insere ou atualiza um documento.

        Args:
            document: Documento a ser persistido.

        Returns:
            True se a operação foi bem-sucedida.
        """
        result = self.collection.update_one(
            {"numero_controle_pncp": document["numero_controle_pncp"]},
            {"$set": document},
            upsert=True,
        )
        return result.acknowledged

    def upsert_many(self, documents: list[dict[str, Any]]) -> int:
        """
        Insere ou atualiza múltiplos documentos.

        Args:
            documents: Lista de documentos.

        Returns:
            Quantidade de documentos processados.
        """
        if not documents:
            return 0

        processed = 0
        for doc in documents:
            if self.upsert(doc):
                processed += 1

        return processed
        processed = 0
        for doc in documents:
            if self.upsert(doc):
                processed += 1

        return processed
