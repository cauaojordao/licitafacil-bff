"""
Scheduler para jobs periódicos.
Alternativa ao cron usando Python schedule.
"""

import time

import schedule

from cronjob.iceberg_maintenance import IcebergMaintenanceJob
from common.config import Settings


def run_iceberg_maintenance() -> None:
    """
    Executa job de manutenção do Iceberg.
    """
    print("⏰ Iniciando job de manutenção do Iceberg...")
    job = IcebergMaintenanceJob(
        warehouse_path=Settings.ICEBERG_WAREHOUSE_PATH,
        database=Settings.ICEBERG_DATABASE,
        table=Settings.ICEBERG_TABLE,
    )
    job.run(expire_snapshots_days=7)


def main() -> None:
    """
    Inicia o scheduler.
    """
    print("🚀 Scheduler de cronjobs iniciado")

    # Agenda manutenção do Iceberg para rodar diariamente às 3h
    schedule.every().day.at("03:00").do(run_iceberg_maintenance)

    # Opcional: roda uma vez no startup
    # run_iceberg_maintenance()

    print("⏰ Próxima execução:", schedule.next_run())

    while True:
        schedule.run_pending()
        time.sleep(60)  # Checa a cada minuto


if __name__ == "__main__":
    main()
