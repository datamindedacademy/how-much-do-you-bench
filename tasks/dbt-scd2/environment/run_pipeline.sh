#!/bin/bash
# Replays the daily feed from a clean warehouse: load the day's extract over the
# raw table, then snapshot it. Each day is a separate dbt invocation, because
# that is how it runs in production.
set -euo pipefail

rm -f /app/warehouse.duckdb
cd /app/pipeline

for day in 1 2 3; do
  python - "$day" <<'PY'
import sys, duckdb
day = sys.argv[1]
con = duckdb.connect("/app/warehouse.duckdb")
con.execute("CREATE OR REPLACE TABLE main.raw_customers AS "
            f"SELECT *, TIMESTAMP '2026-03-0{day} 06:00:00' AS loaded_at "
            f"FROM read_csv_auto('/app/feed/day{day}.csv')")
con.close()
PY
  dbt snapshot --profiles-dir /app/pipeline --project-dir /app/pipeline
done
