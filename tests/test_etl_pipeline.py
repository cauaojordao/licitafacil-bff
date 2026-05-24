"""
Testes unitários para ETLPipeline.
Usa mocks para isolar a lógica do pipeline sem dependências externas.
"""

from unittest.mock import MagicMock

import pytest

from src.pipeline.etl_pipeline import ETLPipeline


@pytest.fixture
def extractor():
    mock = MagicMock()
    mock.fetch_all.return_value = [
        {"id": 1, "title": "Licitação A"},
        {"id": 2, "title": "Licitação B"}
        ]
    return mock


@pytest.fixture
def transformer():
    mock = MagicMock()
    mock.transform.return_value = [
        {"id": 1, "title": "Licitação A", "transformed": True},
        {"id": 2, "title": "Licitação B", "transformed": True},
    ]
    return mock


@pytest.fixture
def loader():
    mock = MagicMock()
    mock.upsert_many.return_value = 2
    return mock


def test_pipeline_run_sem_loader_retorna_contagens_corretas(extractor, transformer):
    pipeline = ETLPipeline(extractor=extractor, transformer=transformer)

    result = pipeline.run(endpoint="/v1/contratacoes", params={"page": 1})

    assert result["raw_records_count"] == 2
    assert result["transformed_records_count"] == 2
    assert "processed_records_count" not in result


def test_pipeline_loader_retorna_contagem_processados(extractor, transformer, loader):
    pipeline = ETLPipeline(extractor=extractor, transformer=transformer, loader=loader)

    result = pipeline.run(endpoint="/v1/contratacoes", params={"page": 1})

    assert result["processed_records_count"] == 2
    loader.create_indexes.assert_called_once()
    loader.upsert_many.assert_called_once()


def test_pipeline_repassa_endpoint_e_params_ao_extractor(extractor, transformer):
    pipeline = ETLPipeline(extractor=extractor, transformer=transformer)
    params = {"dataInicial": "20260401", "codigoModalidadeContratacao": 1}

    pipeline.run(endpoint="/v1/contratacoes/publicacao", params=params)

    extractor.fetch_all.assert_called_once_with(
        endpoint="/v1/contratacoes/publicacao", params=params
    )


def test_pipeline_repassa_registros_brutos_ao_transformer(extractor, transformer):
    pipeline = ETLPipeline(extractor=extractor, transformer=transformer)

    pipeline.run(endpoint="/v1/contratacoes", params={})

    transformer.transform.assert_called_once_with(records=extractor.fetch_all.return_value)


def test_pipeline_run_com_lista_vazia(transformer):
    extractor = MagicMock()
    extractor.fetch_all.return_value = []
    transformer.transform.return_value = []

    pipeline = ETLPipeline(extractor=extractor, transformer=transformer)
    result = pipeline.run(endpoint="/v1/contratacoes", params={})

    assert result["raw_records_count"] == 0
    assert result["transformed_records_count"] == 0
