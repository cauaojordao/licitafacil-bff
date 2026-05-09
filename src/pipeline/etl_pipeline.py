class ETLPipeline:
    """
    Classe responsável por orquestrar as etapas do ETL:
    extração, transformação e carga.
    """

    def __init__(self, extractor, transformer, loader=None) -> None:
        self.extractor = extractor
        self.transformer = transformer
        self.loader = loader

    def run(self, endpoint: str, params: dict) -> dict:
        raw_records = self.extractor.fetch_all(endpoint=endpoint, params=params)
        transformed_records = self.transformer.transform(records=raw_records)

        result = {
            "raw_records_count": len(raw_records),
            "transformed_records_count": len(transformed_records),
        }

        if self.loader:
            self.loader.create_indexes()
            processed_count = self.loader.upsert_many(transformed_records)
            result["processed_records_count"] = processed_count

        return result