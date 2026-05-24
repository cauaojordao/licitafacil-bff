"""
Job Spark Streaming da camada Silver.
Consome do Kafka, processa com IA e persiste no MongoDB + Iceberg.
"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, current_timestamp

from src.silver.edital_processor import EditalProcessor
from src.silver.iceberg_writer import IcebergWriter
from src.silver.kafka_consumer import KafkaSparkConsumer
from src.silver.silver_repository import SilverRepository


class SilverStreamingJob:
    """
    Job Spark Streaming para processamento da camada Silver.
    """

    def __init__(
        self,
        kafka_bootstrap_servers: str,
        kafka_topic: str,
        mongo_uri: str,
        mongo_database: str,
        mongo_collection: str,
        gemini_api_key: str,
        iceberg_warehouse: str,
        iceberg_database: str = "pncp_silver",
        iceberg_table: str = "editais_enriched",
        checkpoint_location: str = "/tmp/spark-checkpoint-silver",
    ) -> None:
        """
        Inicializa o job.

        Args:
            kafka_bootstrap_servers: Endereço do broker Kafka.
            kafka_topic: Tópico a ser consumido.
            mongo_uri: URI do MongoDB.
            mongo_database: Database do MongoDB.
            mongo_collection: Collection do MongoDB.
            gemini_api_key: Chave da API Gemini.
            checkpoint_location: Diretório para checkpoints do Spark.
        """
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.kafka_topic = kafka_topic
        self.mongo_uri = mongo_uri
        self.mongo_database = mongo_database
        self.mongo_collection = mongo_collection
        self.gemini_api_key = gemini_api_key
        self.iceberg_warehouse = iceberg_warehouse
        self.iceberg_database = iceberg_database
        self.iceberg_table = iceberg_table
        self.checkpoint_location = checkpoint_location

        # Inicializa Spark
        self.spark = self._create_spark_session()

        # Componentes
        self.consumer = KafkaSparkConsumer(
            spark=self.spark,
            kafka_bootstrap_servers=kafka_bootstrap_servers,
            topic=kafka_topic,
        )
        self.processor = EditalProcessor(gemini_api_key=gemini_api_key)
        self.repository = SilverRepository(
            uri=mongo_uri,
            database_name=mongo_database,
            collection_name=mongo_collection,
        )
        self.iceberg_writer = IcebergWriter(
            spark=self.spark,
            warehouse_path=iceberg_warehouse,
        )

    def _create_spark_session(self) -> SparkSession:
        """
        Cria a sessão Spark com configurações necessárias.

        Returns:
            Sessão Spark configurada.
        """
        return (
            SparkSession.builder.appName("PNCP-Silver-Streaming")
            .config(
                "spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
                "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.3",
            )
            .config("spark.sql.streaming.checkpointLocation", self.checkpoint_location)
            .config(
                "spark.sql.extensions",
                "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
            )
            .getOrCreate()
        )

    def _process_batch(self, batch_df: DataFrame, batch_id: int) -> None:
        """
        Processa um micro-batch do stream.

        Args:
            batch_df: DataFrame do batch.
            batch_id: ID do batch.
        """
        print(f"📦 Processando batch #{batch_id} com {batch_df.count()} registros...")

        # Coleta os dados (cuidado com volume!)
        rows = batch_df.collect()

        enriched_docs = []
        for row in rows:
            try:
                enriched = self.processor.process(row)
                enriched_docs.append(enriched)
            except Exception as e:
                print(f"❌ Erro ao processar {row.numero_controle_pncp}: {e}")

        if not enriched_docs:
            return

        # ── 1. Persiste no MongoDB (consultas operacionais) ────────────────
        self.repository.create_indexes()
        mongo_count = self.repository.upsert_many(enriched_docs)
        print(f"✅ Batch #{batch_id}: {mongo_count} documentos salvos no MongoDB.")

        # ── 2. Persiste no Iceberg (analytics) ─────────────────────────────
        try:
            # Converte para DataFrame
            enriched_df = self.spark.createDataFrame(enriched_docs)

            # Adiciona timestamp de processamento
            enriched_df = enriched_df.withColumn(
                "processamento_timestamp", current_timestamp()
            )

            # Flatten nested structures para Iceberg
            flattened_df = enriched_df.select(
                col("numero_controle_pncp"),
                col("objeto_compra"),
                col("valor_total_estimado"),
                col("modalidade_nome"),
                col("data_encerramento_proposta"),
                col("orgao_entidade.razao_social").alias("orgao_razao_social"),
                col("orgao_entidade.cnpj").alias("orgao_cnpj"),
                col("unidade_orgao.uf_sigla").alias("uf_sigla"),
                col("unidade_orgao.municipio_nome").alias("municipio_nome"),
                col("categorias_cnae"),
                col("justificativa_categorizacao"),
                col("resumo_simplificado"),
                col("processamento_status"),
                col("processamento_timestamp"),
            )

            # Escreve no Iceberg
            self.iceberg_writer.create_table_if_not_exists(
                database=self.iceberg_database,
                table=self.iceberg_table,
            )
            self.iceberg_writer.write_batch(
                df=flattened_df,
                database=self.iceberg_database,
                table=self.iceberg_table,
                mode="append",
            )
            print(f"🧊 Batch #{batch_id}: {len(enriched_docs)} registros salvos.")
        except Exception as e:
            print(f"❌ Erro ao escrever no Iceberg: {e}")

    def run(self) -> None:
        """
        Inicia o streaming job.
        """
        print("🚀 Iniciando Silver Streaming Job...")
        print(f"📥 Consumindo de: {self.kafka_topic}")
        print(f"💾 MongoDB: {self.mongo_database}.{self.mongo_collection}")
        print(f"🧊 Iceberg: {self.iceberg_database}.{self.iceberg_table}")

        # Setup do repositório
        self.repository.create_indexes()

        # Setup do Iceberg
        self.iceberg_writer.create_table_if_not_exists(
            database=self.iceberg_database,
            table=self.iceberg_table,
        )

        # Lê stream do Kafka
        stream_df = self.consumer.read_stream()

        # Processa e escreve
        query = (
            stream_df.writeStream.foreachBatch(self._process_batch)
            .outputMode("append")
            .start()
        )

        print("✅ Streaming ativo. Aguardando mensagens...")
        query.awaitTermination()
