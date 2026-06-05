"""
Cronjob para manutenção do Data Lake
===================================
Executa tarefas de manutenção periódicas no Apache Iceberg.
"""

from core.config import CronjobSettings
from services.maintenance_service import MaintenanceService
from services.scheduler_service import SchedulerService


def run_maintenance() -> None:
    """
    Executa tarefa de manutenção do Iceberg.
    """
    print("🧹 Iniciando job de manutenção do Iceberg...")

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
        print("📊 Resultados da manutenção:")
        for operation, success in results.items():
            status = "✅ Sucesso" if success else "❌ Falha"
            print(f"   {operation}: {status}")

    except Exception as e:
        print(f"💥 Erro durante manutenção: {e}")
    finally:
        maintenance_service.close()


def main() -> None:
    """
    Função principal do maintenance.
    """
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
