"""
Serviço de manutenção do Apache Iceberg.
"""

from pyspark.sql import SparkSession

from repositories.iceberg_repository import IcebergRepository


class MaintenanceService:
    """
    Serviço responsável pela manutenção de tabelas Iceberg.
    """

    def __init__(self, warehouse_path: str):
        """
        Inicializa o serviço de manutenção.

        Args:
            warehouse_path: Caminho do warehouse Iceberg.
        """
        self.warehouse_path = warehouse_path
        self.spark = self._create_spark_session()
        self.iceberg_repository = IcebergRepository(self.spark, warehouse_path)

    def run_maintenance(
        self,
        database: str,
        table: str,
        expire_snapshots_days: int = 7,
        min_input_files: int = 2,
    ) -> dict[str, bool]:
        """
        Executa rotina completa de manutenção.

        Args:
            database: Nome do database.
            table: Nome da tabela.
            expire_snapshots_days: Dias para expirar snapshots.
            min_input_files: Mínimo de arquivos para compaction.

        Returns:
            Dicionário com status das operações.
        """
        print(f"🧹 Iniciando manutenção: {database}.{table}")

        results = {}

        # Compaction
        try:
            print("🗜️ Executando compaction...")
            self.iceberg_repository.compact_table(database, table, min_input_files)
            print("✅ Compaction concluída")
            results["compaction"] = True
        except Exception as e:
            print(f"❌ Erro na compaction: {e}")
            results["compaction"] = False

        # Expire snapshots
        try:
            print("🗑️ Removendo snapshots antigos...")
            self.iceberg_repository.expire_snapshots(database, table, expire_snapshots_days)
            print("✅ Snapshots antigos removidos")
            results["expire_snapshots"] = True
        except Exception as e:
            print(f"❌ Erro ao remover snapshots: {e}")
            results["expire_snapshots"] = False

        # Relatório
        self._generate_maintenance_report(database, table)

        return results

    def _generate_maintenance_report(self, database: str, table: str) -> None:
        """
        Gera relatório de manutenção.

        Args:
            database: Nome do database.
            table: Nome da tabela.
        """
        try:
            print("📊 Gerando relatório de manutenção...")

            # História da tabela
            history_df = self.iceberg_repository.get_table_history(database, table)
            snapshots_count = history_df.count()

            # Informações dos arquivos
            files_df = self.iceberg_repository.get_table_files(database, table)
            files_count = files_df.count()

            print(f"📈 Snapshots ativos: {snapshots_count}")
            print(f"📁 Arquivos de dados: {files_count}")

        except Exception as e:
            print(f"⚠️ Erro ao gerar relatório: {e}")

    def _create_spark_session(self) -> SparkSession:
        """
        Cria sessão Spark para manutenção.

        Returns:
            Sessão Spark configurada.
        """
        return (
            SparkSession.builder
            .appName("IcebergMaintenance")
            .config("processor.sql.extensions", "org.apache.iceberg.processor.extensions.IcebergSparkSessionExtensions")
            .getOrCreate()
        )

    def close(self) -> None:
        """
        Fecha a sessão Spark.
        """
        self.spark.stop()
