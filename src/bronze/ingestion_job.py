"""
Job de ingestão da camada Bronze.

Orquestra o fluxo completo:
  1. Extrai dados da API PNCP
  2. Transforma os registros brutos
  3. Persiste no MongoDB (raw store)
  4. Publica no Kafka para consumo downstream
"""

from typing import Any

from src.bronze.kafka_publisher import BronzeKafkaPublisher
from src.bronze.pncp_client import PNCPClient
from src.bronze.pncp_transformer import PNCPTransformer
from src.bronze.raw_repository import RawRepository


class BronzeIngestionJob:
    """
    Job da camada Bronze para ingestão completa de dados.
    """

    def __init__(
        self,
        pncp_client: PNCPClient,
        transformer: PNCPTransformer,
        raw_repository: RawRepository,
        kafka_publisher: BronzeKafkaPublisher,
    ) -> None:
        """
        Inicializa o job com todas as dependências necessárias.

        Args:
            pncp_client: Cliente para extração da API PNCP.
            transformer: Transformador de dados brutos.
            raw_repository: Repositório para persistência no MongoDB.
            kafka_publisher: Publisher para envio ao Kafka.
        """
        self.pncp_client = pncp_client
        self.transformer = transformer
        self.raw_repository = raw_repository
        self.kafka_publisher = kafka_publisher

    def run(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """
        Executa o pipeline completo da camada Bronze.

        Args:
            endpoint: Endpoint da API PNCP.
            params: Parâmetros da consulta.

        Returns:
            Dicionário com métricas de execução do pipeline.
        """
        # ── 1. Extração da API ─────────────────────────────────────────────
        raw_records = self.pncp_client.fetch_all(endpoint=endpoint, params=params)

        # ── 2. Transformação ───────────────────────────────────────────────
        transformed_records = self.transformer.transform(records=raw_records)

        # ── 3. Persistência no MongoDB ─────────────────────────────────────
        self.raw_repository.create_indexes()
        mongo_count = self.raw_repository.upsert_many(transformed_records)

        # ── 4. Publicação no Kafka ─────────────────────────────────────────
        kafka_count = self.kafka_publisher.publish(transformed_records)

        return {
            "raw_records_count": len(raw_records),
            "transformed_records_count": len(transformed_records),
            "mongo_upserted_count": mongo_count,
            "kafka_published_count": kafka_count,
        }
