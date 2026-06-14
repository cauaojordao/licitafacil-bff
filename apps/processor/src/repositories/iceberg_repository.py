"""
Repository para Apache Iceberg.
Persiste dados enriquecidos no Data Lake.
"""

from pyspark.sql import DataFrame, SparkSession


class IcebergRepository:
    """
    Repository para operações com Apache Iceberg.
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
        Configura catálogo Iceberg.
        """
        self.spark.conf.set(
            "spark.sql.catalog.iceberg_catalog",
            "org.apache.iceberg.spark.SparkCatalog",
        )
        self.spark.conf.set(
            "spark.sql.catalog.iceberg_catalog.type",
            "hadoop",
        )
        self.spark.conf.set(
            "spark.sql.catalog.iceberg_catalog.warehouse",
            self.warehouse_path,
        )

    def create_database_if_not_exists(self, database: str) -> None:
        """
        Cria namespace/database se não existir.

        Args:
            database: Nome do database.
        """
        self.spark.sql(
            f"CREATE NAMESPACE IF NOT EXISTS iceberg_catalog.{database}"
        )

    def table_exists(self, database: str, table: str) -> bool:
        """
        Verifica se a tabela existe.

        Args:
            database: Nome do database.
            table: Nome da tabela.

        Returns:
            True se a tabela existe.
        """
        try:
            self.spark.sql(
                f"DESCRIBE TABLE iceberg_catalog.{database}.{table}"
            )
            return True
        except Exception:
            return False

    def write_batch(
        self,
        df: DataFrame,
        database: str,
        table: str,
        mode: str = "append",
    ) -> None:
        """
        Escreve um batch no Iceberg.

        Args:
            df: DataFrame a ser escrito.
            database: Nome do database.
            table: Nome da tabela.
            mode: append ou overwrite
        """
        full_table_name = f"iceberg_catalog.{database}.{table}"
        exists = self.table_exists(database, table)

        try:
            if mode == "overwrite":
                print(f"🧊 Overwrite Iceberg: {full_table_name}")
                if exists:
                    df.writeTo(full_table_name).replace()
                else:
                    df.writeTo(full_table_name).create()
            else:
                print(f"🧊 Append Iceberg: {full_table_name}")
                if exists:
                    df.writeTo(full_table_name).append()
                else:
                    df.writeTo(full_table_name).create()

            print(f"✅ Dados gravados com sucesso em {full_table_name}")

        except Exception as e:
            print(f"❌ Erro ao escrever no Iceberg: {e}")
            raise
