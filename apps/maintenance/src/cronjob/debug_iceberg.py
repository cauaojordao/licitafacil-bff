# apps/maintenance/src/cronjob/debug_iceberg.py

import logging

from pyspark.sql import SparkSession


logger = logging.getLogger(__name__)

WAREHOUSE = "/tmp/iceberg-warehouse"
TABLE = "iceberg_catalog.pncp_silver.editais_enriched"


spark = (
    SparkSession.builder
    .appName("Debug-Iceberg")
    .config(
        "spark.jars.packages",
        "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2"
    )
    .config(
        "spark.sql.catalog.iceberg_catalog",
        "org.apache.iceberg.spark.SparkCatalog"
    )
    .config("spark.sql.catalog.iceberg_catalog.type", "hadoop")
    .config("spark.sql.catalog.iceberg_catalog.warehouse", WAREHOUSE)
    .getOrCreate()
)

logger.info("\n=== NAMESPACES ===")
spark.sql("SHOW NAMESPACES IN iceberg_catalog").show(truncate=False)

logger.info("\n=== TABLES ===")
spark.sql("SHOW TABLES IN iceberg_catalog.pncp_silver").show(truncate=False)

logger.info("\n=== COLUMNS ===")
spark.sql(f"DESCRIBE TABLE {TABLE}").show(200, truncate=False)

logger.info("\n=== COUNT ===")
spark.sql(f"SELECT COUNT(*) AS total FROM {TABLE}").show(truncate=False)

logger.info("\n=== SAMPLE ===")
spark.sql(f"SELECT * FROM {TABLE} LIMIT 5").show(truncate=False)

logger.info("\n=== FILES ===")
spark.sql(f"SELECT * FROM {TABLE}.files").show(50, truncate=False)

logger.info("\n=== SNAPSHOTS ===")
spark.sql(f"SELECT * FROM {TABLE}.snapshots").show(50, truncate=False)

logger.info("\n=== HISTORY ===")
spark.sql(f"SELECT * FROM {TABLE}.history").show(50, truncate=False)

spark.stop()