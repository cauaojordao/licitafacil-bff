"""
Job de ingestão da camada Bronze.
Orquestra extração, transformação, persistência e publicação.
"""

from typing import Any

from clients.pncp import PNCPClient
from consumer.transformer import PNCPTransformer
from consumer.repository import RawRepository
from consumer.publisher import KafkaPublisher


class IngestionJob:
    """
    Job completo de ingestão da camada Bronze.
    """

    def __init__(
        self,
        pncp_client: PNCPClient,
        transformer: PNCPTransformer,
        raw_repository: RawRepository,
        kafka_publisher: KafkaPublisher,
    ) -> None:
        """
        Inicializa o job com todas as dependências.

        Args:
            pncp_client: Cliente para extração de dados do PNCP.
            transformer: Transformador de dados brutos.
            raw_repository: Repositório para persistir dados brutos.
            kafka_publisher: Publisher para enviar mensagens ao Kafka.
        """
        self.pncp_client = pncp_client
        self.transformer = transformer
        self.raw_repository = raw_repository
        self.kafka_publisher = kafka_publisher

    def run(self, endpoint: str, params: dict[str, Any]) -> dict[str, int]:
        """
        Executa o pipeline completo de ingestão.

        Args:
            endpoint: Endpoint da API do PNCP.
            params: Parâmetros de consulta.

        Returns:
            Dicionário com contadores do processamento.
        """
        # 1. Extrai dados brutos da API
        raw_records = self.pncp_client.fetch_all(endpoint=endpoint, params=params)

        # 2. Transforma os dados
        transformed_records = [
            self.transformer.transform(record) for record in raw_records
        ]

        # 3. Persiste no MongoDB
        self.raw_repository.create_indexes()
        mongo_upserted = self.raw_repository.upsert_many(transformed_records)

        # 4. Publica no Kafka
        kafka_published = self.kafka_publisher.publish_batch(transformed_records)
"""
Job de ingestão da camada Bronze.

Orquestra o fluxo completo:
  1. Extrai dados da API PNCP
  2. Transforma os registros brutos
  3. Persiste no MongoDB (raw store)
  4. Publica no Kafka para consumo downstream
"""

from typing import Any

from clients.pncp import PNCPClient
from consumer.publisher import KafkaPublisher
from consumer.transformer import PNCPTransformer
from consumer.repository import RawRepository


class IngestionJob:
    """
    Job da camada Bronze para ingestão completa de dados.
    """

    def __init__(
        self,
        pncp_client: PNCPClient,
        transformer: PNCPTransformer,
        raw_repository: RawRepository,
        kafka_publisher: KafkaPublisher,
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
"""
Job de ingestão da camada Bronze.

Orquestra o fluxo completo:
  1. Extrai dados da API PNCP
  2. Transforma os registros brutos
  3. Persiste no MongoDB (raw store)
  4. Publica no Kafka para consumo downstream
"""

from typing import Any

from clients.pncp import PNCPClient
from consumer.kafka_publisher import BronzeKafkaPublisher
from consumer.transformer import PNCPTransformer
from consumer.repository import RawRepository


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
        # ── 4. Publicação no Kafka ─────────────────────────────────────────
        kafka_count = self.kafka_publisher.publish(transformed_records)

        return {
            "raw_records_count": len(raw_records),
            "transformed_records_count": len(transformed_records),
            "mongo_upserted_count": mongo_count,
            "kafka_published_count": kafka_count,
        }
        return {
            "raw_records_count": len(raw_records),
            "transformed_records_count": len(transformed_records),
            "mongo_upserted_count": mongo_upserted,
            "kafka_published_count": kafka_published,
        }
