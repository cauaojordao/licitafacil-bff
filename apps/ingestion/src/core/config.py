"""
Configurações específicas do Consumer.
"""

from common.config import Settings as BaseSettings


class ConsumerSettings(BaseSettings):
    """
    Configurações específicas para o Consumer da camada Bronze.
    Herda configurações globais e adiciona configurações específicas.
    """

    # Configurações específicas do ingestion podem ser adicionadas aqui
    CONSUMER_BATCH_SIZE: int = 100
    CONSUMER_TIMEOUT_SECONDS: int = 30

    @classmethod
    def get_consumer_config(cls) -> dict[str, str]:
        """
        Retorna configurações específicas para o ingestion.
        """
        return {
            "pncp_base_url": cls.PNCP_BASE_URL,
            "mongo_uri": cls.MONGO_URI,
            "mongo_database": cls.MONGO_DATABASE,
            "mongo_collection": cls.MONGO_COLLECTION,
            "kafka_bootstrap_servers": cls.KAFKA_BOOTSTRAP_SERVERS,
            "kafka_bronze_topic": cls.KAFKA_BRONZE_TOPIC,
        }
