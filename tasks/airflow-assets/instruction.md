The orders mart is regularly built from yesterday's extract.

Both DAGs in `/app/dags` run on a daily timer, so `build_marts` fires whether or
not `ingest_orders` has landed anything that day. When the extract is late, the
mart is silently stale. Nobody notices until someone reconciles revenue.

Make `build_marts` run when the extract actually lands, rather than on a clock.
The producer already declares what it writes; the consumer should be scheduled
on that, so a late extract delays the mart instead of skipping it.

While you are in there: both DAGs use the dataset API that Airflow 3 replaced.
It still parses, on a deprecation shim that will not survive the next upgrade.
Move to the current API.

Constraints:

- Keep both DAG ids (`ingest_orders`, `build_marts`) and both task ids
  (`land_extract`, `total_revenue`).
- Keep the asset URI `file:///app/warehouse/orders.csv`.
- No references to the deprecated dataset API may remain in `/app/dags`.
- Do not schedule `build_marts` on a cron, a timedelta, or `None`.
