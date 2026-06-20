"""
Bronze Layer Consumer - PNCP Data Ingestion
============================================
Extrai dados da API PNCP, persiste no MongoDB e publica no Kafka.
"""

import logging
import os

from core.config import ConsumerSettings
from services.ingestion_service import IngestionService
from services.transformation_service import TransformationService

from apps.ingestion.src.repositories.bronze_repository import BronzeRepository
from apps.ingestion.src.services.kafka_service import KafkaService
from libs.clients.pncp import PNCPClient

logger = logging.getLogger(__name__)


def main() -> None:
    """
    Executa o job de ingestão da camada Bronze.
    """
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    ConsumerSettings.validate()

    # Configurações
    config = ConsumerSettings.get_consumer_config()

    # Inicialização dos serviços
    pncp_client = PNCPClient(base_url=config["pncp_base_url"])
    transformation_service = TransformationService()

    bronze_repository = BronzeRepository(
        uri=config["mongo_uri"],
        database_name=config["mongo_database"],
        collection_name=config["mongo_collection"],
    )

    kafka_service = KafkaService(
        bootstrap_servers=config["kafka_bootstrap_servers"],
        topic=config["kafka_bronze_topic"],
    )

    # Serviço principal de ingestão
    ingestion_service = IngestionService(
        pncp_client=pncp_client,
        transformation_service=transformation_service,
        bronze_repository=bronze_repository,
        kafka_service=kafka_service,
    )

    # Execução
    result = ingestion_service.run_ingestion(
        endpoint="/v1/contratacoes/publicacao",
        params={
            "dataInicial": "20260401",
            "dataFinal": "20260406",
            "codigoModalidadeContratacao": 1,
        },
    )

    logger.info("Bronze Ingestion concluída com sucesso!")
    logger.info("Extraídos:           %s", result["raw_records_count"])
    logger.info("Transformados:       %s", result["transformed_records_count"])
    logger.info("Salvos no MongoDB:   %s", result["mongo_upserted_count"])
    logger.info("Publicados no Kafka: %s", result["kafka_published_count"])

    # Limpeza
    bronze_repository.close()
    kafka_service.close()


if __name__ == "__main__":
    main()
