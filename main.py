from src.config.settings import Settings
from src.extract.pncp_extractor import PNCPExtractor
from src.transform.pncp_transformer import PNCPTransformer
from src.load.mongodb_loader import MongoDBLoader
from src.pipeline.etl_pipeline import ETLPipeline


def main() -> None:
    """
    Função principal de execução do ETL.
    """
    Settings.validate()

    extractor = PNCPExtractor(base_url=Settings.PNCP_BASE_URL)
    transformer = PNCPTransformer()
    loader = MongoDBLoader(
        uri=Settings.MONGO_URI,
        database_name=Settings.MONGO_DATABASE,
        collection_name=Settings.MONGO_COLLECTION,
    )

    pipeline = ETLPipeline(
        extractor=extractor,
        transformer=transformer,
        loader=loader,
    )

    endpoint = "/v1/contratacoes/publicacao"

    params = {
        "dataInicial": "20260401",
        "dataFinal": "20260406",
        "codigoModalidadeContratacao": 1,
    }

    result = pipeline.run(endpoint=endpoint, params=params)

    print("ETL executado com sucesso.")
    print(f"Registros extraídos: {result['raw_records_count']}")
    print(f"Registros transformados: {result['transformed_records_count']}")

    if "processed_records_count" in result:
        print(f"Registros processados no MongoDB: {result['processed_records_count']}")


if __name__ == "__main__":
    main()