"""
Silver Layer - Spark Streaming Job
==================================
Consome mensagens do Kafka (Bronze), processa com IA (Gemini)
e persiste dados enriquecidos no PostgreSQL + Iceberg.
"""

from core.config import SparkSettings
from services.streaming_service import StreamingService


def main() -> None:
    """
    Executa o job Spark Streaming da camada Silver.
    """
    SparkSettings.validate()

    config = SparkSettings.get_spark_config()

    streaming_service = StreamingService(
        kafka_bootstrap_servers=config["kafka_bootstrap_servers"],
        kafka_topic=config["kafka_bronze_topic"],
        supabase_url=config["supabase_url"],
        supabase_key=config["supabase_key"],
        gemini_api_key=config["gemini_api_key"],
        iceberg_warehouse=config["iceberg_warehouse"],
        iceberg_database=config["iceberg_database"],
        iceberg_table=config["iceberg_table"],
        checkpoint_location=config["checkpoint_location"],
    )

    try:
        streaming_service.run_streaming()
    except KeyboardInterrupt:
        print("🛑 Parando streaming...")
    finally:
        streaming_service.close()


if __name__ == "__main__":
    main()
