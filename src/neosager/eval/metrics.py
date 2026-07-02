"""Verification metrics. All functions take plain arrays; NaN labels or NaN
predictions are excluded pairwise (count reported)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _clean(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    ok = ~np.isnan(y) & ~np.isnan(p)
    return y[ok], p[ok], int(ok.sum())


def brier(y, p) -> float:
    y, p, n = _clean(y, p)
    return float(np.mean((p - y) ** 2)) if n else np.nan


def brier_skill(y, p, p_ref) -> float:
    """BSS vs a reference forecast (climatology). Computed on rows where
    BOTH forecasts are defined, so the comparison is paired."""
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    r = np.asarray(p_ref, dtype=float)
    ok = ~np.isnan(y) & ~np.isnan(p) & ~np.isnan(r)
    if not ok.any():
        return np.nan
    bs = np.mean((p[ok] - y[ok]) ** 2)
    bs_ref = np.mean((r[ok] - y[ok]) ** 2)
    return float(1.0 - bs / bs_ref) if bs_ref > 0 else np.nan


def reliability_curve(y, p, n_bins: int = 10) -> pd.DataFrame:
    """Equal-count bins: (mean forecast, observed frequency, count)."""
    y, p, n = _clean(y, p)
    if n == 0:
        return pd.DataFrame(columns=["p_mean", "obs_freq", "n"])
    order = np.argsort(p)
    edges = np.array_split(order, n_bins)
    rows = [{"p_mean": float(p[idx].mean()),
             "obs_freq": float(y[idx].mean()),
             "n": int(len(idx))} for idx in edges if len(idx)]
    return pd.DataFrame(rows)


def sharpness(p, n_bins: int = 10) -> pd.Series:
    p = np.asarray(p, dtype=float)
    p = p[~np.isnan(p)]
    return pd.Series(np.histogram(p, bins=n_bins, range=(0, 1))[0])


def roc_auc(y, p) -> float:
    y, p, n = _clean(y, p)
    if n == 0 or len(np.unique(y)) < 2:
        return np.nan
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, p))


def heidke(y_class, f_class, n_classes: int = 4) -> float:
    """Heidke skill score for categorical forecasts."""
    y = np.asarray(y_class, dtype=float)
    f = np.asarray(f_class, dtype=float)
    ok = ~np.isnan(y) & ~np.isnan(f)
    y, f = y[ok].astype(int), f[ok].astype(int)
    n = len(y)
    if n == 0:
        return np.nan
    ct = np.zeros((n_classes, n_classes))
    np.add.at(ct, (f, y), 1)
    pc = np.trace(ct) / n
    pe = float((ct.sum(axis=0) * ct.sum(axis=1)).sum()) / n ** 2
    return float((pc - pe) / (1 - pe)) if pe < 1 else np.nan


def peirce(y_class, f_class, n_classes: int = 4) -> float:
    """Peirce (Hanssen-Kuipers) skill score, multiclass form."""
    y = np.asarray(y_class, dtype=float)
    f = np.asarray(f_class, dtype=float)
    ok = ~np.isnan(y) & ~np.isnan(f)
    y, f = y[ok].astype(int), f[ok].astype(int)
    n = len(y)
    if n == 0:
        return np.nan
    ct = np.zeros((n_classes, n_classes))
    np.add.at(ct, (f, y), 1)
    pc = np.trace(ct) / n
    pf = ct.sum(axis=1) / n   # forecast marginals
    po = ct.sum(axis=0) / n   # observed marginals
    pe = float((pf * po).sum())
    denom = 1 - float((po ** 2).sum())
    return float((pc - pe) / denom) if denom > 0 else np.nan
