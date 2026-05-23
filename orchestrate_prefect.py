"""
Orquestrador Prefect — PNCP MEI Pipeline
=========================================
Executa o pipeline completo:
  1. Bronze Layer  → Extração API PNCP → MongoDB + Kafka
  2. Silver Layer  → Spark Streaming + Gemini AI → MongoDB + Iceberg

Uso:
    # Execução única
    python orchestrate_prefect.py

    # Com Prefect Server + agendamento
    ./run_prefect.sh
"""

from __future__ import annotations
import time
from datetime import date, timedelta
from threading import Thread

from prefect import flow, task, get_run_logger, serve

from src.bronze.pncp_transformer import PNCPTransformer
from src.config.settings import Settings
from src.bronze.pncp_client import PNCPClient
from src.bronze.raw_repository import RawRepository
from src.bronze.kafka_publisher import BronzeKafkaPublisher
from src.bronze.ingestion_job import BronzeIngestionJob
from src.silver.streaming_job import SilverStreamingJob


# ───────────────────────────────────────────────────────────────────────────
# Tasks
# ───────────────────────────────────────────────────────────────────────────

@task(name="Validar Configurações", retries=0)
def task_validate_settings() -> None:
    Settings.validate()
    get_run_logger().info("✅ Configurações validadas")


@task(name="Bronze Layer — Ingestão", retries=2, retry_delay_seconds=60)
def task_bronze_ingestion(data_inicial: str, data_final: str) -> dict:
    logger = get_run_logger()
    logger.info(f"📥 Extraindo contratações: {data_inicial} → {data_final}")

    job = BronzeIngestionJob(
        pncp_client=PNCPClient(base_url=Settings.PNCP_BASE_URL),
        transformer=PNCPTransformer(),
        raw_repository=RawRepository(
            uri=Settings.MONGO_URI,
            database_name=Settings.MONGO_DATABASE,
            collection_name=Settings.MONGO_COLLECTION,
        ),
        kafka_publisher=BronzeKafkaPublisher(
            bootstrap_servers=Settings.KAFKA_BOOTSTRAP_SERVERS,
            topic=Settings.KAFKA_BRONZE_TOPIC,
        ),
    )

    result = job.run(
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


@task(name="Silver Layer — Streaming + IA", timeout_seconds=3600)
def task_silver_streaming(duration_seconds: int = 600) -> dict:
    """Executa Spark Streaming processando mensagens Kafka por um período."""
    logger = get_run_logger()
    logger.info(f"🔄 Iniciando Silver Streaming ({duration_seconds}s)...")

    def run_streaming():
        job = SilverStreamingJob(
            kafka_bootstrap_servers=Settings.KAFKA_BOOTSTRAP_SERVERS,
            kafka_topic=Settings.KAFKA_BRONZE_TOPIC,
            mongo_uri=Settings.MONGO_URI,
            mongo_database=Settings.MONGO_DATABASE,
            mongo_collection=Settings.MONGO_SILVER_COLLECTION,
            gemini_api_key=Settings.GEMINI_API_KEY,
            iceberg_warehouse=Settings.ICEBERG_WAREHOUSE_PATH,
            iceberg_database=Settings.ICEBERG_DATABASE,
            iceberg_table=Settings.ICEBERG_TABLE,
            checkpoint_location=Settings.SPARK_CHECKPOINT_DIR,
        )
        job.run()

    # Rodar em thread daemon
    thread = Thread(target=run_streaming, daemon=True)
    thread.start()

    # Aguardar duração
    time.sleep(duration_seconds)

    logger.info(f"✅ Silver Streaming finalizado ({duration_seconds}s)")
    return {"duration_seconds": duration_seconds, "status": "completed"}


# ───────────────────────────────────────────────────────────────────────────
# Flow Principal
# ───────────────────────────────────────────────────────────────────────────

@flow(name="PNCP MEI Pipeline", log_prints=True)
def pncp_pipeline(
    data_inicial: str | None = None,
    data_final: str | None = None,
    run_silver: bool = True,
    silver_duration_seconds: int = 600,
) -> dict:
    """
    Pipeline completo PNCP MEI: Bronze + Silver.

    Args:
        data_inicial: Data inicial YYYYMMDD (padrão: ontem).
        data_final: Data final YYYYMMDD (padrão: hoje).
        run_silver: Executar Silver streaming (padrão: True).
        silver_duration_seconds: Duração Silver em segundos (padrão: 600).

    Returns:
        Resultados de cada camada.
    """
    # Definir datas
    hoje = date.today()
    if data_inicial is None:
        data_inicial = (hoje - timedelta(days=1)).strftime("%Y%m%d")
    if data_final is None:
        data_final = hoje.strftime("%Y%m%d")

    # Validar
    task_validate_settings()

    # Bronze
    bronze_result = task_bronze_ingestion(data_inicial, data_final)

    # Silver (opcional)
    silver_result = None
    if run_silver:
        silver_result = task_silver_streaming(silver_duration_seconds)

    return {
        "periodo": f"{data_inicial} → {data_final}",
        "bronze": bronze_result,
        "silver": silver_result,
    }


# ───────────────────────────────────────────────────────────────────────────
# Deployment (para Prefect Server)
# ───────────────────────────────────────────────────────────────────────────

def create_deployments():
    """Cria deployments com agendamento."""

    # Deployment diário completo
    pncp_pipeline.serve(
        name="pncp-pipeline-diario",
        cron="0 7 * * *",
        parameters={
            "run_silver": True,
            "silver_duration_seconds": 600,
        },
        tags=["production", "daily"],
        description="Pipeline completo diário (Bronze + Silver 10min)",
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        print("🚀 Iniciando Prefect Server com deployment...")
        create_deployments()
    else:
        print("▶️  Executando pipeline uma vez...")
        pncp_pipeline()
