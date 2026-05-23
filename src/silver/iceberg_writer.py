"""
Writer Apache Iceberg para camada Silver.
Persiste dados enriquecidos em formato otimizado para analytics.
"""
from pyspark.sql import SparkSession, DataFrame


class IcebergWriter:
    """
    Responsável por escrever dados no Apache Iceberg.
    """

    def __init__(
        self,
        spark: SparkSession,
        catalog_name: str = "iceberg_catalog",
        warehouse_path: str = "/tmp/iceberg-warehouse",
    ) -> None:
        """
        Inicializa o writer Iceberg.

        Args:
            spark: Sessão Spark configurada.
            catalog_name: Nome do catálogo Iceberg.
            warehouse_path: Caminho do warehouse Iceberg.
        """
        self.spark = spark
        self.catalog_name = catalog_name
        self.warehouse_path = warehouse_path

        # Configura Iceberg no Spark
        self._configure_iceberg()

    def _configure_iceberg(self) -> None:
        """
        Configura o catálogo Iceberg no Spark.
        """
        self.spark.conf.set(f"spark.sql.catalog.{self.catalog_name}", "org.apache.iceberg.spark.SparkCatalog")
        self.spark.conf.set(f"spark.sql.catalog.{self.catalog_name}.type", "hadoop")
        self.spark.conf.set(f"spark.sql.catalog.{self.catalog_name}.warehouse", self.warehouse_path)

    def create_table_if_not_exists(
        self,
        database: str,
        table: str,
    ) -> None:
        """
        Cria a tabela Iceberg se não existir.

        Args:
            database: Nome do database.
            table: Nome da tabela.
        """
        # Cria database se não existir
        self.spark.sql(f"CREATE DATABASE IF NOT EXISTS {self.catalog_name}.{database}")

        # Cria tabela se não existir
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.catalog_name}.{database}.{table} (
            numero_controle_pncp STRING,
            objeto_compra STRING,
            valor_total_estimado DOUBLE,
            modalidade_nome STRING,
            data_encerramento_proposta STRING,
            orgao_razao_social STRING,
            orgao_cnpj STRING,
            uf_sigla STRING,
            municipio_nome STRING,
            categorias_cnae ARRAY<STRUCT<codigo: STRING, descricao: STRING, confianca: DOUBLE>>,
            justificativa_categorizacao STRING,
            resumo_simplificado STRING,
            processamento_status STRING,
            processamento_timestamp TIMESTAMP
        )
        USING iceberg
        PARTITIONED BY (days(processamento_timestamp), uf_sigla)
        """
        self.spark.sql(create_table_sql)

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
            mode: Modo de escrita (append, overwrite, etc).
        """
        table_path = f"{self.catalog_name}.{database}.{table}"

        df.writeTo(table_path) \
            .using("iceberg") \
            .tableProperty("write.format.default", "parquet") \
            .tableProperty("write.parquet.compression-codec", "snappy") \
            .option("merge-schema", "true") \
            .createOrReplace() if mode == "overwrite" else df.writeTo(table_path).append()

    def write_stream(
        self,
        df: DataFrame,
        database: str,
        table: str,
        checkpoint_location: str,
    ):
        """
        Escreve um stream no Iceberg.

        Args:
            df: DataFrame de streaming.
            database: Nome do database.
            table: Nome da tabela.
            checkpoint_location: Diretório de checkpoint.

        Returns:
            StreamingQuery objeto.
        """
        table_path = f"{self.catalog_name}.{database}.{table}"

        return df.writeStream \
            .format("iceberg") \
            .outputMode("append") \
            .option("checkpointLocation", checkpoint_location) \
            .option("path", table_path) \
            .start()

    def compact_table(self, database: str, table: str) -> None:
        """
        Executa compaction na tabela Iceberg.

        Args:
            database: Nome do database.
            table: Nome da tabela.
        """
        table_path = f"{self.catalog_name}.{database}.{table}"

        # Reescreve arquivos pequenos em arquivos maiores
        self.spark.sql(f"CALL {self.catalog_name}.system.rewrite_data_files(table => '{table_path}')")

    def expire_snapshots(
        self,
        database: str,
        table: str,
        older_than_days: int = 7,
    ) -> None:
        """
        Remove snapshots antigos (data retention).

        Args:
            database: Nome do database.
            table: Nome da tabela.
            older_than_days: Dias de retenção.
        """
        table_path = f"{self.catalog_name}.{database}.{table}"

        self.spark.sql(f"""
            CALL {self.catalog_name}.system.expire_snapshots(
                table => '{table_path}',
                older_than => TIMESTAMP '{older_than_days} days'
            )
        """)

    def get_table_history(self, database: str, table: str) -> DataFrame:
        """
        Retorna o histórico de snapshots da tabela.

        Args:
            database: Nome do database.
            table: Nome da tabela.

        Returns:
            DataFrame com histórico.
        """
        table_path = f"{self.catalog_name}.{database}.{table}"
        return self.spark.sql(f"SELECT * FROM {table_path}.history")
