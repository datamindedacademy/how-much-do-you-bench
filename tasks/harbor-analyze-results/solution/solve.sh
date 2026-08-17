#!/bin/bash
# The upstream reference answer, embedded file by file.
set -euo pipefail

mkdir -p /app
cat > /app/analyze_results.py <<'SOLUTION_EOF'
"""Reference solution: analyze a Harbor job directory."""
from __future__ import annotations

import re
from pathlib import Path

# A verbose pytest line: "<nodeid> PASSED/FAILED/ERROR [ 12%]".
_TEST_LINE = re.compile(r"^(?P<nodeid>\S+::\S+)\s+(?P<status>PASSED|FAILED|ERROR)\b")


def _parse_stdout(path: Path) -> tuple[list[str], list[str]]:
    """Return (passed_node_ids, failed_node_ids) from a verbose pytest stdout."""
    passed: list[str] = []
    failed: list[str] = []
    if not path.exists():
        return passed, failed
    for line in path.read_text().splitlines():
        m = _TEST_LINE.match(line.strip())
        if not m:
            continue
        if m.group("status") == "PASSED":
            passed.append(m.group("nodeid"))
        else:  # FAILED or ERROR
            failed.append(m.group("nodeid"))
    return passed, failed


def _read_reward(path: Path) -> float:
    if not path.exists():
        return 0.0
    try:
        return float(path.read_text().strip())
    except ValueError:
        return 0.0


def analyze_run(job_dir) -> dict:
    job = Path(job_dir)
    exercises = []
    for d in sorted(job.iterdir()):
        if not d.is_dir() or not d.name.startswith("python__"):
            continue
        name = d.name.rsplit("__", 1)[0]  # strip the random suffix
        passed, failed = _parse_stdout(d / "verifier" / "test-stdout.txt")
        reward = _read_reward(d / "verifier" / "reward.txt")
        exercises.append({
            "name": name,
            "reward": reward,
            "passed": len(passed),
            "failed": len(failed),
            "passed_tests": passed,
            "failed_tests": failed,
        })

    exercises.sort(key=lambda e: e["name"])
    return {
        "exercises": exercises,
        "total_passed": sum(e["passed"] for e in exercises),
        "total_failed": sum(e["failed"] for e in exercises),
        "n_exercises": len(exercises),
        "reward_sum": sum(e["reward"] for e in exercises),
    }
SOLUTION_EOF
