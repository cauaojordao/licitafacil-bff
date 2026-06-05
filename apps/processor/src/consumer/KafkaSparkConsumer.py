"""
Consumer Kafka para Spark Streaming.
Consome mensagens da camada Bronze.
"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import (
    ArrayType,
    BooleanType,
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
        self.spark = spark
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.topic = topic
        self.schema = self._define_schema()

    def _define_schema(self) -> StructType:
        """
        Define o schema completo dos dados consumidos da camada Bronze.
        """
        return StructType(
            [
                StructField("numero_controle_pncp", StringType(), True),
                StructField("objeto_compra", StringType(), True),

                StructField("modalidade_nome", StringType(), True),
                StructField("modalidade_id", StringType(), True),

                StructField("situacao_compra_nome", StringType(), True),
                StructField("situacao_compra_id", StringType(), True),

                StructField("valor_total_estimado", DoubleType(), True),
                StructField("valor_total_homologado", DoubleType(), True),

                StructField("data_publicacao_pncp", StringType(), True),
                StructField("data_abertura_proposta", StringType(), True),
                StructField("data_encerramento_proposta", StringType(), True),
                StructField("data_atualizacao", StringType(), True),
                StructField("data_atualizacao_global", StringType(), True),
                StructField("data_inclusao", StringType(), True),

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

                StructField("link_sistema_origem", StringType(), True),
                StructField("link_processo_eletronico", StringType(), True),

                StructField("criterio_julgamento_nome", StringType(), True),

                StructField("informacao_complementar", StringType(), True),
                StructField("resumo_simplificado", StringType(), True),

                StructField(
                    "amparo_legal",
                    StructType(
                        [
                            StructField("codigo", StringType(), True),
                            StructField("nome", StringType(), True),
                            StructField("descricao", StringType(), True),
                        ]
                    ),
                    True,
                ),

                StructField("ano_compra", StringType(), True),
                StructField("numero_compra", StringType(), True),
                StructField("processo", StringType(), True),
                StructField("sequencial_compra", StringType(), True),

                StructField("modo_disputa_id", StringType(), True),
                StructField("modo_disputa_nome", StringType(), True),

                StructField("tipo_instrumento_convocatorio_codigo", StringType(), True),
                StructField("tipo_instrumento_convocatorio_nome", StringType(), True),

                StructField("srp", BooleanType(), True),
                StructField("usuario_nome", StringType(), True),

                StructField("fontes_orcamentarias", ArrayType(StringType()), True),

                StructField("processed_at", StringType(), True),
                StructField("source", StringType(), True),
            ]
        )

    def read_stream(self) -> DataFrame:
        """
        Lê o stream do Kafka e retorna DataFrame já estruturado.
        """
        raw_stream = (
            self.spark.readStream
            .format("kafka")
            .option("kafka.bootstrap.servers", self.kafka_bootstrap_servers)
            .option("subscribe", self.topic)
            .option("startingOffsets", "latest")
            .option("failOnDataLoss", "false")
            .load()
        )

        return (
            raw_stream
            .select(from_json(col("value").cast("string"), self.schema).alias("data"))
            .select("data.*")
        )