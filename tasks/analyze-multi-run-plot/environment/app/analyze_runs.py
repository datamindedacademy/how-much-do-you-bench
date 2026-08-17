"""Compare multiple Harbor runs and plot them.

Implement `analyze_runs` and `plot_runs` per ../instruction.md.
"""
from __future__ import annotations

from pathlib import Path


def analyze_runs(runs_dir) -> list[dict]:
    raise NotImplementedError


def plot_runs(summaries, output_path) -> None:
    raise NotImplementedError
