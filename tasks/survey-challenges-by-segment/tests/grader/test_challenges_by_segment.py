"""Hidden grader for exercise 14: top challenges per segment."""
import importlib

import pytest


@pytest.fixture(scope="session")
def mod():
    return importlib.import_module("challenges_by_segment")


@pytest.fixture
def csv_path(target_dir):
    return target_dir / "quant151.csv"


def _norm(result):
    """Map {group: [(name, count), ...]} accepting list- or tuple-pairs."""
    return {g: [tuple(p) for p in pairs] for g, pairs in result.items()}


def test_by_size(mod, csv_path):
    res = _norm(mod.top_challenges_by_segment(csv_path, "size", 3))
    assert set(res) == {"<10M", "10-100M", ">100M"}
    assert res["<10M"] == [
        ("Aligning data initiatives with business strategy", 6),
        ("Data quality", 5),
        ("Alignment between leadership and data teams", 4),
    ]
    assert res["10-100M"] == [
        ("Data quality", 21),
        ("Building data literacy across the organization", 17),
        ("Aligning data initiatives with business strategy", 16),
    ]
    assert res[">100M"] == [
        ("Data quality", 72),
        ("Aligning data initiatives with business strategy", 70),
        ("Building data literacy across the organization", 60),
    ]


def test_by_industry(mod, csv_path):
    res = _norm(mod.top_challenges_by_segment(csv_path, "industry", 3))
    assert len(res) == 22
    assert all(len(pairs) <= 3 for pairs in res.values())
    assert res["Technology, Media & Telecommunications"] == [
        ("Data quality", 26),
        ("Aligning data initiatives with business strategy", 21),
        ("Data governance implementation", 20),
    ]
    assert res["Financial Services"] == [
        ("Aligning data initiatives with business strategy", 16),
        ("Data governance implementation", 15),
        ("Building data literacy across the organization", 13),
    ]


def test_k_param(mod, csv_path):
    res = _norm(mod.top_challenges_by_segment(csv_path, "size", 1))
    assert res[">100M"] == [("Data quality", 72)]
    assert all(len(pairs) == 1 for pairs in res.values())
