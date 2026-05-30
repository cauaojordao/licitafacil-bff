"""
Silver Layer - Spark Streaming Job
==================================
Consome mensagens do Kafka (Bronze), processa com IA (Gemini)
e persiste dados enriquecidos no PostgreSQL + Iceberg.
"""

from common.config import Settings
from spark_jobs.streaming_job import SilverStreamingJob


def main() -> None:
    """
    Executa o job Spark Streaming da camada Silver.
    """
    Settings.validate()

    job = SilverStreamingJob(
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

    job.run()


if __name__ == "__main__":
    main()
