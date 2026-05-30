"""
Job Spark Streaming da camada Silver.
Consome do Kafka, processa com IA e persiste no PostgreSQL + Iceberg.
"""

from pyspark.sql import DataFrame, SparkSession
from spark_jobs.repository import SilverRepository

class SilverStreamingJob:
    """
    Job Spark Streaming para processamento da camada Silver.
    """

    def __init__(
        self,
        kafka_bootstrap_servers: str,
        kafka_topic: str,
        supabase_url: str,
        supabase_key: str,
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
            supabase_url: URL do projeto Supabase.
            supabase_key: Service key do Supabase.
            gemini_api_key: Chave da API Gemini.
            iceberg_warehouse: Caminho do warehouse Iceberg.
            iceberg_database: Database do Iceberg.
            iceberg_table: Tabela do Iceberg.
            checkpoint_location: Diretório para checkpoints do Spark.
        """
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.kafka_topic = kafka_topic
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.gemini_api_key = gemini_api_key
        self.iceberg_warehouse = iceberg_warehouse
        self.iceberg_database = iceberg_database
        self.iceberg_table = iceberg_table
        self.checkpoint_location = checkpoint_location

        # Inicializa Spark
        self.spark = self._create_spark_session()

        # Inicializa Supabase
        supabase: Client = create_client(supabase_url, supabase_key)

        # Componentes
        self.consumer = KafkaSparkConsumer(
            spark=self.spark,
            kafka_bootstrap_servers=kafka_bootstrap_servers,
            topic=kafka_topic,
        )
        self.processor = EditalProcessor(gemini_api_key=gemini_api_key)
        self.repository = SilverRepository(supabase=supabase)
        self.iceberg_writer = IcebergWriter(
            spark=self.spark,
            warehouse_path=iceberg_warehouse,
        )

    def _create_spark_session(self) -> SparkSession:
        """
        Cria a sessão Spark com configurações necessárias.
        Adiciona flags Java para compatibilidade com Java 11+.

        Returns:
            Sessão Spark configurada.
        """
        # Flags para compatibilidade com Java 11+
        java_options = (
            "--add-opens=java.base/java.lang=ALL-UNNAMED "
            "--add-opens=java.base/java.lang.invoke=ALL-UNNAMED "
            "--add-opens=java.base/java.lang.reflect=ALL-UNNAMED "
            "--add-opens=java.base/java.io=ALL-UNNAMED "
            "--add-opens=java.base/java.net=ALL-UNNAMED "
            "--add-opens=java.base/java.nio=ALL-UNNAMED "
            "--add-opens=java.base/java.util=ALL-UNNAMED "
            "--add-opens=java.base/java.util.concurrent=ALL-UNNAMED "
            "--add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED "
            "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED "
            "--add-opens=java.base/sun.nio.cs=ALL-UNNAMED "
            "--add-opens=java.base/sun.security.action=ALL-UNNAMED "
            "--add-opens=java.base/sun.util.calendar=ALL-UNNAMED "
        )

        return (
            SparkSession.builder.appName("PNCP-Silver-Streaming")
            .config(
                "spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,"
                "org.apache.iceberg:iceberg-spark-runtime-3.4_2.12:1.4.3",
            )
            .config("spark.sql.streaming.checkpointLocation", self.checkpoint_location)
            .config("spark.driver.extraJavaOptions", java_options)
            .config("spark.executor.extraJavaOptions", java_options)
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

        # ── 1. Persiste no PostgreSQL (consultas operacionais) ─────────────
        pg_count = self.repository.upsert_many(enriched_docs)
        print(f"✅ Batch #{batch_id}: {pg_count} registros salvos no PostgreSQL.")

        # ── 2. Persiste no Iceberg (analytics) ─────────────────────────────
        try:
            normalized_docs = []

            for doc in enriched_docs:
                normalized_docs.append({
                    "numero_controle_pncp": str(doc.get("numero_controle_pncp") or ""),
                    "objeto_compra": str(doc.get("objeto_compra") or ""),
                    "valor_total_estimado": float(doc.get("valor_total_estimado") or 0),
                    "modalidade_nome": str(doc.get("modalidade_nome") or ""),
                    "data_encerramento_proposta": str(doc.get("data_encerramento_proposta") or ""),
                    "orgao_entidade": doc.get("orgao_entidade") or {},
                    "unidade_orgao": doc.get("unidade_orgao") or {},
                    "categorias_cnae": doc.get("categorias_cnae") or [],
                    "justificativa_categorizacao": str(doc.get("justificativa_categorizacao") or ""),
                    "resumo_simplificado": str(doc.get("resumo_simplificado") or ""),
                    "processamento_status": str(doc.get("processamento_status") or "PROCESSADO"),
                })

            enriched_df = self.spark.createDataFrame(normalized_docs)

            enriched_df = enriched_df.withColumn(
                "processamento_timestamp", current_timestamp()
            )

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
            print(f"🧊 Batch #{batch_id}: {len(enriched_docs)} registros salvos no Iceberg.")
        except Exception as e:
            print(f"❌ Erro ao escrever no Iceberg: {e}")
"""
Job Spark Streaming da camada Silver.
Consome do Kafka, processa com IA e persiste no PostgreSQL + Iceberg.
"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, current_timestamp
from supabase import Client, create_client

from spark_jobs.edital_processor import EditalProcessor
from spark_jobs.iceberg_writer import IcebergWriter
from spark_jobs.kafka_consumer import KafkaSparkConsumer
from spark_jobs.silver_repository import SilverRepository


class SilverStreamingJob:
    """
    Job Spark Streaming para processamento da camada Silver.
    """

    def __init__(
        self,
        kafka_bootstrap_servers: str,
        kafka_topic: str,
        supabase_url: str,
        supabase_key: str,
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
            supabase_url: URL do projeto Supabase.
            supabase_key: Service key do Supabase.
            gemini_api_key: Chave da API Gemini.
            iceberg_warehouse: Caminho do warehouse Iceberg.
            iceberg_database: Database do Iceberg.
            iceberg_table: Tabela do Iceberg.
            checkpoint_location: Diretório para checkpoints do Spark.
        """
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.kafka_topic = kafka_topic
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.gemini_api_key = gemini_api_key
        self.iceberg_warehouse = iceberg_warehouse
        self.iceberg_database = iceberg_database
        self.iceberg_table = iceberg_table
        self.checkpoint_location = checkpoint_location

        # Inicializa Spark
        self.spark = self._create_spark_session()

        # Inicializa Supabase
        supabase: Client = create_client(supabase_url, supabase_key)

        # Componentes
        self.consumer = KafkaSparkConsumer(
            spark=self.spark,
            kafka_bootstrap_servers=kafka_bootstrap_servers,
            topic=kafka_topic,
        )
        self.processor = EditalProcessor(gemini_api_key=gemini_api_key)
        self.repository = SilverRepository(supabase=supabase)
        self.iceberg_writer = IcebergWriter(
            spark=self.spark,
            warehouse_path=iceberg_warehouse,
        )

    def _create_spark_session(self) -> SparkSession:
        """
        Cria a sessão Spark com configurações necessárias.
        Adiciona flags Java para compatibilidade com Java 11+.

        Returns:
            Sessão Spark configurada.
        """
        # Flags para compatibilidade com Java 11+
        java_options = (
            "--add-opens=java.base/java.lang=ALL-UNNAMED "
            "--add-opens=java.base/java.lang.invoke=ALL-UNNAMED "
            "--add-opens=java.base/java.lang.reflect=ALL-UNNAMED "
            "--add-opens=java.base/java.io=ALL-UNNAMED "
            "--add-opens=java.base/java.net=ALL-UNNAMED "
            "--add-opens=java.base/java.nio=ALL-UNNAMED "
            "--add-opens=java.base/java.util=ALL-UNNAMED "
            "--add-opens=java.base/java.util.concurrent=ALL-UNNAMED "
            "--add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED "
            "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED "
            "--add-opens=java.base/sun.nio.cs=ALL-UNNAMED "
            "--add-opens=java.base/sun.security.action=ALL-UNNAMED "
            "--add-opens=java.base/sun.util.calendar=ALL-UNNAMED "
        )

        return (
            SparkSession.builder.appName("PNCP-Silver-Streaming")
            .config(
                "spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,"
                "org.apache.iceberg:iceberg-spark-runtime-3.4_2.12:1.4.3",
            )
            .config("spark.sql.streaming.checkpointLocation", self.checkpoint_location)
            .config("spark.driver.extraJavaOptions", java_options)
            .config("spark.executor.extraJavaOptions", java_options)
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

        # ── 1. Persiste no PostgreSQL (consultas operacionais) ─────────────
        pg_count = self.repository.upsert_many(enriched_docs)
        print(f"✅ Batch #{batch_id}: {pg_count} registros salvos no PostgreSQL.")

        # ── 2. Persiste no Iceberg (analytics) ─────────────────────────────
        try:
            normalized_docs = []

            for doc in enriched_docs:
                normalized_docs.append(
                    {
                        "numero_controle_pncp": str(
                            doc.get("numero_controle_pncp") or ""
                        ),
                        "objeto_compra": str(doc.get("objeto_compra") or ""),
                        "valor_total_estimado": float(
                            doc.get("valor_total_estimado") or 0
                        ),
                        "modalidade_nome": str(doc.get("modalidade_nome") or ""),
                        "data_encerramento_proposta": str(
                            doc.get("data_encerramento_proposta") or ""
                        ),
                        "orgao_entidade": doc.get("orgao_entidade") or {},
                        "unidade_orgao": doc.get("unidade_orgao") or {},
                        "categorias_cnae": doc.get("categorias_cnae") or [],
                        "justificativa_categorizacao": str(
                            doc.get("justificativa_categorizacao") or ""
                        ),
                        "resumo_simplificado": str(
                            doc.get("resumo_simplificado") or ""
                        ),
                        "processamento_status": str(
                            doc.get("processamento_status") or "PROCESSADO"
                        ),
                    }
                )

            enriched_df = self.spark.createDataFrame(normalized_docs)

            enriched_df = enriched_df.withColumn(
                "processamento_timestamp", current_timestamp()
            )

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
            print(
                f"🧊 Batch #{batch_id}: {len(enriched_docs)} registros salvos no Iceberg."
            )
        except Exception as e:
            print(f"❌ Erro ao escrever no Iceberg: {e}")

    def run(self) -> None:
        """
        Inicia o streaming job.
        """
        print("🚀 Iniciando Silver Streaming Job...")
        print(f"📥 Consumindo de: {self.kafka_topic}")
        print("🐘 PostgreSQL: public.opportunities")
        print(f"🧊 Iceberg: {self.iceberg_database}.{self.iceberg_table}")

        # Setup do Iceberg
        self.iceberg_writer.create_table_if_not_exists(
            database=self.iceberg_database,
            table=self.iceberg_table,
        )

        stream_df = self.consumer.read_stream()

        query = (
            stream_df.writeStream.foreachBatch(self._process_batch)
            .outputMode("append")
            .start()
        )

        print("✅ Streaming ativo. Aguardando mensagens...")
        query.awaitTermination()
    def run(self) -> None:
        """
        Inicia o streaming job.
        """
        print("🚀 Iniciando Silver Streaming Job...")
        print(f"📥 Consumindo de: {self.kafka_topic}")
        print(f"🐘 PostgreSQL: public.opportunities")
        print(f"🧊 Iceberg: {self.iceberg_database}.{self.iceberg_table}")

        # Setup do Iceberg
        self.iceberg_writer.create_table_if_not_exists(
            database=self.iceberg_database,
            table=self.iceberg_table,
        )

        stream_df = self.consumer.read_stream()

        query = (
            stream_df.writeStream.foreachBatch(self._process_batch)
            .outputMode("append")
            .start()
        )

        print("✅ Streaming ativo. Aguardando mensagens...")
        query.awaitTermination()
