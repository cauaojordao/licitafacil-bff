"""
Serviço de ingestão de dados da camada Bronze.
"""

import logging

from apps.ingestion.src.repositories.bronze_repository import BronzeRepository
from libs.clients.pncp import PNCPClient
from services.kafka_service import KafkaService
from services.transformation_service import TransformationService

logger = logging.getLogger(__name__)


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

    def run_ingestion(self, endpoint: str, params: dict) -> dict[str, int]:
        """
        Executa o processo completo de ingestão.

        Args:
            endpoint: Endpoint da API PNCP.
            params: Parâmetros da consulta.

        Returns:
            Dicionário com métricas do processo.
        """
        logger.info("Iniciando ingestão Bronze: %s", endpoint)

        # Extração
        raw_data = self.pncp_client.fetch_all(endpoint=endpoint, params=params)
        raw_records_count = len(raw_data)
        logger.info("Extraídos %s registros", raw_records_count)

        # Transformação
        transformed_data = self.transformation_service.transform_batch(raw_data)
        transformed_records_count = len(transformed_data)
        logger.info("Transformados %s registros", transformed_records_count)

        # Persistência no MongoDB
        mongo_upserted_count = self.bronze_repository.upsert_many(transformed_data)
        logger.info("Salvos no MongoDB: %s registros", mongo_upserted_count)

        # Publicação no Kafka
        kafka_published_count = self.kafka_service.publish_batch(transformed_data)
        logger.info("Publicados no Kafka: %s mensagens", kafka_published_count)

        return {
            "raw_records_count": raw_records_count,
            "transformed_records_count": transformed_records_count,
            "mongo_upserted_count": mongo_upserted_count,
            "kafka_published_count": kafka_published_count,
        }
