#!/bin/bash
# The dimension has one row per version, so joining it straight to the events
# multiplies every event of a restated customer. Reduce it to the current version
# per customer first, then join.
set -euo pipefail

cat > /app/job.py <<'PY'
"""Revenue per segment and country.

Reads /app/data/events.parquet and /app/data/customers.parquet, writes
/app/out/revenue.parquet.
"""

from pyspark.sql import SparkSession, Window, functions as F


def main() -> None:
    spark = (
        SparkSession.builder.appName("revenue")
        .master("local[2]")
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )

    events = spark.read.parquet("/app/data/events.parquet")
    customers = spark.read.parquet("/app/data/customers.parquet")

    # One row per customer: the version in force now.
    current = (
        customers.withColumn(
            "rn",
            F.row_number().over(
                Window.partitionBy("customer_id").orderBy(F.col("valid_from").desc())
            ),
        )
        .filter(F.col("rn") == 1)
        .drop("rn")
    )

    revenue = (
        events.join(F.broadcast(current), on="customer_id", how="left")
        .fillna({"segment": "unknown", "country": "unknown"})
        .groupBy("segment", "country")
        .agg(
            F.round(F.sum("amount"), 2).alias("revenue"),
            F.count("*").alias("events"),
        )
    )

    revenue.write.mode("overwrite").parquet("/app/out/revenue.parquet")
    spark.stop()


if __name__ == "__main__":
    main()
PY
