"""
Job de manutenção do Iceberg.
Executa compaction e limpeza de snapshots antigos.
Deve ser executado periodicamente (ex: via cron diário).
"""

import sys

from pyspark.sql import SparkSession

from common.config import Settings
from cronjob.iceberg_writer import IcebergWriter


class IcebergMaintenanceJob:
    """
    Job para manutenção periódica das tabelas Iceberg.
    """

    def __init__(
        self,
        warehouse_path: str,
        database: str = "pncp_silver",
        table: str = "editais_enriched",
    ) -> None:
        """
        Inicializa o job de manutenção.

        Args:
            warehouse_path: Caminho do warehouse Iceberg.
            database: Nome do database.
            table: Nome da tabela.
        """
        self.warehouse_path = warehouse_path
        self.database = database
        self.table = table

        # Cria Spark session com extensões Iceberg
        self.spark = (
            SparkSession.builder.appName("Iceberg-Maintenance-Job")
            .config(
                "spark.jars.packages",
                "org.apache.iceberg:iceberg-spark-runtime-3.4_2.12:1.4.3",
            )
            .config(
                "spark.sql.extensions",
                "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
            )
            .getOrCreate()
        )

        self.iceberg_writer = IcebergWriter(
            spark=self.spark,
            warehouse_path=warehouse_path,
        )

    def run(self, expire_snapshots_days: int = 7) -> None:
        """
        Executa manutenção completa da tabela.

        Args:
            expire_snapshots_days: Dias de retenção de snapshots.
        """
        print(f"🔧 Iniciando manutenção Iceberg: {self.database}.{self.table}")

        # 1. Compaction (reescreve arquivos pequenos)
        print("📦 Executando compaction...")
        try:
            self.iceberg_writer.compact_table(
                database=self.database,
                table=self.table,
            )
            print("✅ Compaction concluído.")
        except Exception as e:
            print(f"❌ Erro no compaction: {e}")

        # 2. Expire snapshots antigos
        print(f"🗑️  Removendo snapshots anteriores a {expire_snapshots_days} dias...")
        try:
            self.iceberg_writer.expire_snapshots(
                database=self.database,
                table=self.table,
                older_than_days=expire_snapshots_days,
            )
            print("✅ Snapshots expirados.")
        except Exception as e:
            print(f"❌ Erro ao expirar snapshots: {e}")

        # 3. Mostra histórico atualizado
        print("📊 Histórico de snapshots:")
        try:
            history = self.iceberg_writer.get_table_history(
                database=self.database,
                table=self.table,
            )
            history.show(truncate=False)
        except Exception as e:
            print(f"❌ Erro ao buscar histórico: {e}")

        print("✅ Manutenção concluída!")
        self.spark.stop()


def main() -> None:
    """
    Entry point para execução via CLI ou scheduler.
    """
    warehouse = (
        sys.argv[1] if len(sys.argv) > 1 else Settings.ICEBERG_WAREHOUSE_PATH
    )
    retention_days = int(sys.argv[2]) if len(sys.argv) > 2 else 7

    job = IcebergMaintenanceJob(warehouse_path=warehouse)
    job.run(expire_snapshots_days=retention_days)


if __name__ == "__main__":
    main()
