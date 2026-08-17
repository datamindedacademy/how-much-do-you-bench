"""Hidden grader for exercise 02 (single-attempt trajectories)."""
import importlib

import pytest


@pytest.fixture(scope="session")
def mod():
    return importlib.import_module("analyze_trajectory")


@pytest.fixture(scope="session")
def tasks(target_dir):
    return target_dir / "sample_tasks"


def test_pass_with_skill(mod, tasks):
    r = mod.analyze_trajectory(tasks / "python__connect__Gya8Hs4")
    assert r["outcome"] == "PASS"
    assert r["n_steps"] == 4
    assert r["n_tool_calls"] == 4
    assert r["skill_invoked"] is True
    assert r["tools"] == {"read": 1, "skill": 1, "edit": 1, "bash": 1}


def test_fail_no_skill(mod, tasks):
    r = mod.analyze_trajectory(tasks / "python__grep__yk3p1Q")
    assert r["outcome"] == "FAIL"
    assert r["n_steps"] == 2
    assert r["n_tool_calls"] == 2
    assert r["skill_invoked"] is False
    assert r["tools"] == {"read": 1, "edit": 1}


def test_agent_error_no_trajectory(mod, tasks):
    r = mod.analyze_trajectory(tasks / "python__forth__Zq02mn")
    assert r["outcome"] == "AGENT_ERROR"
    assert r["n_steps"] == 0
    assert r["n_tool_calls"] == 0
    assert r["tools"] == {}
    assert r["skill_invoked"] is False
