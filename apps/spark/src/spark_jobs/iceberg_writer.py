"""
Writer para Apache Iceberg.
Persiste dados enriquecidos no Data Lake.
"""

from pyspark.sql import DataFrame, SparkSession


class IcebergWriter:
    """
    Escreve dados no formato Apache Iceberg para analytics.
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
            "spark.sql.catalog.iceberg_catalog", "org.apache.iceberg.spark.SparkCatalog"
        )
        self.spark.conf.set(
            "spark.sql.catalog.iceberg_catalog.type", "hadoop"
        )
        self.spark.conf.set(
            "spark.sql.catalog.iceberg_catalog.warehouse", warehouse_path
        )

    def create_table_if_not_exists(self, database: str, table: str) -> None:
        """
        Cria database e tabela Iceberg se não existirem.

        Args:
            database: Nome do database.
            table: Nome da tabela.
        """
        # Cria database
        self.spark.sql(f"CREATE DATABASE IF NOT EXISTS iceberg_catalog.{database}")

        # Cria tabela (schema será inferido no primeiro write)
        try:
            self.spark.sql(f"DESCRIBE TABLE iceberg_catalog.{database}.{table}")
        except Exception:
            # Tabela não existe, será criada no primeiro write
            pass

    def write_batch(
        self, df: DataFrame, database: str, table: str, mode: str = "append"
    ) -> None:
        """
        Escreve um batch no Iceberg.

        Args:
            df: DataFrame a ser escrito.
            database: Nome do database.
            table: Nome da tabela.
            mode: Modo de escrita ('append', 'overwrite').
        """
        full_table_name = f"iceberg_catalog.{database}.{table}"

        df.writeTo(full_table_name).mode(mode).createOrReplace()
