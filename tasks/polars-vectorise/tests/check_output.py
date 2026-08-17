"""Same answers, inside the window.

The expected values are computed here independently of the script under test, so a
transform that is fast because it stopped doing the work fails.
"""

import subprocess
import sys
import time
from pathlib import Path

import polars as pl

# The UDF version takes ~28s and the vectorised one ~7s on the build fixture, so
# this sits between them with room on both sides for a busy worker.
BUDGET_SEC = 15.0
failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'} {label}" + ("" if ok else f": {detail}"))
    if not ok:
        failures.append(label)


out = Path("/app/out/enriched.parquet")
if out.exists():
    out.unlink()

started = time.perf_counter()
run = subprocess.run(
    [sys.executable, "/app/transform.py"], capture_output=True, text=True, timeout=600
)
elapsed = time.perf_counter() - started
print(f"     transform took {elapsed:.1f}s")

check("transform succeeds", run.returncode == 0, (run.stderr or run.stdout)[-400:])
check("inside the window", elapsed < BUDGET_SEC, f"{elapsed:.1f}s against a {BUDGET_SEC:.0f}s budget")

if not out.exists():
    check("output written", False, "no /app/out/enriched.parquet")
    sys.exit(1)

actual = pl.read_parquet(out)
orders = pl.read_parquet("/app/data/orders.parquet")

expected = (
    orders.with_columns(
        pl.when(pl.col("qty") >= 20)
        .then(0.15)
        .when(pl.col("qty") >= 10)
        .then(0.10)
        .when(pl.col("qty") >= 5)
        .then(0.05)
        .otherwise(0.0)
        .alias("discount_rate"),
        pl.col("promo_code").str.split("-").list.first().str.to_uppercase().alias("promo_kind"),
        pl.concat_str(
            [
                pl.col("promo_code").str.split("-").list.first().str.to_uppercase(),
                pl.when(pl.col("qty") >= 20).then(pl.lit("bulk"))
                .when(pl.col("qty") >= 5).then(pl.lit("multi"))
                .otherwise(pl.lit("single")),
                pl.when(pl.col("unit_price") >= 150).then(pl.lit("high"))
                .when(pl.col("unit_price") >= 50).then(pl.lit("mid"))
                .otherwise(pl.lit("low")),
            ],
            separator="/",
        ).alias("line_label"),
        pl.from_epoch(pl.col("ordered_at"), time_unit="s").dt.strftime("%Y-%m-%d").alias("ordered_date"),
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

check("row count", actual.height == expected.height, f"{actual.height} vs {expected.height}")
check(
    "columns",
    set(expected.columns) <= set(actual.columns),
    f"missing {sorted(set(expected.columns) - set(actual.columns))}",
)

if set(expected.columns) <= set(actual.columns) and actual.height == expected.height:
    # Aggregates first: cheap, and they catch anything systematic.
    for col in ("discount_rate", "net_amount", "running_spend"):
        a = round(actual[col].sum(), 2)
        e = round(expected[col].sum(), 2)
        check(f"{col} total", abs(a - e) < 0.05, f"{a} vs {e}")

    for col in ("line_label", "ordered_date"):
        a = dict(zip(*actual[col].value_counts().to_dict(as_series=False).values()))
        e = dict(zip(*expected[col].value_counts().to_dict(as_series=False).values()))
        check(f"{col} distribution", a == e, f"{len(a)} distinct vs {len(e)}")

    a_kinds = dict(zip(*actual["promo_kind"].value_counts().to_dict(as_series=False).values()))
    e_kinds = dict(zip(*expected["promo_kind"].value_counts().to_dict(as_series=False).values()))
    check("promo_kind distribution", a_kinds == e_kinds, f"{a_kinds} vs {e_kinds}")

    # Then exact rows, so an error that cancels out in a sum is still caught.
    cols = ["order_id", "discount_rate", "promo_kind", "line_label", "ordered_date", "net_amount", "running_spend"]
    sample = expected.select(cols).sample(2000, seed=7).sort("order_id")
    got = actual.select(cols).join(sample.select("order_id"), on="order_id", how="inner").sort("order_id")
    check("sampled rows match exactly", got.equals(sample), "values differ on sampled order_ids")

sys.exit(1 if failures else 0)
