#!/bin/bash
# Airflow 3 renamed Dataset to Asset and moved it into airflow.sdk. The consumer
# is then scheduled on the asset itself rather than on a clock.
set -euo pipefail

python - <<'PY'
from pathlib import Path

for name in ("ingest_orders.py", "build_marts.py"):
    p = Path("/app/dags") / name
    s = p.read_text()
    s = s.replace("from airflow.datasets import Dataset", "from airflow.sdk import Asset")
    s = s.replace("Dataset(", "Asset(")
    p.write_text(s)

# The mart runs when the extract lands, not daily.
p = Path("/app/dags/build_marts.py")
s = p.read_text().replace('schedule="@daily"', "schedule=ORDERS")
p.write_text(s)
PY
