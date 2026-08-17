#!/bin/bash
# The upstream reference answer, embedded file by file.
set -euo pipefail

mkdir -p /app
cat > /app/challenges_by_segment.py <<'SOLUTION_EOF'
"""Reference solution: top survey challenges within each segment."""
from __future__ import annotations

import csv
from collections import Counter, defaultdict

_SIZE = {
    "Less than €1M": "<10M", "€1M - €10M": "<10M",
    "€10M - €50M": "10-100M", "€50M - €100M": "10-100M",
    "€100M - €1B": ">100M", "More than €1B": ">100M",
}


def _load(csv_path):
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    return rows[0], rows[1], rows[2:]        # codes, question text, data


def _challenge_columns(codes, questions):
    return [(i, questions[i].split(" - ")[-1].strip())
            for i, c in enumerate(codes)
            if c.startswith("Q20a") and not c.endswith("_TEXT")]


def top_challenges_by_segment(csv_path, segment, k=3) -> dict:
    codes, questions, data = _load(csv_path)
    cols = _challenge_columns(codes, questions)

    if segment == "size":
        gi = codes.index("Q1")
        group_of = lambda v: _SIZE.get(v.strip())
    elif segment == "industry":
        gi = codes.index("Q4")
        group_of = lambda v: v.strip() or None
    else:
        raise ValueError(f"unknown segment: {segment!r}")

    groups: dict = defaultdict(Counter)
    for row in data:
        g = group_of(row[gi])
        if g is None:
            continue
        for i, label in cols:
            if row[i].strip():
                groups[g][label] += 1

    return {g: sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:k]
            for g, c in groups.items()}
SOLUTION_EOF
