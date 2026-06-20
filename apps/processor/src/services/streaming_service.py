"""
Serviço de processamento streaming da camada Silver.
"""
from datetime import datetime, date
import json
import logging
import os
import sys
from decimal import Decimal

from pyspark.sql import DataFrame, SparkSession
from supabase import create_client

from apps.api.src.repositories.cnae_repository import CNAERepository
from apps.processor.src.consumer.KafkaSparkConsumer import KafkaSparkConsumer
from apps.processor.src.repositories.iceberg_repository import IcebergRepository
from apps.processor.src.repositories.silver_repository import SilverRepository

from apps.processor.src.services.enrichment_service import EnrichmentService

logger = logging.getLogger(__name__)


def _normalize_for_spark(doc: dict) -> dict:
    """
    Normaliza documento para evitar erro de inferência de schema no Spark.
    Converte dict/list para JSON string e datas/decimals para tipos simples.
    """
    normalized = {}

    for key, value in doc.items():
        if isinstance(value, (dict, list)):
            normalized[key] = json.dumps(value, ensure_ascii=False)

        elif isinstance(value, (datetime, date)):
            normalized[key] = value.isoformat()

        elif isinstance(value, Decimal):
            normalized[key] = float(value)


        elif value is None:
            normalized[key] = ""

        else:
            normalized[key] = value

    return normalized


class StreamingService:
    """
    Serviço principal para processamento streaming da camada Silver.
    """

    def __init__(
        self,
        kafka_bootstrap_servers: str,
        kafka_topic: str,
        supabase_url: str,
        supabase_key: str,
        gemini_api_key: str,
        iceberg_warehouse: str,
        iceberg_database: str,
        iceberg_table: str,
        checkpoint_location: str,
    ):
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.kafka_topic = kafka_topic
        self.iceberg_warehouse = iceberg_warehouse
        self.iceberg_database = iceberg_database
        self.iceberg_table = iceberg_table
        self.checkpoint_location = checkpoint_location

        self.spark = self._create_spark_session()

        self.kafka_consumer = KafkaSparkConsumer(
            spark=self.spark,
            kafka_bootstrap_servers=self.kafka_bootstrap_servers,
            topic=self.kafka_topic,
        )

        self.supabase = create_client(supabase_url, supabase_key)
        self.cnae_repository = CNAERepository(self.supabase)
        self.silver_repository = SilverRepository(self.supabase)
        self.iceberg_repository = IcebergRepository(
            self.spark,
            iceberg_warehouse,
        )
        self.enrichment_service = EnrichmentService(
            gemini_api_key=gemini_api_key,
            cnae_repository=self.cnae_repository,
        )

    def run_streaming(self) -> None:
        logger.info("Iniciando Spark Streaming - Silver Layer")

        self.iceberg_repository.create_database_if_not_exists(
            self.iceberg_database
        )

        processed_df = self.kafka_consumer.read_stream()

        query = (
            processed_df.writeStream
            .foreachBatch(self._process_batch)
            .outputMode("append")
            .option(
                "checkpointLocation",
                self.checkpoint_location,
            )
            .trigger(availableNow=True)
            .start()
        )

        logger.info("Streaming iniciado. Processando mensagens disponíveis...")

        query.awaitTermination()

        logger.info("Silver Streaming finalizado")

    def _process_batch(self, df: DataFrame, batch_id: int) -> None:
        logger.info("Batch recebido: %s", batch_id)

        df.persist()

        count = df.count()

        logger.info(
            "Processando batch %s com %s registros",
            batch_id,
            count,
        )

        if count == 0:
            df.unpersist()
            return

        df.select(
            "numero_controle_pncp",
            "objeto_compra",
            "valor_total_estimado",
        ).show(5, truncate=False)

        documents = [row.asDict(recursive=True) for row in df.collect()]

        unique_docs = {
            doc["numero_controle_pncp"]: doc
            for doc in documents
        }.values()

        documents = list(unique_docs)

        logger.info("Após deduplicação: %s registros", len(documents))

        enriched_documents = self.enrichment_service.enrich_batch(documents)

        unique_docs = {
            doc["numero_controle_pncp"]: doc
            for doc in enriched_documents
        }.values()

        enriched_documents = list(unique_docs)

        enriched_documents = [
            self._add_analytics_fields(doc)
            for doc in enriched_documents
        ]

        postgres_count = self.silver_repository.upsert_many(enriched_documents)

        logger.info("Persistidos no PostgreSQL: %s registros", postgres_count)

        if enriched_documents:
            normalized_documents = [
                _normalize_for_spark(doc)
                for doc in enriched_documents
            ]

            iceberg_df = self.spark.createDataFrame(normalized_documents)

            self.iceberg_repository.write_batch(
                iceberg_df,
                self.iceberg_database,
                self.iceberg_table,
                mode="append",
            )

            logger.info(
                "Persistidos no Iceberg: %s registros",
                len(enriched_documents),
            )

    def _create_spark_session(self) -> SparkSession:
        os.environ["PYSPARK_PYTHON"] = sys.executable
        os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

        java_options = (
            "--add-opens=java.base/java.lang=ALL-UNNAMED "
            "--add-opens=java.base/java.lang.invoke=ALL-UNNAMED "
            "--add-opens=java.base/java.lang.reflect=ALL-UNNAMED "
            "--add-opens=java.base/java.io=ALL-UNNAMED "
            "--add-opens=java.base/java.net=ALL-UNNAMED "
            "--add-opens=java.base/java.nio=ALL-UNNAMED "
            "--add-opens=java.base/java.util=ALL-UNNAMED "
            "--add-opens=java.base/java.util.concurrent=ALL-UNNAMED "
            "--add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED "
            "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED "
            "--add-opens=java.base/sun.nio.cs=ALL-UNNAMED "
            "--add-opens=java.base/sun.security.action=ALL-UNNAMED "
            "--add-opens=java.base/sun.util.calendar=ALL-UNNAMED "
        )

        return (
            SparkSession.builder
            .appName("PNCP-Silver-Streaming")
            .config(
                "spark.jars.packages",
                ",".join([
                    "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2",
                    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1",
                ])
            )
            .config("spark.pyspark.python", sys.executable)
            .config("spark.pyspark.driver.python", sys.executable)
            .config("spark.sql.streaming.checkpointLocation", self.checkpoint_location)
            .config("spark.driver.extraJavaOptions", java_options)
            .config("spark.executor.extraJavaOptions", java_options)
            .getOrCreate()
        )

    def close(self) -> None:
        self.spark.stop()

    def _normalize_for_spark(self, doc):
        pass

    def _add_analytics_fields(self, doc: dict) -> dict:
        unidade = doc.get("unidade_orgao") or {}
        orgao = doc.get("orgao_entidade") or {}

        doc["uf"] = unidade.get("uf_sigla")
        doc["municipio"] = unidade.get("municipio_nome")
        doc["nome_unidade"] = unidade.get("nome_unidade")
        doc["orgao_razao_social"] = orgao.get("razao_social")
        doc["orgao_cnpj"] = orgao.get("cnpj")

        return doc