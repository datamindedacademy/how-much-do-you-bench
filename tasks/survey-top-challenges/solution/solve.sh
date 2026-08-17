#!/bin/bash
# The upstream reference answer, embedded file by file.
set -euo pipefail

mkdir -p /app
cat > /app/challenges.py <<'SOLUTION_EOF'
"""Reference solution: rank survey challenges and plot the top ones."""
from __future__ import annotations

import csv
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def _load(csv_path):
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    return rows[0], rows[1], rows[2:]        # codes, question text, data


def _challenge_columns(codes, questions):
    return [(i, questions[i].split(" - ")[-1].strip())
            for i, c in enumerate(codes)
            if c.startswith("Q20a") and not c.endswith("_TEXT")]


def top_challenges(csv_path, n=5) -> list:
    codes, questions, data = _load(csv_path)
    cols = _challenge_columns(codes, questions)
    counts = Counter()
    for row in data:
        for i, label in cols:
            if row[i].strip():
                counts[label] += 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:n]


def plot_challenges(challenges, output_path) -> None:
    labels = [c[0] for c in challenges]
    values = [c[1] for c in challenges]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(labels[::-1], values[::-1], color="#E45756")   # highest at the top
    ax.set_xlabel("number of organizations")
    ax.set_title("Top challenges")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
SOLUTION_EOF
