"""
Configurações específicas do Spark.
"""

from common.config import Settings as BaseSettings


class SparkSettings(BaseSettings):
    """
    Configurações específicas para os jobs Spark.
    Herda configurações globais e adiciona configurações específicas.
    """

    # Configurações específicas do Spark
    SPARK_APP_NAME: str = "LicitaFacil-Silver"
    SPARK_STREAMING_BATCH_DURATION: str = "30 seconds"
    SPARK_STREAMING_TRIGGER_ONCE: bool = False

    @classmethod
    def get_spark_config(cls) -> dict[str, str]:
        """
        Retorna configurações específicas para jobs Spark.
        """
        return {
            "kafka_bootstrap_servers": cls.KAFKA_BOOTSTRAP_SERVERS,
            "kafka_bronze_topic": cls.KAFKA_BRONZE_TOPIC,
            "supabase_url": cls.SUPABASE_URL,
            "supabase_key": cls.SUPABASE_KEY,
            "gemini_api_key": cls.GEMINI_API_KEY,
            "iceberg_warehouse": cls.ICEBERG_WAREHOUSE_PATH,
            "iceberg_database": cls.ICEBERG_DATABASE,
            "iceberg_table": cls.ICEBERG_TABLE,
            "checkpoint_location": cls.SPARK_CHECKPOINT_DIR,
            "app_name": cls.SPARK_APP_NAME,
            "batch_duration": cls.SPARK_STREAMING_BATCH_DURATION,
        }
