import os
from dotenv import load_dotenv


load_dotenv()


class Settings:
    """
    Classe responsável por centralizar as configurações da aplicação.
    As variáveis são carregadas a partir do arquivo .env.
    """

    PNCP_BASE_URL = os.getenv("PNCP_BASE_URL", "")
    MONGO_URI = os.getenv("MONGO_URI", "")
    MONGO_DATABASE = os.getenv("MONGO_DATABASE", "")
    MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    # Configurações do Kafka
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_BRONZE_TOPIC = os.getenv("KAFKA_BRONZE_TOPIC", "bronze.pncp.contratacoes")

    # Configurações da camada Silver
    MONGO_SILVER_COLLECTION = os.getenv("MONGO_SILVER_COLLECTION", "editais_categorizados")
    SPARK_CHECKPOINT_DIR = os.getenv("SPARK_CHECKPOINT_DIR", "/tmp/spark-checkpoint-silver")

    # Configurações do Iceberg (Data Lake)
    ICEBERG_WAREHOUSE_PATH = os.getenv("ICEBERG_WAREHOUSE_PATH", "/tmp/iceberg-warehouse")
    ICEBERG_DATABASE = os.getenv("ICEBERG_DATABASE", "pncp_silver")
    ICEBERG_TABLE = os.getenv("ICEBERG_TABLE", "editais_enriched")

    @classmethod
    def validate(cls) -> None:
        """
        Valida se as configurações obrigatórias foram definidas.

        Raises:
            ValueError: Caso alguma configuração obrigatória esteja ausente.
        """
        required_fields = {
            "PNCP_BASE_URL": cls.PNCP_BASE_URL,
            "MONGO_URI": cls.MONGO_URI,
            "MONGO_DATABASE": cls.MONGO_DATABASE,
            "MONGO_COLLECTION": cls.MONGO_COLLECTION,
        }

        missing = [key for key, value in required_fields.items() if not value]

        if missing:
            raise ValueError(
                f"As seguintes variáveis de ambiente não foram definidas: {', '.join(missing)}"
            )