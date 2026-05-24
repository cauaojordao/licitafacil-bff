"""
Job de manutenção do Iceberg.
Executa compaction e limpeza de snapshots antigos.
"""
from pyspark.sql import SparkSession
from src.silver.iceberg_writer import IcebergWriter


class IcebergCompactionJob:
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
        Inicializa o job de compaction.

        Args:
            warehouse_path: Caminho do warehouse Iceberg.
            database: Nome do database.
            table: Nome da tabela.
        """
        self.warehouse_path = warehouse_path
        self.database = database
        self.table = table

        # Cria Spark session
        self.spark = SparkSession.builder \
            .appName("Iceberg-Compaction-Job") \
            .config("spark.jars.packages", "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.3") \
            .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
            .getOrCreate()

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
        self.iceberg_writer.compact_table(
            database=self.database,
            table=self.table,
        )
        print("✅ Compaction concluído.")

        # 2. Expire snapshots antigos
        print(f"🗑️  Removendo snapshots anteriores a {expire_snapshots_days} dias...")
        self.iceberg_writer.expire_snapshots(
            database=self.database,
            table=self.table,
            older_than_days=expire_snapshots_days,
        )
        print("✅ Snapshots expirados.")

        # 3. Mostra histórico atualizado
        print("📊 Histórico de snapshots:")
        history = self.iceberg_writer.get_table_history(
            database=self.database,
            table=self.table,
        )
        history.show(truncate=False)

        print("✅ Manutenção concluída com sucesso!")

        self.spark.stop()


if __name__ == "__main__":
    import sys

    warehouse = sys.argv[1] if len(sys.argv) > 1 else "/tmp/iceberg-warehouse"

    job = IcebergCompactionJob(warehouse_path=warehouse)
    job.run()
