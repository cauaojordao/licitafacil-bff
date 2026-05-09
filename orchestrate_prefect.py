"""
Orquestrador Prefect — PNCP MEI Oportunidades
==============================================
Executa sequencialmente os 4 pipelines do projeto:
  1. ETL Contratações       — extrai e carrega dados da API PNCP no MongoDB
  2. Alertas de Prazo       — identifica licitações com encerramento próximo
  3. Comparação Temporal    — detecta novas oportunidades (hoje vs ontem)
  4. Categorização MEI      — classifica licitações por segmento via Gemini

Uso rápido:
    python orchestrate_prefect.py

Agendamento diário (Prefect serve):
    python -c "from orchestrate_prefect import pncp_orchestrator; \
               from prefect.schedules import CronSchedule; \
               pncp_orchestrator.serve(name='pncp-diario', \
                                       cron='0 7 * * *')"
"""

from __future__ import annotations

from datetime import date, timedelta

from prefect import flow, task, get_run_logger

from src.config.settings import Settings
from src.extract.pncp_extractor import PNCPExtractor
from src.transform.pncp_transformer import PNCPTransformer
from src.load.mongodb_loader import MongoDBLoader
from src.pipeline.etl_pipeline import ETLPipeline
from src.pipeline.deadline_alerts import DeadlineAlertsPipeline
from src.pipeline.temporal_comparison import TemporalComparisonPipeline
from src.pipeline.mei_categorization import MEICategorizationPipeline


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _build_loader() -> MongoDBLoader:
    return MongoDBLoader(
        uri=Settings.MONGO_URI,
        database_name=Settings.MONGO_DATABASE,
        collection_name=Settings.MONGO_COLLECTION,
    )


# ---------------------------------------------------------------------------
# Tasks — cada @task é uma unidade rastreável no Prefect UI
# ---------------------------------------------------------------------------

@task(name="Validar Configurações", retries=0)
def task_validate_settings() -> None:
    Settings.validate()
    get_run_logger().info("Configurações validadas com sucesso.")


@task(name="ETL Contratações", retries=2, retry_delay_seconds=60)
def task_etl_contratacoes(data_inicial: str, data_final: str) -> dict:
    logger = get_run_logger()
    logger.info(f"Extraindo contratações de {data_inicial} a {data_final}")

    pipeline = ETLPipeline(
        extractor=PNCPExtractor(base_url=Settings.PNCP_BASE_URL),
        transformer=PNCPTransformer(),
        loader=_build_loader(),
    )
    result = pipeline.run(
        endpoint="/v1/contratacoes/publicacao",
        params={
            "dataInicial": data_inicial,
            "dataFinal": data_final,
            "codigoModalidadeContratacao": 1,
        },
    )

    logger.info(
        f"ETL concluído — extraídos: {result['raw_records_count']}, "
        f"processados: {result.get('processed_records_count', 0)}"
    )
    return result


@task(name="Alertas de Prazo")
def task_deadline_alerts(dias_alerta: int = 7) -> dict:
    logger = get_run_logger()
    result = DeadlineAlertsPipeline(loader=_build_loader(), dias_alerta=dias_alerta).run()
    logger.info(f"Alertas encontrados: {result['total_alertas']}")
    return result


@task(name="Comparação Temporal")
def task_temporal_comparison() -> dict:
    logger = get_run_logger()
    result = TemporalComparisonPipeline(loader=_build_loader()).run()
    logger.info(
        f"Hoje: {result['total_hoje']} | Ontem: {result['total_ontem']} | "
        f"Novas: {result['novas_oportunidades']}"
    )
    return result


@task(name="Categorização MEI (Gemini)")
def task_mei_categorization(limit: int = 50) -> dict:
    logger = get_run_logger()
    result = MEICategorizationPipeline(
        loader=_build_loader(),
        gemini_api_key=Settings.GEMINI_API_KEY,
    ).run(limit=limit)
    logger.info(f"Categorizados: {result['categorizados']} | Erros: {result['erros']}")
    return result


# ---------------------------------------------------------------------------
# Flow principal — orquestra todos os pipelines
# ---------------------------------------------------------------------------

@flow(name="PNCP MEI — Orquestrador Principal", log_prints=True)
def pncp_orchestrator(
    data_inicial: str | None = None,
    data_final: str | None = None,
    dias_alerta: int = 7,
    categorization_limit: int = 50,
) -> dict:
    """
    Flow principal do projeto PNCP MEI.

    Args:
        data_inicial: Data inicial no formato YYYYMMDD (padrão: ontem).
        data_final: Data final no formato YYYYMMDD (padrão: hoje).
        dias_alerta: Janela em dias para alertas de prazo de encerramento.
        categorization_limit: Máximo de registros a categorizar por execução.

    Returns:
        Dicionário com o resultado consolidado de cada pipeline.
    """
    hoje = date.today()
    if data_inicial is None:
        data_inicial = (hoje - timedelta(days=1)).strftime("%Y%m%d")
    if data_final is None:
        data_final = hoje.strftime("%Y%m%d")

    # ── 1. Validação ───────────────────────────────────────────────────────
    task_validate_settings()

    # ── 2. ETL principal ───────────────────────────────────────────────────
    etl_result = task_etl_contratacoes(
        data_inicial=data_inicial,
        data_final=data_final,
    )

    # ── 3. Alertas de prazo ────────────────────────────────────────────────
    alerts_result = task_deadline_alerts(dias_alerta=dias_alerta)

    # ── 4. Comparação temporal ─────────────────────────────────────────────
    comparison_result = task_temporal_comparison()

    # ── 5. Categorização MEI com IA ────────────────────────────────────────
    categorization_result = task_mei_categorization(limit=categorization_limit)

    return {
        "periodo": f"{data_inicial} → {data_final}",
        "etl": etl_result,
        "alertas_prazo": alerts_result,
        "comparacao_temporal": comparison_result,
        "categorizacao_mei": categorization_result,
    }


if __name__ == "__main__":
    pncp_orchestrator()
