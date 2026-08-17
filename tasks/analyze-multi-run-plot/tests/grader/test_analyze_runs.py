"""Hidden grader for exercise 08: multi-run analysis + plot."""
import importlib
import os
from pathlib import Path

import pytest

import image_diff

REFERENCE_IMAGE = Path(__file__).resolve().parent / "reference_output.png"


@pytest.fixture(scope="session")
def mod():
    return importlib.import_module("analyze_runs")


@pytest.fixture(scope="session")
def summaries(mod, target_dir):
    return mod.analyze_runs(target_dir / "runs")


def test_runs_sorted_by_name(summaries):
    assert [s["run"] for s in summaries] == [
        "opencode-raw",
        "opencode-system-prompt",
        "opencode-system-prompt-skills",
    ]


def test_opencode_raw_30pct(summaries):
    s = next(s for s in summaries if s["run"] == "opencode-raw")
    assert s["n_exercises"] == 3
    assert s["solved"] == 1
    assert s["success_rate"] == pytest.approx(1 / 3)
    assert s["tests_passed"] == 6
    assert s["tests_total"] == 15


def test_system_prompt_60pct(summaries):
    s = next(s for s in summaries if s["run"] == "opencode-system-prompt")
    assert s["solved"] == 2
    assert s["success_rate"] == pytest.approx(2 / 3)
    assert s["tests_passed"] == 11


def test_skills_same_rate_more_tests(summaries):
    s2 = next(s for s in summaries if s["run"] == "opencode-system-prompt")
    s3 = next(s for s in summaries if s["run"] == "opencode-system-prompt-skills")
    # same overall success rate as the system-prompt run ...
    assert s3["success_rate"] == pytest.approx(s2["success_rate"])
    # ... but more successful hidden tests (the reason to plot both metrics)
    assert s3["tests_passed"] == 13
    assert s3["tests_passed"] > s2["tests_passed"]


def test_plot_written(mod, summaries, tmp_path):
    out = tmp_path / "runs.png"
    mod.plot_runs(summaries, out)
    assert out.exists() and out.stat().st_size > 0
    # valid PNG magic bytes
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_plot_is_a_real_chart(mod, summaries, tmp_path):
    """The image diff can't tell a blank canvas from the (mostly white) reference,
    so verify the plot actually has axes and a bar/line series drawn on it."""
    out = tmp_path / "candidate.png"
    mod.plot_runs(summaries, out)
    s = image_diff.structure(out)
    print(f"\nplot structure: {s}")

    assert s["ink"] >= 0.002, "the plot looks blank (almost no non-white pixels)"
    # Axis spines show up as near-full-length dark vertical/horizontal lines.
    assert s["vaxis"] >= 0.4 and s["haxis"] >= 0.4, (
        "no axes detected (need both a y-axis and an x-axis spine); "
        f"got vaxis={s['vaxis']:.2f}, haxis={s['haxis']:.2f}"
    )
    # A real bar/line series is either coloured, or fills the plot interior with
    # ink — empty axes have neither.
    assert s["colored"] >= 0.003 or s["interior_ink"] >= 0.007, (
        "no bar/line series detected inside the axes "
        f"(colored={s['colored']:.4f}, interior_ink={s['interior_ink']:.4f}); "
        "is the data actually plotted?"
    )


def test_plot_resembles_reference(mod, summaries, tmp_path):
    """Diff the produced plot against the reference image to see how far off it is.

    The exercise allows different layouts, so this is a generous similarity gate
    (override the threshold with $BENCH_PLOT_MAX_DIFF); the diff % is printed so
    you can read it even on a pass (run pytest with -rA / -s to surface it).
    """
    out = tmp_path / "candidate.png"
    mod.plot_runs(summaries, out)

    diff = image_diff.difference(out, REFERENCE_IMAGE)
    threshold = float(os.environ.get("BENCH_PLOT_MAX_DIFF", "0.30"))
    print(f"\nplot image diff vs reference: {diff * 100:.1f}%  "
          f"(threshold {threshold * 100:.0f}%)")

    assert diff <= threshold, (
        f"produced plot differs from the reference by {diff * 100:.1f}% "
        f"(> {threshold * 100:.0f}%); does it plot both the success rate and the "
        f"successful-test count for all three runs?"
    )
