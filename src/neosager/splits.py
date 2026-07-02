"""Fold assignment. Splits are BY STATION and BY YEAR, never random rows.

- Station folds: 85/15 train/test, regime-stratified, seeded, committed into
  the manifest (column station_fold) so they can never be resampled.
- Year folds: train 1990-2016, val 2017-18, calib 2019, test 2020-24.
- Purge: an example whose label window (t + purge_lead_h) lands in a
  different year-fold than t is dropped — train labels must not peek into
  val/test years.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Config


def assign_station_folds(manifest: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.splits.seed)
    out = manifest.copy()
    out["station_fold"] = "train"
    for regime, grp in out.groupby("regime", sort=True):
        n_test = max(1, round(len(grp) * cfg.splits.station_test_frac))
        test_idx = rng.choice(grp.index, size=n_test, replace=False)
        out.loc[test_idx, "station_fold"] = "test"
    return out


def year_fold(year: int, cfg: Config) -> str:
    s = cfg.splits
    for name, (a, b) in [("train", s.train_years), ("val", s.val_years),
                         ("calib", s.calib_years), ("test", s.test_years)]:
        if a <= year <= b:
            return name
    return "outside"


def example_mask(index: pd.DatetimeIndex, cfg: Config) -> np.ndarray:
    """Thinning + purge: keep t at 0 mod thin_hours whose purge window stays
    within t's own year-fold."""
    thin = index.hour % cfg.splits.thin_hours == 0
    yf = np.array([year_fold(y, cfg) for y in index.year])
    end = index + pd.Timedelta(hours=cfg.splits.purge_lead_h)
    yf_end = np.array([year_fold(y, cfg) for y in end.year])
    return thin & (yf == yf_end) & (yf != "outside")


def train_mask_rng(station: str, cfg: Config) -> np.random.Generator:
    """Deterministic RNG for the manual-input masking augmentation.
    (hashlib, not hash() — the builtin is salted per process.)"""
    import hashlib
    digest = hashlib.sha256(f"{station}|{cfg.splits.seed}".encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "little"))
