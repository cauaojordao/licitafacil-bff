"""
Repository para operações avançadas do Apache Iceberg.
"""

from datetime import datetime, timedelta

from pyspark.sql import DataFrame, SparkSession


class IcebergRepository:
    """
    Repository para operações de manutenção e consulta do Apache Iceberg.
    """

    def __init__(self, spark: SparkSession, warehouse_path: str):
        """
        Inicializa o repository Iceberg.

        Args:
            spark: Sessão Spark ativa.
            warehouse_path: Caminho do warehouse Iceberg.
        """
        self.spark = spark
        self.warehouse_path = warehouse_path
        self._configure_catalog()

    def _configure_catalog(self) -> None:
        """
        Configura o catálogo Iceberg no Spark.
        """
        self.spark.conf.set(
            "processor.sql.catalog.iceberg_catalog",
            "org.apache.iceberg.processor.SparkCatalog",
        )
        self.spark.conf.set("processor.sql.catalog.iceberg_catalog.type", "hadoop")
        self.spark.conf.set(
            "processor.sql.catalog.iceberg_catalog.warehouse", self.warehouse_path
        )

    def compact_table(
        self, database: str, table: str, min_input_files: int = 2
    ) -> None:
        """
        Executa compaction na tabela (reescreve arquivos pequenos).

        Args:
            database: Nome do database.
            table: Nome da tabela.
            min_input_files: Número mínimo de arquivos de entrada para compaction.
        """
        full_table_name = f"iceberg_catalog.{database}.{table}"

        self.spark.sql(
            f"""
            CALL iceberg_catalog.system.rewrite_data_files(
                table => '{full_table_name}',
                strategy => 'binpack',
                options => map('min-input-files', '{min_input_files}')
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
        older_than_timestamp = self._get_older_than_timestamp(older_than_days)

        self.spark.sql(
            f"""
            CALL iceberg_catalog.system.expire_snapshots(
                table => '{full_table_name}',
                older_than => TIMESTAMP '{older_than_timestamp}',
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
        return self.spark.sql(
            f"SELECT * FROM iceberg_catalog.{database}.{table}.history"
        )

    def get_table_snapshots(self, database: str, table: str) -> DataFrame:
        """
        Retorna informações sobre snapshots da tabela.

        Args:
            database: Nome do database.
            table: Nome da tabela.

        Returns:
            DataFrame com informações dos snapshots.
        """
        return self.spark.sql(
            f"SELECT * FROM iceberg_catalog.{database}.{table}.snapshots"
        )

    def get_table_files(self, database: str, table: str) -> DataFrame:
        """
        Retorna informações sobre arquivos da tabela.

        Args:
            database: Nome do database.
            table: Nome da tabela.

        Returns:
            DataFrame com informações dos arquivos.
        """
        return self.spark.sql(f"SELECT * FROM iceberg_catalog.{database}.{table}.files")

    def _get_older_than_timestamp(self, days: int) -> str:
        """
        Calcula timestamp de X dias atrás.

        Args:
            days: Número de dias.

        Returns:
            Timestamp formatado para SQL.
        """
        older_than = datetime.now() - timedelta(days=days)
        return older_than.strftime("%Y-%m-%d %H:%M:%S")
