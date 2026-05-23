"""
Repositório de dados brutos da camada Bronze.
Responsável por persistir os dados brutos no MongoDB.
"""
from pymongo import MongoClient


class RawRepository:
    """
    Repositório para persistência de dados brutos na camada Bronze.
    """

    def __init__(self, uri: str, database_name: str, collection_name: str) -> None:
        """
        Inicializa a conexão com o MongoDB.

        Args:
            uri: String de conexão do MongoDB Atlas.
            database_name: Nome do banco de dados.
            collection_name: Nome da collection.
        """
        self.client = MongoClient(uri)
        self.database = self.client[database_name]
        self.collection = self.database[collection_name]

    def create_indexes(self) -> None:
        """
        Cria índice único para evitar duplicidade lógica.
        """
        self.collection.create_index("numero_controle_pncp", unique=True)

    def upsert_many(self, documents: list[dict]) -> int:
        """
        Insere ou atualiza documentos com base no numero_controle_pncp.

        Args:
            documents: Lista de documentos transformados.

        Returns:
            Quantidade de documentos processados.
        """
        if not documents:
            return 0

        processed = 0

        for document in documents:
            self.collection.update_one(
                {"numero_controle_pncp": document["numero_controle_pncp"]},
                {"$set": document},
                upsert=True
            )
            processed += 1

        return processed