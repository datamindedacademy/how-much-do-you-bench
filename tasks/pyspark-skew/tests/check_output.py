"""The report has to reconcile with the events, and match a version-aware join.

Expected values are computed here from the raw inputs, independently of the job:
each event counted once, attributed to its customer's latest dimension version.
"""

import subprocess
import sys
from pathlib import Path

import polars as pl

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'} {label}" + ("" if ok else f": {detail}"))
    if not ok:
        failures.append(label)


out = Path("/app/out/revenue.parquet")
if out.exists():
    subprocess.run(["rm", "-rf", str(out)], check=False)

run = subprocess.run(
    [sys.executable, "/app/job.py"], capture_output=True, text=True, timeout=900
)
check("job succeeds", run.returncode == 0, (run.stderr or run.stdout)[-500:])

if not out.exists():
    check("output written", False, "no /app/out/revenue.parquet")
    sys.exit(1)

# Spark writes a directory of part files, not a single parquet.
actual = pl.read_parquet(str(out / "*.parquet") if out.is_dir() else str(out))
events = pl.read_parquet("/app/data/events.parquet")
customers = pl.read_parquet("/app/data/customers.parquet")

latest = (
    customers.sort(["customer_id", "valid_from"])
    .group_by("customer_id")
    .last()
)
expected = (
    events.join(latest, on="customer_id", how="left")
    .with_columns(
        pl.col("segment").fill_null("unknown"),
        pl.col("country").fill_null("unknown"),
    )
    .group_by(["segment", "country"])
    .agg(
        pl.col("amount").sum().round(2).alias("revenue"),
        pl.len().alias("events"),
    )
    .sort(["segment", "country"])
)

# Reconciliation first: this is the complaint finance actually made.
check(
    "event count reconciles",
    actual["events"].sum() == events.height,
    f"{actual['events'].sum()} counted against {events.height} events",
)
check(
    "revenue reconciles",
    abs(actual["revenue"].sum() - round(events["amount"].sum(), 2)) < 0.5,
    f"{actual['revenue'].sum():.2f} against {events['amount'].sum():.2f}",
)

# Then the attribution: reconciling totals can still be spread across the wrong
# segments if an older version of a customer won the join.
got = actual.select(["segment", "country", "revenue", "events"]).sort(["segment", "country"])
check("groups match", got.height == expected.height, f"{got.height} vs {expected.height} groups")

if got.height == expected.height:
    joined = got.join(expected, on=["segment", "country"], suffix="_want")
    check("all groups present", joined.height == expected.height, "group keys differ")
    if joined.height == expected.height:
        worst_rev = (joined["revenue"] - joined["revenue_want"]).abs().max()
        worst_cnt = (joined["events"] - joined["events_want"]).abs().max()
        check("revenue per group", worst_rev < 0.5, f"largest gap {worst_rev:.2f}")
        check("events per group", worst_cnt == 0, f"largest gap {worst_cnt}")

sys.exit(1 if failures else 0)
