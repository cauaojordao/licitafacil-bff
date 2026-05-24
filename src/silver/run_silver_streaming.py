"""
Ponto de entrada — Camada Silver (Spark Streaming)
===================================================
Consome mensagens do Kafka (Bronze), processa com IA (Gemini)
e persiste dados enriquecidos no MongoDB + Iceberg.

Uso:
    python run_silver_streaming.py
"""

from src.config.settings import Settings
from src.silver.streaming_job import SilverStreamingJob


def main() -> None:
    """
    Executa o job Spark Streaming da camada Silver.
    """
    Settings.validate()

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


if __name__ == "__main__":
    main()
