# apps/maintenance/src/cronjob/debug_iceberg.py

from pyspark.sql import SparkSession


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

print("\n=== NAMESPACES ===")
spark.sql("SHOW NAMESPACES IN iceberg_catalog").show(truncate=False)

print("\n=== TABLES ===")
spark.sql("SHOW TABLES IN iceberg_catalog.pncp_silver").show(truncate=False)

print("\n=== COLUMNS ===")
spark.sql(f"DESCRIBE TABLE {TABLE}").show(200, truncate=False)

print("\n=== COUNT ===")
spark.sql(f"SELECT COUNT(*) AS total FROM {TABLE}").show(truncate=False)

print("\n=== SAMPLE ===")
spark.sql(f"SELECT * FROM {TABLE} LIMIT 5").show(truncate=False)

print("\n=== FILES ===")
spark.sql(f"SELECT * FROM {TABLE}.files").show(50, truncate=False)

print("\n=== SNAPSHOTS ===")
spark.sql(f"SELECT * FROM {TABLE}.snapshots").show(50, truncate=False)

print("\n=== HISTORY ===")
spark.sql(f"SELECT * FROM {TABLE}.history").show(50, truncate=False)

spark.stop()