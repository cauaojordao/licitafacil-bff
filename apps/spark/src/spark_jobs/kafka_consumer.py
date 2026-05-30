"""
Consumer Kafka para Spark Streaming.
Consome mensagens da camada Bronze.
"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import (
    DoubleType,
    StringType,
    StructField,
    StructType,
)


class KafkaSparkConsumer:
    """
    Consumer Kafka integrado com Spark Streaming.
    """

    def __init__(self, spark: SparkSession, kafka_bootstrap_servers: str, topic: str):
        """
        Inicializa o consumer.

        Args:
            spark: Sessão Spark ativa.
            kafka_bootstrap_servers: Endereço do broker Kafka.
            topic: Tópico a ser consumido.
        """
        self.spark = spark
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.topic = topic
        self.schema = self._define_schema()

    def _define_schema(self) -> StructType:
        """
        Define o schema dos dados consumidos do Kafka.

        Returns:
            StructType com o schema esperado.
        """
        return StructType(
            [
                StructField("numero_controle_pncp", StringType(), True),
                StructField("link_sistema_origem", StringType(), True),
                StructField("data_publicacao_pncp", StringType(), True),
                StructField("objeto_compra", StringType(), True),
                StructField("valor_total_estimado", DoubleType(), True),
                StructField("modalidade_id", StringType(), True),
                StructField("modalidade_nome", StringType(), True),
                StructField("situacao_compra_id", StringType(), True),
                StructField("situacao_compra_nome", StringType(), True),
                StructField(
                    "orgao_entidade",
                    StructType(
                        [
                            StructField("razao_social", StringType(), True),
                            StructField("cnpj", StringType(), True),
                        ]
                    ),
                    True,
                ),
                StructField(
                    "unidade_orgao",
                    StructType(
                        [
                            StructField("nome_unidade", StringType(), True),
                            StructField("uf_sigla", StringType(), True),
                            StructField("municipio_nome", StringType(), True),
                        ]
                    ),
                    True,
                ),
                StructField("data_abertura_proposta", StringType(), True),
                StructField("data_encerramento_proposta", StringType(), True),
                StructField("criterio_julgamento_id", StringType(), True),
                StructField("criterio_julgamento_nome", StringType(), True),
            ]
        )

    def read_stream(self) -> DataFrame:
        """
        Lê o stream do Kafka e retorna um DataFrame estruturado.

        Returns:
            DataFrame Spark com stream do Kafka.
        """
        raw_stream = (
            self.spark.readStream.format("kafka")
            .option("kafka.bootstrap.servers", self.kafka_bootstrap_servers)
            .option("subscribe", self.topic)
            .option("startingOffsets", "latest")
            .load()
        )

        # Parse JSON do Kafka
        parsed_stream = raw_stream.select(
            from_json(col("value").cast("string"), self.schema).alias("data")
        ).select("data.*")

        return parsed_stream
