"""Hidden grader for exercise 01. The candidate never sees this file."""
import importlib

import pytest


@pytest.fixture(scope="session")
def run(target_dir):
    mod = importlib.import_module("analyze_results")
    job = target_dir / "sample_jobs" / "job-mixed"
    return mod.analyze_run(job)


def test_exercise_count_and_order(run):
    names = [e["name"] for e in run["exercises"]]
    assert names == [
        "python__affine-cipher",
        "python__book-store",
        "python__bowling",
    ]
    assert run["n_exercises"] == 3


def test_book_store_partial_fail(run):
    e = next(e for e in run["exercises"] if e["name"] == "python__book-store")
    assert e["reward"] == 0
    assert e["passed"] == 2
    assert e["failed"] == 1
    assert e["failed_tests"] == [
        "book_store_test.py::BookStoreTest::test_two_different_books"
    ]
    assert set(e["passed_tests"]) == {
        "book_store_test.py::BookStoreTest::test_only_a_single_book",
        "book_store_test.py::BookStoreTest::test_two_of_the_same_book",
    }


def test_affine_all_pass(run):
    e = next(e for e in run["exercises"] if e["name"] == "python__affine-cipher")
    assert e["reward"] == 1
    assert e["passed"] == 3
    assert e["failed"] == 0
    assert e["failed_tests"] == []


def test_bowling_counts_error_as_failure(run):
    e = next(e for e in run["exercises"] if e["name"] == "python__bowling")
    # one PASSED, one FAILED, one ERROR -> 1 passed, 2 failed
    assert e["passed"] == 1
    assert e["failed"] == 2
    assert "bowling_test.py::BowlingTest::test_consecutive_strikes" in e["failed_tests"]


def test_totals(run):
    assert run["total_passed"] == 6
    assert run["total_failed"] == 3
    assert run["reward_sum"] == 1
