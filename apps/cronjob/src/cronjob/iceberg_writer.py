"""
Writer Iceberg com operações de manutenção.
Estende funcionalidades para compaction e snapshot management.
"""

from pyspark.sql import DataFrame, SparkSession


class IcebergWriter:
    """
    Escreve dados no formato Apache Iceberg e gerencia manutenção.
    """

    def __init__(self, spark: SparkSession, warehouse_path: str):
        """
        Inicializa o writer Iceberg.

        Args:
            spark: Sessão Spark ativa.
            warehouse_path: Caminho do warehouse Iceberg.
        """
        self.spark = spark
        self.warehouse_path = warehouse_path

        # Configura catálogo Iceberg
        self.spark.conf.set(
            "spark.sql.catalog.iceberg_catalog",
            "org.apache.iceberg.spark.SparkCatalog",
        )
        self.spark.conf.set("spark.sql.catalog.iceberg_catalog.type", "hadoop")
        self.spark.conf.set(
            "spark.sql.catalog.iceberg_catalog.warehouse", warehouse_path
        )

    def compact_table(self, database: str, table: str) -> None:
        """
        Executa compaction na tabela (reescreve arquivos pequenos).

        Args:
            database: Nome do database.
            table: Nome da tabela.
        """
        full_table_name = f"iceberg_catalog.{database}.{table}"

        # Rewrite data files (compaction)
        self.spark.sql(
            f"""
            CALL iceberg_catalog.system.rewrite_data_files(
                table => '{full_table_name}',
                strategy => 'binpack',
                options => map('min-input-files', '2')
            )
        """
        )

    def expire_snapshots(
        self, database: str, table: str, older_than_days: int = 7
    ) -> None:
        """
        Remove snapshots antigos da tabela.

        Args:
            database: Nome do database.
            table: Nome da tabela.
            older_than_days: Remove snapshots mais antigos que X dias.
        """
        full_table_name = f"iceberg_catalog.{database}.{table}"

        self.spark.sql(
            f"""
            CALL iceberg_catalog.system.expire_snapshots(
                table => '{full_table_name}',
                older_than => TIMESTAMP '{self._get_older_than_timestamp(older_than_days)}',
                retain_last => 1
            )
        """
        )

    def get_table_history(self, database: str, table: str) -> DataFrame:
        """
        Retorna histórico de snapshots da tabela.

        Args:
            database: Nome do database.
            table: Nome da tabela.

        Returns:
            DataFrame com histórico de snapshots.
        """
        full_table_name = f"iceberg_catalog.{database}.{table}"

        return self.spark.sql(
            f"SELECT * FROM iceberg_catalog.{database}.{table}.history"
        )

    def _get_older_than_timestamp(self, days: int) -> str:
        """
        Calcula timestamp de X dias atrás.

        Args:
            days: Número de dias.

        Returns:
            Timestamp formatado para SQL.
        """
        from datetime import datetime, timedelta

        older_than = datetime.now() - timedelta(days=days)
        return older_than.strftime("%Y-%m-%d %H:%M:%S")
