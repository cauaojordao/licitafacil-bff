"""
Serviço de analytics baseado no Iceberg.
Lê dados da camada Silver e grava métricas agregadas no Supabase/Postgres.
"""

import logging
from datetime import datetime, timezone

from pyspark.sql import SparkSession
from supabase import create_client

from apps.maintenance.src.repositories.iceberg_repository import IcebergRepository

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(
        self,
        warehouse_path: str,
        supabase_url: str,
        supabase_key: str,
    ):
        self.warehouse_path = warehouse_path
        self.spark = self._create_spark_session()
        self.iceberg_repository = IcebergRepository(self.spark, warehouse_path)
        self.supabase = create_client(supabase_url, supabase_key)

    def run_analytics(self, database: str, table: str) -> None:
        logger.info(
            "Iniciando analytics: %s.%s",
            database,
            table,
        )

        self._generate_summary(database, table)
        self._generate_by_state(database, table)
        self._generate_by_category(database, table)

        logger.info("Analytics atualizado com sucesso")

    def _full_table_name(self, database: str, table: str) -> str:
        return f"iceberg_catalog.{database}.{table}"

    def _generate_summary(self, database: str, table: str) -> None:
        df = self.spark.sql(f"""
            SELECT
                COUNT(*) AS total_opportunities,
                COALESCE(SUM(valor_total_estimado), 0) AS total_estimated_value,
                COALESCE(AVG(relevancia_score), 0) AS average_relevance
            FROM {self._full_table_name(database, table)}
        """)

        row = df.first()

        payload = {
            "id": 1,
            "total_opportunities": int(row["total_opportunities"]),
            "total_estimated_value": float(row["total_estimated_value"]),
            "average_relevance": float(row["average_relevance"]),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        self.supabase.table("analytics_summary").upsert(payload).execute()
        logger.info("analytics_summary atualizado")

    def _generate_by_state(self, database: str, table: str) -> None:
        df = self.spark.sql(f"""
            SELECT
                uf,
                COUNT(*) AS total_opportunities,
                COALESCE(SUM(valor_total_estimado), 0) AS total_estimated_value
            FROM {self._full_table_name(database, table)}
            WHERE uf IS NOT NULL AND uf != ''
            GROUP BY uf
        """)

        rows = [
            {
                "uf": row["uf"],
                "total_opportunities": int(row["total_opportunities"]),
                "total_estimated_value": float(row["total_estimated_value"]),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            for row in df.collect()
        ]

        if rows:
            self.supabase.table("analytics_by_state").upsert(rows).execute()

        logger.info("analytics_by_state atualizado")

    def _generate_by_category(self, database: str, table: str) -> None:
        df = self.spark.sql(f"""
            SELECT
                categoria_ia AS category,
                COUNT(*) AS total_opportunities,
                COALESCE(SUM(valor_total_estimado), 0) AS total_estimated_value
            FROM {self._full_table_name(database, table)}
            WHERE categoria_ia IS NOT NULL AND categoria_ia != ''
            GROUP BY categoria_ia
        """)

        rows = [
            {
                "category": row["category"],
                "total_opportunities": int(row["total_opportunities"]),
                "total_estimated_value": float(row["total_estimated_value"]),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            for row in df.collect()
        ]

        if rows:
            self.supabase.table("analytics_by_category").upsert(rows).execute()

        logger.info("analytics_by_category atualizado")

    def _create_spark_session(self) -> SparkSession:
        return (
            SparkSession.builder.appName("IcebergAnalytics")
            .config(
                "spark.jars.packages",
                "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2",
            )
            .config(
                "spark.sql.catalog.iceberg_catalog",
                "org.apache.iceberg.spark.SparkCatalog",
            )
            .config("spark.sql.catalog.iceberg_catalog.type", "hadoop")
            .config(
                "spark.sql.catalog.iceberg_catalog.warehouse",
                self.warehouse_path,
            )
            .getOrCreate()
        )

    def close(self) -> None:
        self.spark.stop()
