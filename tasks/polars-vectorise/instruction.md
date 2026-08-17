`/app/transform.py` enriches the orders extract. It is correct and it is far too
slow: it now takes long enough that the nightly job overruns its window, and the
extract is only going to grow.

Make it fast. The output must stay byte-for-byte equivalent in meaning: same
columns, same values, same rows.

It must run in under 25 seconds, reading `/app/data/orders.parquet` and writing
`/app/out/enriched.parquet` exactly as it does now.

Constraints:

- Do not change `/app/data/orders.parquet`, and do not pre-compute the output.
  The verifier deletes `/app/out` and runs your script from scratch.
- Do not sample, approximate, or drop rows: all 8,000,000 must be there.
- `python /app/transform.py` must remain the way it is run.
