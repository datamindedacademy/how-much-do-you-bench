Two complaints, same week.

Finance says the revenue figure is sometimes yesterday's. Both DAGs in
`/app/dags` run on a daily timer, so `build_marts` fires whether or not
`ingest_orders` has landed anything that day. When the extract is late, the mart
is silently stale.

Platform says the opposite risk: last quarter the ingest was broken for three
days and nobody noticed, because the mart kept producing a figure. They want the
mart to keep running on its own schedule too, so a missing extract shows up as a
number that stops changing rather than a job that stops appearing.

So `build_marts` must run **as soon as the extract lands**, and **also once a day
regardless**, whichever comes first.

The scheduler must be able to parse both DAGs, and neither may rely on an API
that Airflow has already replaced -- the next upgrade removes it.

Constraints:

- Keep both DAG ids (`ingest_orders`, `build_marts`) and both task ids
  (`land_extract`, `total_revenue`).
- Keep the URI `file:///app/warehouse/orders.csv` as what the ingest produces
  and the mart consumes.
- Do not make `build_marts` depend on `ingest_orders` with a task or DAG
  dependency: the two run on their own, coupled only through the data.
