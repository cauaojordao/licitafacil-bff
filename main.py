"""
Ponto de entrada legado (compatibilidade).
Recomenda-se usar run_bronze_ingestion.py para execuções completas.
"""

from src.bronze.ingestion_job import BronzeIngestionJob
from src.bronze.kafka_publisher import BronzeKafkaPublisher
from src.bronze.pncp_client import PNCPClient
from src.bronze.pncp_transformer import PNCPTransformer
from src.bronze.raw_repository import RawRepository
from src.config.settings import Settings


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
