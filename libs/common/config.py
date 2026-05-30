"""Configurações compartilhadas."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    Classe responsável por centralizar as configurações da aplicação.
    As variáveis são carregadas a partir do arquivo .env.
    """

    # API PNCP
    PNCP_BASE_URL = os.getenv("PNCP_BASE_URL", "https://pncp.gov.br/api/consulta")

    # MongoDB (Bronze)
    MONGO_URI = os.getenv("MONGO_URI", "")
    MONGO_DATABASE = os.getenv("MONGO_DATABASE", "pncp_db")
    MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "contratacoes")

    # Supabase (Silver)
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

    # Gemini AI
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_BRONZE_TOPIC = os.getenv("KAFKA_BRONZE_TOPIC", "bronze.pncp.contratacoes")

    # Spark
    SPARK_CHECKPOINT_DIR = os.getenv(
        "SPARK_CHECKPOINT_DIR", "/tmp/processor-checkpoint-silver"
    )

    # Iceberg
    ICEBERG_WAREHOUSE_PATH = os.getenv(
        "ICEBERG_WAREHOUSE_PATH", "/tmp/iceberg-warehouse"
    )
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
            "SUPABASE_URL": cls.SUPABASE_URL,
            "SUPABASE_KEY": cls.SUPABASE_KEY,
        }

        missing = [key for key, value in required_fields.items() if not value]

        if missing:
            raise ValueError(
                f"As seguintes variáveis de ambiente não foram definidas: {', '.join(missing)}"
            )
