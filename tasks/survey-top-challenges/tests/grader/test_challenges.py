"""Hidden grader for exercise 13: top challenges + plot."""
import importlib

import pytest


@pytest.fixture(scope="session")
def mod():
    return importlib.import_module("challenges")


@pytest.fixture
def csv_path(target_dir):
    return target_dir / "quant151.csv"


TOP5 = [
    ("Data quality", 98),
    ("Aligning data initiatives with business strategy", 92),
    ("Building data literacy across the organization", 79),
    ("Data governance implementation", 71),
    ("Demonstrating ROI of data investments", 71),
]


def _pairs(result):
    return [tuple(p) for p in result]      # accept list- or tuple-pairs


def _assert_real_png(path):
    import matplotlib.image as mpimg
    import numpy as np
    assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    img = np.asarray(mpimg.imread(str(path)), dtype=float)
    assert img.std() > 0.0, "the plot looks blank (a single flat colour)"
    gray = img[..., :3].mean(axis=-1) if img.ndim == 3 else img
    assert (gray < 0.5).any(), "no dark pixels — expected axes / bars"


def test_top5(mod, csv_path):
    assert _pairs(mod.top_challenges(csv_path, 5)) == TOP5


def test_default_n_is_5(mod, csv_path):
    assert _pairs(mod.top_challenges(csv_path)) == TOP5


def test_respects_n(mod, csv_path):
    assert _pairs(mod.top_challenges(csv_path, 3)) == TOP5[:3]


def test_plot_is_a_real_chart(mod, csv_path, tmp_path):
    out = tmp_path / "challenges.png"
    mod.plot_challenges(mod.top_challenges(csv_path, 5), out)
    _assert_real_png(out)
