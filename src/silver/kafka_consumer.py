"""
Consumer Kafka usando Spark Structured Streaming.
Consome mensagens da camada Bronze e retorna DataFrame Spark.
"""
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType, BooleanType


class KafkaSparkConsumer:
    """
    Consumer Kafka usando Spark Structured Streaming.
    """

    def __init__(
        self,
        spark: SparkSession,
        kafka_bootstrap_servers: str,
        topic: str,
    ) -> None:
        """
        Inicializa o consumer Spark.

        Args:
            spark: Sessão Spark ativa.
            kafka_bootstrap_servers: Endereço do broker Kafka.
            topic: Tópico a ser consumido.
        """
        self.spark = spark
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.topic = topic

    def _get_schema(self) -> StructType:
        """
        Define o schema dos dados vindos da Bronze.

        Returns:
            Schema Spark para parsing do JSON.
        """
        return StructType([
            StructField("numero_controle_pncp", StringType(), True),
            StructField("ano_compra", IntegerType(), True),
            StructField("sequencial_compra", IntegerType(), True),
            StructField("numero_compra", StringType(), True),
            StructField("processo", StringType(), True),
            StructField("objeto_compra", StringType(), True),
            StructField("valor_total_estimado", FloatType(), True),
            StructField("valor_total_homologado", FloatType(), True),
            StructField("modalidade_id", IntegerType(), True),
            StructField("modalidade_nome", StringType(), True),
            StructField("modo_disputa_id", IntegerType(), True),
            StructField("modo_disputa_nome", StringType(), True),
            StructField("situacao_compra_id", IntegerType(), True),
            StructField("situacao_compra_nome", StringType(), True),
            StructField("tipo_instrumento_codigo", IntegerType(), True),
            StructField("tipo_instrumento_nome", StringType(), True),
            StructField("data_inclusao", StringType(), True),
            StructField("data_publicacao_pncp", StringType(), True),
            StructField("data_atualizacao", StringType(), True),
            StructField("data_encerramento_proposta", StringType(), True),
            StructField("link_sistema_origem", StringType(), True),
            StructField("informacao_complementar", StringType(), True),
            StructField("srp", BooleanType(), True),
            StructField("orgao_entidade", StructType([
                StructField("cnpj", StringType(), True),
                StructField("razao_social", StringType(), True),
                StructField("poder_id", StringType(), True),
                StructField("esfera_id", StringType(), True),
            ]), True),
            StructField("unidade_orgao", StructType([
                StructField("uf_nome", StringType(), True),
                StructField("uf_sigla", StringType(), True),
                StructField("municipio_nome", StringType(), True),
                StructField("codigo_ibge", StringType(), True),
            ]), True),
        ])

    def read_stream(self) -> DataFrame:
        """
        Lê stream de mensagens do Kafka.

        Returns:
            DataFrame Spark com os dados parseados.
        """
        # Lê do Kafka
        kafka_df = self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.kafka_bootstrap_servers) \
            .option("subscribe", self.topic) \
            .option("startingOffsets", "earliest") \
            .load()

        # Parse do JSON
        schema = self._get_schema()
        parsed_df = kafka_df.select(
            from_json(col("value").cast("string"), schema).alias("data")
        ).select("data.*")

        return parsed_df

    def read_batch(self) -> DataFrame:
        """
        Lê dados do Kafka em modo batch (útil para testes).

        Returns:
            DataFrame Spark com os dados.
        """
        kafka_df = self.spark \
            .read \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.kafka_bootstrap_servers) \
            .option("subscribe", self.topic) \
            .option("startingOffsets", "earliest") \
            .option("endingOffsets", "latest") \
            .load()

        schema = self._get_schema()
        parsed_df = kafka_df.select(
            from_json(col("value").cast("string"), schema).alias("data")
        ).select("data.*")

        return parsed_df
