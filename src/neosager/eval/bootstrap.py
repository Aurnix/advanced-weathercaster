"""Block-bootstrap confidence intervals.

Blocks are station x ISO-week: a station-week is plausibly exchangeable
while keeping within-week autocorrelation intact inside blocks. Paired
differences (model A - model B) are resampled on identical blocks, so CIs on
differences are much tighter than the individual CIs.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd


def block_ids(station_ids: pd.Series, index: pd.DatetimeIndex) -> np.ndarray:
    iso = index.isocalendar()
    key = (station_ids.astype(str).to_numpy() + "|"
           + iso.year.astype(str).to_numpy() + "-"
           + iso.week.astype(str).to_numpy())
    _, ids = np.unique(key, return_inverse=True)
    return ids


def bootstrap_ci(metric: Callable[[np.ndarray], float],
                 blocks: np.ndarray, n_rows: int,
                 n_boot: int = 1000, seed: int = 0,
                 alpha: float = 0.05) -> tuple[float, float, float]:
    """Generic block bootstrap. `metric` maps a row-index array -> scalar.
    Returns (point, lo, hi)."""
    rng = np.random.default_rng(seed)
    point = metric(np.arange(n_rows))
    uniq = np.unique(blocks)
    # index rows by block once
    order = np.argsort(blocks, kind="stable")
    sorted_blocks = blocks[order]
    starts = np.searchsorted(sorted_blocks, uniq, side="left")
    ends = np.searchsorted(sorted_blocks, uniq, side="right")
    rows_by_block = [order[a:b] for a, b in zip(starts, ends)]

    stats = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(uniq), size=len(uniq))
        idx = np.concatenate([rows_by_block[i] for i in pick])
        stats.append(metric(idx))
    stats = np.asarray(stats, dtype=float)
    stats = stats[~np.isnan(stats)]
    if len(stats) == 0:
        return point, np.nan, np.nan
    lo, hi = np.quantile(stats, [alpha / 2, 1 - alpha / 2])
    return point, float(lo), float(hi)
