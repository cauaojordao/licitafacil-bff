"""
Job de analytics do Iceberg.
Lê a camada Silver e materializa métricas no Supabase.
"""

import logging

from apps.maintenance.src.services.analytics_service import AnalyticsService
from libs.common.config import Settings

logger = logging.getLogger(__name__)


class IcebergAnalyticsJob:
    def __init__(
        self,
        database: str = "pncp_silver",
        table: str = "editais_enriched",
    ):
        self.database = database
        self.table = table

        self.analytics_service = AnalyticsService(
            warehouse_path=Settings.ICEBERG_WAREHOUSE_PATH,
            supabase_url=Settings.SUPABASE_URL,
            supabase_key=Settings.SUPABASE_KEY,
        )

    def run(self) -> None:
        logger.info(
            "Executando job analytics: %s.%s",
            self.database,
            self.table,
        )

        try:
            self.analytics_service.run_analytics(
                database=self.database,
                table=self.table,
            )
        finally:
            self.analytics_service.close()


def main() -> None:

    job = IcebergAnalyticsJob()
    job.run()


if __name__ == "__main__":
    main()
