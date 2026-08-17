"""Summarise a Harbor task trajectory.

CURRENT STATE: this handles single-attempt runs only. Your job (see
../instruction.md) is to extend it to also handle multi-attempt runs
(steps/attemptN/...), adding an "n_attempts" key, without breaking the
single-attempt path.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def _outcome(task: Path) -> str:
    if (task / "exception.txt").exists():
        return "AGENT_ERROR"
    reward_f = task / "verifier" / "reward.txt"
    if not reward_f.exists():
        return "AGENT_ERROR"
    return "PASS" if reward_f.read_text().strip().startswith("1") else "FAIL"


def analyze_trajectory(task_dir) -> dict:
    task = Path(task_dir)

    tools: Counter = Counter()
    n_steps = n_calls = 0

    traj = task / "agent" / "trajectory.json"
    if traj.exists():
        try:
            data = json.loads(traj.read_text())
        except (json.JSONDecodeError, OSError):
            data = {}
        for step in data.get("steps", []):
            if step.get("source") != "agent":
                continue
            n_steps += 1
            for tc in step.get("tool_calls") or []:
                tools[tc.get("function_name", "?")] += 1
                n_calls += 1

    return {
        "outcome": _outcome(task),
        "n_steps": n_steps,
        "n_tool_calls": n_calls,
        "tools": dict(tools),
        "skill_invoked": tools.get("skill", 0) > 0,
    }
