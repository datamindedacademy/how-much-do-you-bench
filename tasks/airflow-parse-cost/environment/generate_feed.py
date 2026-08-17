"""Builds the events feed at image build time.

Generated rather than committed: the file has to be big enough that scanning it
during a parse is unmistakably expensive, and a 100MB+ fixture does not belong in
a git repository.
"""

import csv
import random
from pathlib import Path

SEED = 20260817
ROWS = 6_000_000
PARTITIONS = [f"p{i:02d}" for i in range(12)]

random.seed(SEED)
out = Path("/app/feed/events.csv")
out.parent.mkdir(parents=True, exist_ok=True)

with out.open("w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(["event_id", "partition", "payload"])
    for i in range(ROWS):
        writer.writerow([i, random.choice(PARTITIONS), "x" * 12])

print(f"feed: {ROWS:,} rows, {out.stat().st_size / 1e6:.0f} MB")
