"""Same answers, and faster than what it replaced.

The expected values are computed here independently of the script under test, so a
transform that is fast because it stopped doing the work fails.

Speed is measured against the original implementation rather than a stopwatch.
A fixed budget is a measurement of the host as much as of the submission: the
graded fleet runs two rollouts per instance, so the same code took 8s on an idle
box and could take twice that beside a busy neighbour. Running the yardstick
here, immediately before the submission, on the same machine, under the same
load, is what makes the number mean the same thing every time.
"""

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import polars as pl

# The UDF version takes ~28s and a properly vectorised one ~7s, so the real
# ratio is about 4. Three is the bar: comfortably past "shaved a bit off the
# loop", comfortably short of requiring the exact solution we had in mind.
SPEEDUP = 3.0
BASELINE = "/tests/baseline_udf.py"
failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'} {label}" + ("" if ok else f": {detail}"))
    if not ok:
        failures.append(label)


# Bounded rather than unbounded: a submission that prints in a loop would
# otherwise be held entirely in the checker's memory, and the tail is all that
# ever gets reported anyway.
TAIL = 4000
TIMEOUT = 600


def timed(script: str, env: dict | None = None) -> tuple[float, int, str]:
    """Elapsed seconds, exit status, and the tail of what it said.

    A timeout is a result, not an exception: letting TimeoutExpired escape ends
    the checker before it can record which of the two scripts hung.
    """
    started = time.perf_counter()
    try:
        run = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            env={**os.environ, **(env or {})},
        )
    except subprocess.TimeoutExpired:
        return float(TIMEOUT), 124, f"timed out after {TIMEOUT}s"
    return time.perf_counter() - started, run.returncode, (run.stderr or run.stdout or "")[-TAIL:]


out = Path("/app/out/enriched.parquet")
if out.exists():
    out.unlink()

# The yardstick writes into a directory of the checker's own, which is then
# removed before the submission runs. It ran first and produced a correct
# answer: leaving it on disk at a documented path means a transform that copies
# it is both instant and exactly right.
scratch = Path(tempfile.mkdtemp(prefix="baseline-", dir="/tmp"))
baseline_out = scratch / "enriched.parquet"

# The yardstick first, so any warming of the page cache by reading the fixture
# counts in the submission's favour rather than against it.
baseline_elapsed, baseline_rc, baseline_err = timed(BASELINE, {"BASELINE_OUT": str(baseline_out)})
print(f"     baseline took {baseline_elapsed:.1f}s")
check("baseline runs", baseline_rc == 0, baseline_err[-400:])
shutil.rmtree(scratch, ignore_errors=True)

elapsed, rc, err = timed("/app/transform.py")
print(f"     transform took {elapsed:.1f}s")

check("transform succeeds", rc == 0, err[-400:])

# Both gated on the baseline having produced a time worth dividing by: a failed
# yardstick makes the ratio meaningless, and reporting "0.3x" for it sends the
# reader after the wrong problem.
if baseline_rc == 0:
    check(
        "faster than the implementation it replaced",
        elapsed * SPEEDUP <= baseline_elapsed,
        f"{elapsed:.1f}s against {baseline_elapsed:.1f}s, "
        f"which is {baseline_elapsed / max(elapsed, 1e-6):.1f}x rather than {SPEEDUP:.0f}x",
    )

if rc != 0 or not out.exists():
    check("output written", False, "no /app/out/enriched.parquet")
    sys.exit(1)

actual = pl.read_parquet(out)
orders = pl.read_parquet("/app/data/orders.parquet")

# Both the answer and the yardstick are computed from this file, so a submission
# that shrank it would make itself fast and correct at the same time -- and one
# that rewrote the values in place would be graded against its own edit while
# keeping the row count honest. The fingerprint is from image build time.
digest = hashlib.sha256(Path("/app/data/orders.parquet").read_bytes()).hexdigest()
want = Path("/opt/orders.sha256").read_text().strip()
check("the extract is intact", digest == want, f"orders.parquet was modified ({orders.height} rows)")

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
