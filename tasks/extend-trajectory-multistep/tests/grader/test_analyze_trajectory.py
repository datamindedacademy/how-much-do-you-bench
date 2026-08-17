"""Hidden grader for exercise 06: single- and multi-attempt trajectories."""
import importlib

import pytest


@pytest.fixture(scope="session")
def mod():
    return importlib.import_module("analyze_trajectory")


@pytest.fixture(scope="session")
def tasks(target_dir):
    return target_dir / "sample_tasks"


def test_single_attempt_still_works(mod, tasks):
    r = mod.analyze_trajectory(tasks / "python__grep__single1")
    assert r["outcome"] == "FAIL"
    assert r["n_attempts"] == 1
    assert r["n_steps"] == 2
    assert r["n_tool_calls"] == 2
    assert r["skill_invoked"] is False
    assert r["tools"] == {"read": 1, "edit": 1}


def test_single_attempt_agent_error(mod, tasks):
    r = mod.analyze_trajectory(tasks / "python__forth__err1")
    assert r["outcome"] == "AGENT_ERROR"
    assert r["n_attempts"] == 1
    assert r["n_steps"] == 0
    assert r["tools"] == {}


def test_multi_attempt_aggregates(mod, tasks):
    r = mod.analyze_trajectory(tasks / "python__connect__multi1")
    # final attempt (attempt2) passed
    assert r["outcome"] == "PASS"
    assert r["n_attempts"] == 2
    # summed across both attempts: read,edit,bash + read,skill,edit
    assert r["n_steps"] == 6
    assert r["n_tool_calls"] == 6
    assert r["tools"] == {"read": 2, "edit": 2, "bash": 1, "skill": 1}
    assert r["skill_invoked"] is True
