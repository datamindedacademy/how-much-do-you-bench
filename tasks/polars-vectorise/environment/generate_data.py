"""Builds the orders extract at image build time.

Generated rather than committed: it has to be large enough that row-at-a-time
Python is hopeless and vectorised expressions are comfortable, which is not a size
that belongs in git.
"""

import numpy as np
import polars as pl

SEED = 20260817
ROWS = 8_000_000

rng = np.random.default_rng(SEED)
kinds = np.array(["SUMMER", "LOYALTY", "WELCOME", "NONE"])

frame = pl.DataFrame(
    {
        "order_id": np.arange(ROWS, dtype=np.int64),
        "customer_id": rng.integers(0, 200_000, ROWS, dtype=np.int64),
        "qty": rng.integers(1, 40, ROWS, dtype=np.int32),
        "unit_price": np.round(rng.uniform(1.0, 250.0, ROWS), 2),
        "promo_code": [
            f"{k}-{n:05d}" for k, n in zip(kinds[rng.integers(0, 4, ROWS)], rng.integers(0, 99999, ROWS))
        ],
        "ordered_at": rng.integers(1_760_000_000, 1_780_000_000, ROWS, dtype=np.int64),
    }
)
frame.write_parquet("/app/data/orders.parquet")
print(f"orders: {ROWS:,} rows")
