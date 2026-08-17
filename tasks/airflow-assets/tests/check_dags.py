"""Both DAGs must parse, and the mart must be scheduled on what the ingest writes.

Plain asserts rather than pytest: the image ships airflow and nothing else, and
adding a test runner would mean reaching for PyPI at build time, which fails
behind an intercepting proxy.
"""

import os
import sys

os.environ.setdefault("AIRFLOW__CORE__DAGS_FOLDER", "/app/dags")
os.environ.setdefault("AIRFLOW__CORE__LOAD_EXAMPLES", "False")

from airflow.models.dagbag import DagBag

URI = "file:///app/warehouse/orders.csv"

failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS {label}")
    else:
        print(f"FAIL {label}: {detail}")
        failures.append(label)


bag = DagBag(dag_folder="/app/dags", include_examples=False)
check("dags parse", not bag.import_errors, str(bag.import_errors))

if not bag.import_errors:
    check(
        "both dags present",
        set(bag.dag_ids) >= {"ingest_orders", "build_marts"},
        str(sorted(bag.dag_ids)),
    )

    # bag.dags, not get_dag(): the latter consults the metadata database, which
    # a parse-only check has no reason to stand up.
    producer = bag.dags.get("ingest_orders")
    outlets = producer.get_task("land_extract").outlets if producer else []
    uris = {getattr(o, "uri", None) or getattr(o, "name", None) for o in outlets}
    check("producer declares the asset", URI in uris, str(outlets))

    mart = bag.dags.get("build_marts")
    schedule = getattr(mart, "schedule", None)
    rendered = repr(schedule)
    # A timer here is the bug, so a timetable that ignores the asset fails.
    check("mart scheduled on the asset", URI in rendered, rendered)
    check(
        "schedule is asset-driven",
        "Asset" in type(schedule).__name__ or "Asset" in rendered,
        f"{type(schedule).__name__}: {rendered}",
    )

# Airflow 3.0 still ships a shim for airflow.datasets, so the old API parses and
# merely warns. Leaving it in place is exactly the migration this task is about,
# so the check is on the source rather than on whether it happened to import.
from pathlib import Path

sources = {p.name: p.read_text() for p in Path("/app/dags").glob("*.py")}
stale = sorted(n for n, t in sources.items() if "airflow.datasets" in t or "Dataset(" in t)
check("no deprecated dataset api", not stale, f"still using the old API: {stale}")

sys.exit(1 if failures else 0)
