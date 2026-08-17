"""Loads yesterday's events, one task per source partition."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

FEED = Path("/app/feed/events.csv")


def partitions() -> list[str]:
    """Which partitions exist in the feed."""
    seen = set()
    with FEED.open() as handle:
        for row in csv.DictReader(handle):
            seen.add(row["partition"])
    return sorted(seen)


def load(partition: str) -> int:
    """Pretend to load one partition; returns the row count."""
    total = 0
    with FEED.open() as handle:
        for row in csv.DictReader(handle):
            if row["partition"] == partition:
                total += 1
    Path(f"/app/out/{partition}.count").write_text(f"{total}\n")
    return total


with DAG(
    dag_id="partitioned_load",
    start_date=datetime.now(),
    schedule="@daily",
) as dag:
    for name in partitions():
        PythonOperator(
            task_id=f"load_{name}",
            python_callable=load,
            op_args=[name],
        )
