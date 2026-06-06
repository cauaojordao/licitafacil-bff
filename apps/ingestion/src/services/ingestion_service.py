"""
Serviço de ingestão de dados da camada Bronze.
"""

from typing import Dict

from libs.clients.pncp import PNCPClient
from apps.ingestion.src.repositories.bronze_repository import BronzeRepository
from services.kafka_service import KafkaService
from services.transformation_service import TransformationService


class IngestionService:
    """
    Orquestra o processo de ingestão de dados da camada Bronze.
    """

    def __init__(
        self,
        pncp_client: PNCPClient,
        transformation_service: TransformationService,
        bronze_repository: BronzeRepository,
        kafka_service: KafkaService,
    ) -> None:
        """
        Inicializa o serviço de ingestão.

        Args:
            pncp_client: Cliente para API do PNCP.
            transformation_service: Serviço de transformação de dados.
            bronze_repository: Repository para persistência no MongoDB.
            kafka_service: Serviço para publicação no Kafka.
        """
        self.pncp_client = pncp_client
        self.transformation_service = transformation_service
        self.bronze_repository = bronze_repository
        self.kafka_service = kafka_service

    def run_ingestion(self, endpoint: str, params: dict) -> Dict[str, int]:
        """
        Executa o processo completo de ingestão.

        Args:
            endpoint: Endpoint da API PNCP.
            params: Parâmetros da consulta.

        Returns:
            Dicionário com métricas do processo.
        """
        print(f"🚀 Iniciando ingestão Bronze: {endpoint}")

        # Extração
        raw_data = self.pncp_client.fetch_all(endpoint=endpoint, params=params)
        raw_records_count = len(raw_data)
        print(f"📥 Extraídos {raw_records_count} registros")

        # Transformação
        transformed_data = self.transformation_service.transform_batch(raw_data)
        transformed_records_count = len(transformed_data)
        print(f"🔄 Transformados {transformed_records_count} registros")

        # Persistência no MongoDB
        mongo_upserted_count = self.bronze_repository.upsert_many(transformed_data)
        print(f"💾 Salvos no MongoDB: {mongo_upserted_count} registros")

        # Publicação no Kafka
        kafka_published_count = self.kafka_service.publish_batch(transformed_data)
        print(f"📤 Publicados no Kafka: {kafka_published_count} mensagens")

        return {
            "raw_records_count": raw_records_count,
            "transformed_records_count": transformed_records_count,
            "mongo_upserted_count": mongo_upserted_count,
            "kafka_published_count": kafka_published_count,
        }
