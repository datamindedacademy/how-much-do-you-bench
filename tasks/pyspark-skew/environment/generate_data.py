"""Builds the two inputs at image build time.

The customer dimension is a slowly-changing table: a customer who changed segment
or country appears more than once, with a valid_from marking when each version
took effect. About one customer in six has been restated at least once.
"""

import numpy as np
import polars as pl

SEED = 20260817
EVENTS = 3_000_000
CUSTOMERS = 6_000

rng = np.random.default_rng(SEED)

pl.DataFrame(
    {
        "event_id": np.arange(EVENTS, dtype=np.int64),
        # A slice of traffic carries ids the dimension has never heard of: a
        # partner feed that reports its own customer numbering.
        "customer_id": np.where(
            rng.random(EVENTS) < 0.02,
            rng.integers(900_000, 999_999, EVENTS, dtype=np.int64),
            rng.integers(0, CUSTOMERS, EVENTS, dtype=np.int64),
        ),
        "amount": np.round(rng.uniform(0.5, 90.0, EVENTS), 2),
    }
).write_parquet("/app/data/events.parquet")

rows = []
for cid in range(CUSTOMERS):
    versions = 1 + (1 if cid % 6 == 0 else 0) + (1 if cid % 31 == 0 else 0)
    for v in range(versions):
        rows.append(
            {
                "customer_id": cid,
                "segment": f"seg-{(cid + v) % 7}",
                "country": ["BE", "NL", "FR", "DE"][(cid + v) % 4],
                "valid_from": f"202{4 + v}-01-01",
            }
        )

pl.DataFrame(rows).write_parquet("/app/data/customers.parquet")
print(f"events: {EVENTS:,}  customer rows: {len(rows):,} for {CUSTOMERS:,} customers")
