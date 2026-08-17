"""Enriches the orders extract.

Reads /app/data/orders.parquet and writes /app/out/enriched.parquet.
"""

from datetime import datetime, timezone

import polars as pl

BULK_TIERS = [(20, 0.15), (10, 0.10), (5, 0.05)]


def discount_for(qty: int) -> float:
    """Bulk discount rate for a line quantity."""
    for threshold, rate in BULK_TIERS:
        if qty >= threshold:
            return rate
    return 0.0


def ordered_date(epoch: int) -> str:
    """Calendar date the order was placed, UTC."""
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%d")


def line_label(row: dict) -> str:
    """Human-readable label used by the finance export."""
    kind = promo_kind(row["promo_code"])
    if row["qty"] >= 20:
        size = "bulk"
    elif row["qty"] >= 5:
        size = "multi"
    else:
        size = "single"
    price = row["unit_price"]
    if price >= 150:
        band = "high"
    elif price >= 50:
        band = "mid"
    else:
        band = "low"
    return f"{kind}/{size}/{band}"


def promo_kind(code: str) -> str:
    """The campaign a promo code belongs to."""
    if code is None or "-" not in code:
        return "UNKNOWN"
    return code.split("-", 1)[0].upper()


def main() -> None:
    orders = pl.read_parquet("/app/data/orders.parquet")

    enriched = orders.with_columns(
        pl.col("qty").map_elements(discount_for, return_dtype=pl.Float64).alias("discount_rate"),
        pl.col("promo_code").map_elements(promo_kind, return_dtype=pl.Utf8).alias("promo_kind"),
        pl.struct(["promo_code", "qty", "unit_price"])
        .map_elements(line_label, return_dtype=pl.Utf8)
        .alias("line_label"),
        pl.col("ordered_at").map_elements(ordered_date, return_dtype=pl.Utf8).alias("ordered_date"),
    ).with_columns(
        (
            pl.col("qty") * pl.col("unit_price") * (1.0 - pl.col("discount_rate"))
        ).round(2).alias("net_amount")
    )

    # Spend to date per customer, oldest order first.
    enriched = enriched.sort(["customer_id", "ordered_at"]).with_columns(
        pl.col("net_amount").cum_sum().over("customer_id").round(2).alias("running_spend")
    )

    enriched.write_parquet("/app/out/enriched.parquet")


if __name__ == "__main__":
    main()
