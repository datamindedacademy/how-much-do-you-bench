#!/bin/bash
# Every UDF here is expressible natively: the tiered discount as a when/then
# chain, the campaign as a string split, the label as concat_str over the same
# conditions, and the date with from_epoch + dt.strftime. That keeps the work
# inside polars instead of calling into Python once per row.
set -euo pipefail

cat > /app/transform.py <<'PY'
"""Enriches the orders extract.

Reads /app/data/orders.parquet and writes /app/out/enriched.parquet.
"""

import polars as pl


def main() -> None:
    campaign = pl.col("promo_code").str.split("-").list.first().str.to_uppercase()
    size = (
        pl.when(pl.col("qty") >= 20)
        .then(pl.lit("bulk"))
        .when(pl.col("qty") >= 5)
        .then(pl.lit("multi"))
        .otherwise(pl.lit("single"))
    )
    band = (
        pl.when(pl.col("unit_price") >= 150)
        .then(pl.lit("high"))
        .when(pl.col("unit_price") >= 50)
        .then(pl.lit("mid"))
        .otherwise(pl.lit("low"))
    )

    enriched = (
        pl.read_parquet("/app/data/orders.parquet")
        .with_columns(
            pl.when(pl.col("qty") >= 20)
            .then(0.15)
            .when(pl.col("qty") >= 10)
            .then(0.10)
            .when(pl.col("qty") >= 5)
            .then(0.05)
            .otherwise(0.0)
            .alias("discount_rate"),
            campaign.alias("promo_kind"),
            pl.concat_str([campaign, size, band], separator="/").alias("line_label"),
            pl.from_epoch(pl.col("ordered_at"), time_unit="s")
            .dt.strftime("%Y-%m-%d")
            .alias("ordered_date"),
        )
        .with_columns(
            (pl.col("qty") * pl.col("unit_price") * (1.0 - pl.col("discount_rate")))
            .round(2)
            .alias("net_amount")
        )
        .sort(["customer_id", "ordered_at"])
        .with_columns(
            pl.col("net_amount").cum_sum().over("customer_id").round(2).alias("running_spend")
        )
    )

    enriched.write_parquet("/app/out/enriched.parquet")


if __name__ == "__main__":
    main()
PY
