"""Hidden grader for exercise 12: data-initiative buckets + plot."""
import importlib

import pytest


@pytest.fixture(scope="session")
def mod():
    return importlib.import_module("initiatives")


@pytest.fixture
def csv_path(target_dir):
    return target_dir / "quant151.csv"


def _assert_real_png(path):
    import matplotlib.image as mpimg
    import numpy as np
    assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    img = np.asarray(mpimg.imread(str(path)), dtype=float)
    assert img.std() > 0.0, "the plot looks blank (a single flat colour)"
    gray = img[..., :3].mean(axis=-1) if img.ndim == 3 else img
    assert (gray < 0.5).any(), "no dark pixels — expected axes / bars"


def test_buckets(mod, csv_path):
    assert mod.initiative_buckets(csv_path) == {"1-5": 58, "6-10": 36, "10+": 40}


def test_plot_is_a_real_chart(mod, csv_path, tmp_path):
    out = tmp_path / "initiatives.png"
    mod.plot_buckets(mod.initiative_buckets(csv_path), out)
    _assert_real_png(out)
