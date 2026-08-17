"""Resolve and import the candidate answer (see exercise 01 conftest)."""
import os
import sys
from pathlib import Path

import pytest


def _target_dir() -> Path:
    env = os.environ.get("BENCH_TARGET")
    if env:
        return Path(env).resolve()
    return (Path(__file__).resolve().parent.parent / "workspace").resolve()


@pytest.fixture(scope="session")
def target_dir() -> Path:
    return _target_dir()


def pytest_configure():
    sys.path.insert(0, str(_target_dir()))
    # Make the local image_diff helper importable (standalone and under Harbor).
    sys.path.insert(0, str(Path(__file__).resolve().parent))
