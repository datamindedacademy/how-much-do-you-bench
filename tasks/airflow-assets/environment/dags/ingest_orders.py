"""Lands the daily orders extract."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.datasets import Dataset
from airflow.decorators import task

ORDERS = Dataset("file:///app/warehouse/orders.csv")

ROWS = [
    {"order_id": "1001", "amount": "42.00"},
    {"order_id": "1002", "amount": "17.50"},
    {"order_id": "1003", "amount": "99.99"},
]


with DAG(
    dag_id="ingest_orders",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
):

    @task(outlets=[ORDERS])
    def land_extract() -> None:
        out = Path("/app/warehouse/orders.csv")
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["order_id", "amount"])
            writer.writeheader()
            writer.writerows(ROWS)

    land_extract()
