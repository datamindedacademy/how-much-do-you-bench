"""Tiny, dependency-light image difference for grading exercise 08's plot.

Uses only numpy + matplotlib (already required by the exercise). Both images are
converted to grayscale and nearest-neighbour resampled onto a fixed grid (so
differing figure sizes/DPIs don't matter), then compared with a normalised RMSE
in [0, 1] — 0 = identical, 1 = maximally different.

It is a *coarse* similarity: it tolerates small rendering differences (fonts,
anti-aliasing, matplotlib versions) and alternative-but-reasonable layouts, while
moving clearly for an unrelated figure. The background is mostly white, so the
metric is dominated by where the "ink" lands; the exercise lets the candidate
choose the layout, so this is a generous "how far off" signal, not a pixel match.
"""
from __future__ import annotations

import numpy as np
import matplotlib.image as mpimg

_GRID = (200, 320)  # rows, cols


def _load_gray(path) -> np.ndarray:
    img = np.asarray(mpimg.imread(path), dtype=np.float64)
    if img.max() > 1.0:               # uint8-style 0..255 -> 0..1
        img = img / 255.0
    if img.ndim == 3:                 # drop alpha, average RGB -> gray
        img = img[..., :3].mean(axis=2)
    h, w = img.shape
    ys = np.linspace(0, h - 1, _GRID[0]).astype(int)
    xs = np.linspace(0, w - 1, _GRID[1]).astype(int)
    return img[np.ix_(ys, xs)]


def difference(path_a, path_b) -> float:
    """Normalised RMSE in [0, 1] between two images (0 = identical)."""
    a = _load_gray(path_a)
    b = _load_gray(path_b)
    return float(np.sqrt(np.mean((a - b) ** 2)))


def _load_rgb(path) -> np.ndarray:
    img = np.asarray(mpimg.imread(path), dtype=np.float64)
    if img.max() > 1.0:
        img = img / 255.0
    if img.ndim == 2:                 # grayscale -> RGB
        img = np.stack([img] * 3, axis=-1)
    return img[..., :3]


def structure(path) -> dict:
    """Cheap pixel features used to assert a real chart was drawn (not a blank
    canvas, and not just empty axes).

    Returns:
      ink            fraction of non-white pixels (blank canvas ~0)
      vaxis, haxis   length of the longest dark vertical / horizontal run as a
                     fraction of height / width — axis spines make these large
      colored        fraction of saturated (coloured) pixels — bars/lines drawn
                     in a real colour; axes/text are black/grey (~0)
      interior_ink   non-white fraction *inside* the plotting area (excludes the
                     spines and tick labels) — empty axes ~0, bars/line clearly >0
    """
    rgb = _load_rgb(path)
    gray = rgb.mean(axis=2)
    h, w = gray.shape

    ink = gray < 0.85
    dark = gray < 0.5
    sat = rgb.max(axis=2) - rgb.min(axis=2)

    # Longest dark run per column / row -> axis spines are near-full-length lines.
    vaxis = float(dark.sum(axis=0).max()) / h
    haxis = float(dark.sum(axis=1).max()) / w

    y0, y1 = int(0.08 * h), int(0.85 * h)
    x0, x1 = int(0.16 * w), int(0.95 * w)
    interior_ink = float(ink[y0:y1, x0:x1].mean()) if (y1 > y0 and x1 > x0) else 0.0

    return {
        "ink": float(ink.mean()),
        "vaxis": vaxis,
        "haxis": haxis,
        "colored": float((sat > 0.2).mean()),
        "interior_ink": interior_ink,
    }
