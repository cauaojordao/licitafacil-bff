"""
Transformações PySpark — PNCP Data Pipeline

  Bronze (MongoDB, dados brutos PNCP)   → DataFrame Spark tabular
  Silver (MongoDB, dados + Gemini CNAE) → análises por segmento MEI

"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType

_MONGO_CONNECTOR = "org.mongodb.spark:mongo-spark-connector_2.13:10.3.0"





def criar_sessao_spark(
    app_name: str = "LicitaFacil-Spark", mongo_uri: str = ""
) -> SparkSession:
    """Inicializa SparkSession local com o conector MongoDB."""
    builder = (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.jars.packages", _MONGO_CONNECTOR)
    )
    if mongo_uri:
        builder = builder.config("spark.mongodb.read.connection.uri", mongo_uri)
    return builder.getOrCreate()




def carregar_bronze(
    spark: SparkSession,
    uri: str,
    database: str,
    collection: str,
) -> DataFrame:
    """
    Carrega documentos brutos da camada Bronze (collection contratacoes).

    Schema relevante:
      numero_controle_pncp, objeto_compra, modalidade_nome,
      valor_total_estimado, valor_total_homologado,
      data_publicacao_pncp, data_encerramento_proposta, data_inclusao,
      orgao_entidade {cnpj, razao_social},
      unidade_orgao   {uf_sigla, uf_nome, municipio_nome, nome_unidade},
      amparo_legal    {nome}
    """
    return (
        spark.read.format("mongodb")
        .option("spark.mongodb.read.connection.uri", uri)
        .option("spark.mongodb.read.database", database)
        .option("spark.mongodb.read.collection", collection)
        .load()
    )




def normalizar_tipos(df: DataFrame) -> DataFrame:
    """
    Converte strings ISO-8601 para DateType e valores monetários para DoubleType.

    Padrão da Aula 07: withColumn + to_date + cast(DoubleType()).
    Os campos originais são substituídos pelas versões tipadas:
      data_publicacao_pncp      → data_publicacao   (DateType)
      data_encerramento_proposta → data_encerramento (DateType)
      data_inclusao             → data_inclusao      (DateType)
      valor_total_estimado      → valor_estimado     (DoubleType)
      valor_total_homologado    → valor_homologado   (DoubleType)
    """
    return (
        df.withColumn(
            "data_publicacao",
            F.to_date(F.col("data_publicacao_pncp"), "yyyy-MM-dd'T'HH:mm:ss"),
        )
        .withColumn(
            "data_encerramento",
            F.to_date(F.col("data_encerramento_proposta"), "yyyy-MM-dd'T'HH:mm:ss"),
        )
        .withColumn(
            "data_inclusao", F.to_date(F.col("data_inclusao"), "yyyy-MM-dd'T'HH:mm:ss")
        )
        .withColumn(
            "valor_estimado",
            F.round(F.col("valor_total_estimado").cast(DoubleType()), 2),
        )
        .withColumn(
            "valor_homologado",
            F.round(F.col("valor_total_homologado").cast(DoubleType()), 2),
        )
        .drop(
            "data_publicacao_pncp",
            "data_encerramento_proposta",
            "valor_total_estimado",
            "valor_total_homologado",
        )
    )



def flatten_campos_aninhados(df: DataFrame) -> DataFrame:
    """
    Achata os subdocumentos MongoDB em colunas planas.

    Este é o núcleo da atividade: transformar o JSON semi-estruturado do MongoDB
    em um DataFrame 100% tabular, pronto para análise, exportação ou Spark SQL.

    orgao_entidade  → cnpj_orgao, razao_social
    unidade_orgao   → uf_sigla, uf_nome, municipio, nome_unidade
    amparo_legal    → amparo_legal_nome
    """
    return (
        df.withColumn("cnpj_orgao", F.col("orgao_entidade.cnpj"))
        .withColumn("razao_social", F.col("orgao_entidade.razao_social"))
        .withColumn("uf_sigla", F.col("unidade_orgao.uf_sigla"))
        .withColumn("uf_nome", F.col("unidade_orgao.uf_nome"))
        .withColumn("municipio", F.col("unidade_orgao.municipio_nome"))
        .withColumn("nome_unidade", F.col("unidade_orgao.nome_unidade"))
        .withColumn("amparo_legal_nome", F.col("amparo_legal.nome"))
        .drop("orgao_entidade", "unidade_orgao", "amparo_legal")
    )



def agregar_por_modalidade(df: DataFrame) -> DataFrame:
    """
    Total de contratos, soma e média de valores por modalidade de licitação.

    Aplica após normalizar_tipos + flatten_campos_aninhados.
    Padrão groupBy + agg do Spark, equivalente a GROUP BY no SQL.
    """
    return (
        df.groupBy("modalidade_nome")
        .agg(
            F.count("numero_controle_pncp").alias("total_contratos"),
            F.round(F.sum("valor_estimado"), 2).alias("valor_total"),
            F.round(F.avg("valor_estimado"), 2).alias("valor_medio"),
        )
        .orderBy(F.col("total_contratos").desc())
    )



def agregar_por_estado(df: DataFrame) -> DataFrame:
    """
    Concentração de licitações por UF.

    Útil para MEIs identificarem em quais regiões estão as melhores oportunidades.
    Aplica após normalizar_tipos + flatten_campos_aninhados (usa coluna uf_sigla plana).
    """
    return (
        df.groupBy("uf_sigla")
        .agg(
            F.count("*").alias("total_licitacoes"),
            F.round(F.sum("valor_estimado"), 2).alias("valor_total"),
        )
        .orderBy(F.col("total_licitacoes").desc())
    )



def filtrar_licitacoes_abertas(df: DataFrame) -> DataFrame:
    """
    Retorna licitações cujo prazo de encerramento ainda não venceu.

    Equivalente distribuído do deadline_alerts.py — mesma lógica de data,
    mas com capacidade de processamento massivo via Spark.
    Aplica após normalizar_tipos + flatten_campos_aninhados.
    """
    return (
        df.filter(F.col("data_encerramento") >= F.current_date())
        .select(
            "numero_controle_pncp",
            "objeto_compra",
            "modalidade_nome",
            "data_encerramento",
            "valor_estimado",
            "uf_sigla",
            "municipio",
        )
        .orderBy("data_encerramento")
    )




def top10_modalidades_sql(spark: SparkSession, df: DataFrame) -> DataFrame:
    """
    Registra o DataFrame como view temporária e executa SQL padrão.

    O Spark SQL suporta as mesmas fontes que o conector (MongoDB, S3, Parquet,
    Iceberg), permitindo que analistas usem SQL familiar sem abrir mão do
    processamento distribuído.
    Aplica após normalizar_tipos + flatten_campos_aninhados.
    """
    df.createOrReplaceTempView("contratacoes")
    return spark.sql("""
        SELECT
            modalidade_nome,
            COUNT(*)                          AS total,
            ROUND(AVG(valor_estimado), 2)     AS valor_medio,
            ROUND(SUM(valor_estimado), 2)     AS valor_total
        FROM contratacoes
        WHERE valor_estimado > 0
        GROUP BY modalidade_nome
        ORDER BY total DESC
        LIMIT 10
    """)




def carregar_silver(
    spark: SparkSession,
    uri: str,
    database: str,
    collection: str,
) -> DataFrame:
    """
    Carrega documentos enriquecidos da camada Silver (editais_categorizados).

    Schema adicional em relação ao Bronze:
      categorias_cnae          array<{codigo, descricao, confianca}>
      justificativa_categorizacao  string
      resumo_simplificado          string
      processamento_status         string  ('success' | 'error')
    """
    return (
        spark.read.format("mongodb")
        .option("spark.mongodb.read.connection.uri", uri)
        .option("spark.mongodb.read.database", database)
        .option("spark.mongodb.read.collection", collection)
        .load()
    )


def agregar_por_cnae(df: DataFrame) -> DataFrame:
    """
    Explode o array categorias_cnae e conta licitações por código CNAE MEI.

    Exclusivo da camada Silver — o campo categorias_cnae é gerado pelo Gemini
    no EditalProcessor. Usa F.explode para transformar um array em linhas
    (operação 1-para-N), depois agrega por código CNAE.
    """
    return (
        df.filter(F.col("processamento_status") == "success")
        .withColumn("cnae", F.explode("categorias_cnae"))
        .groupBy(
            F.col("cnae.codigo").alias("cnae_codigo"),
            F.col("cnae.descricao").alias("cnae_descricao"),
        )
        .agg(
            F.count("*").alias("total_licitacoes"),
            F.round(F.avg("cnae.confianca"), 3).alias("confianca_media"),
            F.round(F.sum("valor_total_estimado"), 2).alias("valor_total"),
        )
        .orderBy(F.col("total_licitacoes").desc())
    )




def mostrar_schema_tabular(df: DataFrame, label: str = "") -> None:
    """Imprime schema, contagem e amostra do DataFrame."""
    titulo = f"--- Schema: {label} ---" if label else "--- Schema Tabular ---"
    print(f"\n{titulo}")
    df.printSchema()
    print(f"Total de registros: {df.count()}")
    df.show(5, truncate=60)



def main() -> None:
    """
    Demonstra o pipeline completo Bronze → transformações → Silver.

    Fluxo:
      1. Lê Bronze (JSON semi-estruturado) → DataFrame raw
      2. Normaliza tipos de data e valores monetários
      3. Achata campos aninhados → DataFrame tabular
      4. Agrega por modalidade, estado e prazo
      5. Executa Spark SQL
      6. Lê Silver (enriquecido) → análise por CNAE MEI
    """
    from src.config.settings import Settings

    Settings.validate()

    spark = criar_sessao_spark(mongo_uri=Settings.MONGO_URI)

    # ── Bronze ──────────────────────────────────────────────────────────────
    print("\n====== CAMADA BRONZE — Dados Brutos PNCP ======")

    bronze_raw = carregar_bronze(
        spark,
        uri=Settings.MONGO_URI,
        database=Settings.MONGO_DATABASE,
        collection=Settings.MONGO_COLLECTION,
    )
    mostrar_schema_tabular(bronze_raw, "Bronze (raw — JSON semi-estruturado)")

    if bronze_raw.count() == 0:
        print("\n⚠️  Collection Bronze está vazia.")
        print("   Execute a ingestão primeiro: python -m src.bronze.run_bronze_ingestion")
        print("   (ou rode: python main.py)\n")
    else:
        bronze_norm = normalizar_tipos(bronze_raw)
        bronze_flat = flatten_campos_aninhados(bronze_norm)
        mostrar_schema_tabular(bronze_flat, "Bronze (normalizado + tabular)")

        print("\n--- Agregação por Modalidade ---")
        agregar_por_modalidade(bronze_flat).show(truncate=40)

        print("\n--- Ranking por Estado ---")
        agregar_por_estado(bronze_flat).show()

        print("\n--- Licitações com Prazo Aberto ---")
        filtrar_licitacoes_abertas(bronze_flat).show(10, truncate=50)

        print("\n--- Top 10 Modalidades (Spark SQL) ---")
        top10_modalidades_sql(spark, bronze_flat).show()

    # ── Silver ──────────────────────────────────────────────────────────────
    print("\n====== CAMADA SILVER — Dados Enriquecidos pelo Gemini ======")

    silver_df = carregar_silver(
        spark,
        uri=Settings.MONGO_URI,
        database=Settings.MONGO_DATABASE,
        collection=Settings.MONGO_SILVER_COLLECTION,
    )
    mostrar_schema_tabular(silver_df, "Silver (com categorias CNAE)")

    if silver_df.count() == 0:
        print("\n⚠️  Collection Silver está vazia.")
        print("   Execute o streaming Silver antes de analisar por CNAE.\n")
    else:
        print("\n--- Oportunidades por Categoria CNAE MEI ---")
        agregar_por_cnae(silver_df).show(truncate=50)

    spark.stop()


if __name__ == "__main__":
    main()
