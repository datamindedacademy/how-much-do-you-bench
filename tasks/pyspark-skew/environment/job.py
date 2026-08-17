"""Revenue per segment and country.

Reads /app/data/events.parquet and /app/data/customers.parquet, writes
/app/out/revenue.parquet.
"""

from pyspark.sql import SparkSession, functions as F


def main() -> None:
    spark = (
        SparkSession.builder.appName("revenue")
        .master("local[2]")
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )

    events = spark.read.parquet("/app/data/events.parquet")
    customers = spark.read.parquet("/app/data/customers.parquet")

    revenue = (
        events.join(customers, on="customer_id", how="inner")
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
