"""
Orquestrador Prefect — PNCP MEI Pipeline
=========================================
Executa os pipelines:
  1. Bronze  → Extração API PNCP → MongoDB + Kafka
  2. Silver  → Spark Streaming com IA → Supabase + Iceberg
  3. Full    → Bronze + Silver

Uso:
    # Pipeline completo
    python orchestrate_prefect.py

    # Apenas Bronze
    python orchestrate_prefect.py bronze

    # Apenas Silver
    python orchestrate_prefect.py silver

    # Com Prefect Server + deployments
    python orchestrate_prefect.py serve
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from typing import Any

from prefect import flow, get_run_logger, serve, task

from apps.ingestion.src.repositories.bronze_repository import BronzeRepository
from apps.ingestion.src.services.ingestion_service import IngestionService
from apps.ingestion.src.services.kafka_service import KafkaService
from apps.ingestion.src.services.transformation_service import TransformationService
from apps.processor.src.services.streaming_service import StreamingService
from libs.clients.pncp import PNCPClient
from libs.common.config import Settings


def _default_dates(
    data_inicial: str | None,
    data_final: str | None,
) -> tuple[str, str]:
    hoje = date.today()

    if data_inicial is None:
        data_inicial = (hoje - timedelta(days=1)).strftime("%Y%m%d")

    if data_final is None:
        data_final = hoje.strftime("%Y%m%d")

    return data_inicial, data_final


@task(name="Validar Configurações", retries=0)
def task_validate_settings() -> None:
    Settings.validate()
    get_run_logger().info("✅ Configurações validadas")


@task(name="Bronze Layer — Ingestão", retries=2, retry_delay_seconds=60)
def task_bronze_ingestion(data_inicial: str, data_final: str) -> dict[str, Any]:
    logger = get_run_logger()
    logger.info(f"📥 Extraindo contratações: {data_inicial} → {data_final}")

    pncp_client = PNCPClient(base_url=Settings.PNCP_BASE_URL)
    transformation_service = TransformationService()

    bronze_repository = BronzeRepository(
        uri=Settings.MONGO_URI,
        database_name=Settings.MONGO_DATABASE,
        collection_name=Settings.MONGO_COLLECTION,
    )

    kafka_service = KafkaService(
        bootstrap_servers=Settings.KAFKA_BOOTSTRAP_SERVERS,
        topic=Settings.KAFKA_BRONZE_TOPIC,
    )

    try:
        ingestion_service = IngestionService(
            pncp_client=pncp_client,
            transformation_service=transformation_service,
            bronze_repository=bronze_repository,
            kafka_service=kafka_service,
        )

        result = ingestion_service.run_ingestion(
            endpoint="/v1/contratacoes/publicacao",
            params={
                "dataInicial": data_inicial,
                "dataFinal": data_final,
                "codigoModalidadeContratacao": 1,
            },
        )

        logger.info(
            f"✅ Bronze concluída — "
            f"Extraídos: {result['raw_records_count']}, "
            f"MongoDB: {result['mongo_upserted_count']}, "
            f"Kafka: {result['kafka_published_count']}"
        )

        return result

    finally:
        bronze_repository.close()
        kafka_service.close()


@task(name="Silver Layer — Streaming + IA", timeout_seconds=3600)
def task_silver_streaming() -> dict[str, Any]:
    logger = get_run_logger()
    logger.info("🔄 Iniciando Silver Streaming...")

    streaming_service = StreamingService(
        kafka_bootstrap_servers=Settings.KAFKA_BOOTSTRAP_SERVERS,
        kafka_topic=Settings.KAFKA_BRONZE_TOPIC,
        supabase_url=Settings.SUPABASE_URL,
        supabase_key=Settings.SUPABASE_KEY,
        gemini_api_key=Settings.GEMINI_API_KEY,
        iceberg_warehouse=Settings.ICEBERG_WAREHOUSE_PATH,
        iceberg_database=Settings.ICEBERG_DATABASE,
        iceberg_table=Settings.ICEBERG_TABLE,
        checkpoint_location=Settings.SPARK_CHECKPOINT_DIR,
    )

    try:
        streaming_service.run_streaming()

        return {
            "status": "completed",
        }

    finally:
        streaming_service.close()


@flow(name="PNCP Bronze Pipeline", log_prints=True)
def bronze_pipeline(
    data_inicial: str | None = None,
    data_final: str | None = None,
) -> dict[str, Any]:
    data_inicial, data_final = _default_dates(data_inicial, data_final)

    task_validate_settings()
    bronze_result = task_bronze_ingestion(data_inicial, data_final)

    return {
        "periodo": f"{data_inicial} → {data_final}",
        "bronze": bronze_result,
    }


@flow(name="PNCP Silver Pipeline", log_prints=True)
def silver_pipeline() -> dict[str, Any]:
    task_validate_settings()
    silver_result = task_silver_streaming()

    return {
        "silver": silver_result,
    }


@flow(name="PNCP Full Pipeline", log_prints=True)
def full_pipeline(
    data_inicial: str | None = None,
    data_final: str | None = None,
    run_silver: bool = True,
) -> dict[str, Any]:
    data_inicial, data_final = _default_dates(data_inicial, data_final)

    task_validate_settings()

    bronze_result = task_bronze_ingestion(data_inicial, data_final)

    silver_result = None
    if run_silver:
        silver_result = task_silver_streaming()

    return {
        "periodo": f"{data_inicial} → {data_final}",
        "bronze": bronze_result,
        "silver": silver_result,
    }


def create_deployments() -> None:
    serve(
        bronze_pipeline.to_deployment(
            name="bronze-diario",
            cron="0 7 * * *",
            tags=["pncp", "bronze", "daily"],
            description="Bronze: PNCP → MongoDB + Kafka",
        ),
        silver_pipeline.to_deployment(
            name="silver-manual",
            tags=["pncp", "silver", "streaming"],
            description="Silver: Kafka → Supabase + Iceberg",
        ),
        full_pipeline.to_deployment(
            name="pipeline-completo-diario",
            cron="0 7 * * *",
            tags=["pncp", "bronze", "silver", "daily"],
            description="Pipeline completo: Bronze + Silver",
            parameters={
                "run_silver": True,
            },
        ),
    )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        print("🚀 Iniciando Prefect com deployments...")
        create_deployments()

    elif len(sys.argv) > 1 and sys.argv[1] == "bronze":
        print("▶️ Executando Bronze Pipeline...")
        bronze_pipeline()

    elif len(sys.argv) > 1 and sys.argv[1] == "silver":
        print("▶️ Executando Silver Pipeline...")
        silver_pipeline()

    else:
        print("▶️ Executando Full Pipeline...")
        full_pipeline()
