#!/bin/bash
# The upstream reference answer, embedded file by file.
set -euo pipefail

mkdir -p /app
cat > /app/initiatives.py <<'SOLUTION_EOF'
"""Reference solution: bucket data-initiative counts and plot them."""
from __future__ import annotations

import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

_LABELS = {
    "1-5 initiatives": "1-5",
    "6-10 initiatives": "6-10",
    "More than 10 initiatives": "10+",
}
_ORDER = ["1-5", "6-10", "10+"]


def _rows(csv_path):
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    return rows[0], rows[2:]              # codes, data (skip the question-text row)


def initiative_buckets(csv_path) -> dict:
    codes, data = _rows(csv_path)
    q2 = codes.index("Q2")
    counts = {b: 0 for b in _ORDER}
    for row in data:
        bucket = _LABELS.get(row[q2].strip())
        if bucket:
            counts[bucket] += 1
    return counts


def plot_buckets(buckets, output_path) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(_ORDER, [buckets.get(b, 0) for b in _ORDER], color="#4C78A8")
    ax.set_xlabel("data initiatives completed (last 12 months)")
    ax.set_ylabel("number of organizations")
    ax.set_title("Data initiatives completed")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
SOLUTION_EOF
