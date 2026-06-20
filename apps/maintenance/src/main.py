"""
Cronjob para manutenção do Data Lake
===================================
Executa tarefas de manutenção periódicas no Apache Iceberg.
"""

import logging
import os

from core.config import CronjobSettings
from services.maintenance_service import MaintenanceService
from services.scheduler_service import SchedulerService

logger = logging.getLogger(__name__)


def run_maintenance() -> None:
    """
    Executa tarefa de manutenção do Iceberg.
    """
    logger.info("Iniciando job de manutenção do Iceberg...")

    config = CronjobSettings.get_maintenance_config()

    maintenance_service = MaintenanceService(
        warehouse_path=config["iceberg_warehouse"]
    )

    try:
        results = maintenance_service.run_maintenance(
            database=config["iceberg_database"],
            table=config["iceberg_table"],
            expire_snapshots_days=int(config["expire_snapshots_days"]),
        )

        # Log dos resultados
        logger.info("Resultados da manutenção:")
        for operation, success in results.items():
            status = "✅ Sucesso" if success else "❌ Falha"
            logger.info("   %s: %s", operation, status)

    except Exception as e:
        logger.error("Erro durante manutenção: %s", e)
    finally:
        maintenance_service.close()


def main() -> None:
    """
    Função principal do maintenance.
    """
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    CronjobSettings.validate()

    scheduler_service = SchedulerService()

    # Agenda a manutenção
    scheduler_service.schedule_maintenance(run_maintenance)

    # Opcional: executar uma vez no startup para teste
    # scheduler_service.run_once(run_maintenance)

    # Inicia o scheduler
    scheduler_service.run_scheduler()


if __name__ == "__main__":
    main()
