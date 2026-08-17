#!/bin/bash
# The upstream reference answer, embedded file by file.
set -euo pipefail

mkdir -p /app
cat > /app/analyze_trajectory.py <<'SOLUTION_EOF'
"""Reference solution: trajectory analyzer for single- AND multi-attempt runs."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


def _attempt_num(p: Path) -> int:
    m = re.search(r"(\d+)$", p.name)
    return int(m.group(1)) if m else 0


def _parse_trajectory(attempt_dir: Path) -> tuple[int, int, Counter]:
    """Return (n_agent_steps, n_tool_calls, tool_counter) for one attempt dir."""
    tools: Counter = Counter()
    traj = attempt_dir / "agent" / "trajectory.json"
    if not traj.exists():
        return 0, 0, tools
    try:
        data = json.loads(traj.read_text())
    except (json.JSONDecodeError, OSError):
        return 0, 0, tools

    n_steps = n_calls = 0
    for step in data.get("steps", []):
        if step.get("source") != "agent":
            continue
        n_steps += 1
        for tc in step.get("tool_calls") or []:
            tools[tc.get("function_name", "?")] += 1
            n_calls += 1
    return n_steps, n_calls, tools


def _outcome(task: Path, final_attempt: Path) -> str:
    # An exception anywhere (task root or the final attempt) is an agent error.
    if (task / "exception.txt").exists() or (final_attempt / "exception.txt").exists():
        return "AGENT_ERROR"
    reward_f = final_attempt / "verifier" / "reward.txt"
    if not reward_f.exists():
        return "AGENT_ERROR"
    return "PASS" if reward_f.read_text().strip().startswith("1") else "FAIL"


def analyze_trajectory(task_dir) -> dict:
    task = Path(task_dir)

    steps_root = task / "steps"
    if steps_root.is_dir():
        attempts = sorted(steps_root.glob("attempt*"), key=_attempt_num)
    else:
        attempts = [task]              # single-attempt run

    tools: Counter = Counter()
    n_steps = n_calls = 0
    for a in attempts:
        s, c, t = _parse_trajectory(a)
        n_steps += s
        n_calls += c
        tools.update(t)

    final = attempts[-1] if attempts else task
    return {
        "outcome": _outcome(task, final),
        "n_attempts": len(attempts),
        "n_steps": n_steps,
        "n_tool_calls": n_calls,
        "tools": dict(tools),
        "skill_invoked": tools.get("skill", 0) > 0,
    }
SOLUTION_EOF
