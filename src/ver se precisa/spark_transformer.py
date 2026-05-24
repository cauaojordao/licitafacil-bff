"""
Exemplos de transformações PySpark para os dados do PNCP armazenados no MongoDB Atlas.

Estas funções ilustram o que PODE ser feito na etapa de transformação — não são
código de produção final. Cada função demonstra uma capacidade diferente do PySpark
aplicada ao schema real do projeto (contratações PNCP).

Para rodar localmente: Docker com Java 11, ou Google Colab (pip install pyspark).
Referência: Aula 07 — Engenharia de Dados e Big Data 2026.1
"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType

# ---------------------------------------------------------------------------
# 1. Sessão Spark
# ---------------------------------------------------------------------------


def criar_sessao_spark(app_name: str = "LicitaFacil-Spark") -> SparkSession:
    """Inicializa uma SparkSession em modo local."""
    return SparkSession.builder.appName(app_name).master("local[*]").getOrCreate()


# ---------------------------------------------------------------------------
# 2. Leitura do MongoDB Atlas
# ---------------------------------------------------------------------------


def carregar_do_mongodb(
    spark: SparkSession,
    uri: str,
    database: str,
    collection: str,
) -> DataFrame:
    """
    Carrega os documentos do MongoDB Atlas em um DataFrame Spark.

    Requer o conector MongoDB Spark Connector adicionado à sessão:
    config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.3.0")
    """
    return (
        spark.read.format("mongodb")
        .option("spark.mongodb.read.connection.uri", uri)
        .option("spark.mongodb.read.database", database)
        .option("spark.mongodb.read.collection", collection)
        .load()
    )


# ---------------------------------------------------------------------------
# 3. Exemplo — Normalização de tipos (Aula 07: withColumn + to_date + cast)
# ---------------------------------------------------------------------------


def normalizar_tipos(df: DataFrame) -> DataFrame:
    """
    Converte strings de data para DateType e valores monetários para DoubleType.

    Espelha o padrão da aula: datatrimestre → to_date, valores → cast(DoubleType()).
    Os campos originais em string são substituídos pelas versões tipadas.
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


# ---------------------------------------------------------------------------
# 4. Exemplo — Flatten de campos aninhados → formato tabular
# ---------------------------------------------------------------------------


def flatten_campos_aninhados(df: DataFrame) -> DataFrame:
    """
    Achata os subdocumentos MongoDB (orgao_entidade, unidade_orgao) em colunas planas.

    Este é o núcleo da atividade: transformar o JSON semi-estruturado do MongoDB
    em um DataFrame totalmente tabular, pronto para análise ou exportação.
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


# ---------------------------------------------------------------------------
# 5. Exemplo — Agregação por modalidade (groupBy + agg)
# ---------------------------------------------------------------------------


def agregar_por_modalidade(df: DataFrame) -> DataFrame:
    """
    Total de contratos, soma e média de valores por modalidade de licitação.

    Padrão groupBy + agg do Spark, equivalente a um GROUP BY no SQL.
    """
    return (
        df.groupBy("modalidade_nome")
        .agg(
            F.count("numero_controle_pncp").alias("total_contratos"),
            F.round(F.sum("valor_total_estimado"), 2).alias("valor_total"),
            F.round(F.avg("valor_total_estimado"), 2).alias("valor_medio"),
        )
        .orderBy(F.col("total_contratos").desc())
    )


# ---------------------------------------------------------------------------
# 6. Exemplo — Ranking de oportunidades por estado
# ---------------------------------------------------------------------------


def agregar_por_estado(df: DataFrame) -> DataFrame:
    """
    Concentração de licitações por UF — útil para mostrar onde estão
    as oportunidades para MEIs de cada região.
    """
    return (
        df.groupBy(F.col("unidade_orgao.uf_sigla").alias("uf"))
        .agg(
            F.count("*").alias("total_licitacoes"),
            F.round(F.sum("valor_total_estimado"), 2).alias("valor_total"),
        )
        .orderBy(F.col("total_licitacoes").desc())
    )


# ---------------------------------------------------------------------------
# 7. Exemplo — Análise por segmento MEI (campo do Gemini)
# ---------------------------------------------------------------------------


def agregar_por_segmento_mei(df: DataFrame) -> DataFrame:
    """
    Conta e soma valores por categoria de MEI categorizada pelo Gemini.

    Só processa os documentos que já foram categorizados (segmento_mei não nulo),
    mostrando quais segmentos têm mais oportunidades de negócio.
    """
    return (
        df.filter(F.col("segmento_mei").isNotNull())
        .groupBy("segmento_mei")
        .agg(
            F.count("*").alias("total_licitacoes"),
            F.round(F.sum("valor_total_estimado"), 2).alias("valor_total"),
            F.round(F.avg("valor_total_estimado"), 2).alias("valor_medio"),
        )
        .orderBy(F.col("total_licitacoes").desc())
    )


# ---------------------------------------------------------------------------
# 8. Exemplo — Filtro de licitações com prazo aberto (Spark vs pipeline atual)
# ---------------------------------------------------------------------------


def filtrar_licitacoes_abertas(df: DataFrame) -> DataFrame:
    """
    Equivalente distribuído do que a pipeline deadline_alerts.py faz no MongoDB.

    Demonstra como o Spark pode substituir ou complementar as aggregation pipelines
    do Mongo com a mesma lógica, mas com capacidade de processamento massivo.
    """
    hoje = F.current_date()
    return (
        df.filter(
            F.to_date(F.col("data_encerramento_proposta"), "yyyy-MM-dd'T'HH:mm:ss")
            >= hoje
        )
        .select(
            "numero_controle_pncp",
            "objeto_compra",
            "modalidade_nome",
            "data_encerramento_proposta",
            "valor_total_estimado",
            F.col("unidade_orgao.uf_sigla").alias("uf"),
            F.col("unidade_orgao.municipio_nome").alias("municipio"),
        )
        .orderBy(F.col("data_encerramento_proposta").asc())
    )


# ---------------------------------------------------------------------------
# 9. Exemplo — Spark SQL (como mostrado na Aula 07)
# ---------------------------------------------------------------------------


def top10_modalidades_sql(spark: SparkSession, df: DataFrame) -> DataFrame:
    """
    Registra o DataFrame como view temporária e executa SQL padrão.

    O Spark SQL suporta as mesmas fontes que o conector MongoDB, S3, Parquet, etc.
    Permite que analistas escrevam SQL familiar sem abrir mão do processamento
    distribuído.
    """
    df.createOrReplaceTempView("contratacoes")
    return spark.sql("""
        SELECT
            modalidade_nome,
            COUNT(*)                              AS total,
            ROUND(AVG(valor_total_estimado), 2)   AS valor_medio,
            ROUND(SUM(valor_total_estimado), 2)   AS valor_total
        FROM contratacoes
        WHERE valor_total_estimado > 0
        GROUP BY modalidade_nome
        ORDER BY total DESC
        LIMIT 10
    """)


# ---------------------------------------------------------------------------
# 10. Exemplo — Schema final tabular (printSchema)
# ---------------------------------------------------------------------------


def mostrar_schema_tabular(df: DataFrame) -> None:
    """Imprime o schema do DataFrame após todas as transformações."""
    print("\n--- Schema Tabular Final (PNCP → PySpark) ---")
    df.printSchema()
    print(f"\nTotal de registros: {df.count()}")
    df.show(5, truncate=50)
