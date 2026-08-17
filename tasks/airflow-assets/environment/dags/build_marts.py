"""Rebuilds the orders mart.

Runs on a timer, which is why the mart is sometimes built from yesterday's
extract. It should run when the extract actually lands instead.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.datasets import Dataset
from airflow.decorators import task

ORDERS = Dataset("file:///app/warehouse/orders.csv")


with DAG(
    dag_id="build_marts",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
):

    @task
    def total_revenue() -> None:
        source = Path("/app/warehouse/orders.csv")
        rows = list(csv.DictReader(source.open()))
        total = sum(float(r["amount"]) for r in rows)
        out = Path("/app/warehouse/revenue.txt")
        out.write_text(f"{total:.2f}\n")

    total_revenue()
