"""
Bronze Layer Consumer - PNCP Data Ingestion
============================================
Extrai dados da API PNCP, persiste no MongoDB e publica no Kafka.
"""

from common.config import Settings
from clients.pncp import PNCPClient
from consumer.transformer import PNCPTransformer
from consumer.repository import RawRepository
from consumer.kafka_publisher import BronzeKafkaPublisher
from consumer.ingestion_job import BronzeIngestionJob


def main() -> None:
    """
    Executa o job de ingestão da camada Bronze.
    """
    Settings.validate()

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
            "dataInicial": "20260401",
            "dataFinal": "20260406",
            "codigoModalidadeContratacao": 1,
        },
    )

    print("✅ Bronze Ingestion concluída com sucesso!")
    print(f"   📥 Extraídos:           {result['raw_records_count']}")
    print(f"   🔄 Transformados:       {result['transformed_records_count']}")
    print(f"   💾 Salvos no MongoDB:   {result['mongo_upserted_count']}")
    print(f"   📤 Publicados no Kafka: {result['kafka_published_count']}")


if __name__ == "__main__":
    main()
