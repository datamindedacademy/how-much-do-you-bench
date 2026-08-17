#!/bin/bash
# The scan moves into a task, and the fan-out becomes dynamic task mapping over
# that task's output -- so partitions are still discovered from the feed, but at
# run time rather than on every parse. start_date becomes fixed and catchup
# explicit, so the DAG can be backfilled.
set -euo pipefail

cat > /app/dags/partitioned_load.py <<'PY'
"""Loads yesterday's events, one mapped task per source partition."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from airflow.sdk import dag, task

FEED = Path("/app/feed/events.csv")


@dag(
    dag_id="partitioned_load",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
)
def partitioned_load() -> None:
    @task
    def partitions() -> list[str]:
        seen = set()
        with FEED.open() as handle:
            for row in csv.DictReader(handle):
                seen.add(row["partition"])
        return sorted(seen)

    @task
    def load(partition: str) -> int:
        total = 0
        with FEED.open() as handle:
            for row in csv.DictReader(handle):
                if row["partition"] == partition:
                    total += 1
        Path(f"/app/out/{partition}.count").write_text(f"{total}\n")
        return total

    load.expand(partition=partitions())


partitioned_load()
PY
