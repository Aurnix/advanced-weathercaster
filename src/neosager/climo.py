"""Train-fold-only climatologies. Everything here is a FITTED quantity and a
leakage hazard: artifacts are computed strictly from train-station x
train-year data and written keyed to a hash of the split definition, so a
changed split can never silently reuse a stale climatology.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .config import Config


def split_hash(cfg: Config) -> str:
    key = json.dumps({
        "train_years": cfg.splits.train_years,
        "val_years": cfg.splits.val_years,
        "calib_years": cfg.splits.calib_years,
        "test_years": cfg.splits.test_years,
        "station_test_frac": cfg.splits.station_test_frac,
        "seed": cfg.splits.seed,
    }, sort_keys=True)
    return hashlib.sha256(key.encode()).hexdigest()[:12]


def prevailing_wind(hourly_frames: list[pd.DataFrame]) -> dict[int, float]:
    """Vector-mean wind direction per calendar month across the given
    (train-year) hourly frames. Returns {month: direction_deg}."""
    us, vs, months = [], [], []
    for h in hourly_frames:
        ok = h["wind_dir_deg"].notna() & h["wind_speed_ms"].notna()
        d = np.radians(h.loc[ok, "wind_dir_deg"].to_numpy())
        # unit vectors (direction only — speed-weighting would let a few
        # storms own the climatology)
        us.append(pd.Series(-np.sin(d), index=h.index[ok]))
        vs.append(pd.Series(-np.cos(d), index=h.index[ok]))
    if not us:
        return {}
    u = pd.concat(us)
    v = pd.concat(vs)
    m = u.index.month
    out = {}
    for month in range(1, 13):
        sel = m == month
        if sel.sum() < 30:
            continue
        mu, mv = u[sel].mean(), v[sel].mean()
        out[month] = float((np.degrees(np.arctan2(-mu, -mv))) % 360)
    return out


def event_climatology(labels: pd.DataFrame, station: str) -> pd.DataFrame:
    """P(event | month) per label column for one station's train years."""
    rows = []
    m = labels.index.month
    for col in labels.columns:
        if col.startswith("cond_"):
            continue
        for month in range(1, 13):
            sel = labels.loc[m == month, col].dropna()
            rows.append({"station": station, "label": col, "month": month,
                         "n": int(len(sel)),
                         "k": int(sel.sum())})
    return pd.DataFrame(rows)


def climo_dir(cfg: Config) -> Path:
    d = cfg.paths.resolved("artifacts_dir") / f"climo_{split_hash(cfg)}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_station_climo(cfg: Config, station: str,
                       prevailing: dict[int, float],
                       events: pd.DataFrame) -> None:
    d = climo_dir(cfg)
    with open(d / f"{station}_prevailing.json", "w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in prevailing.items()}, f)
    events.to_parquet(d / f"{station}_events.parquet")


def load_prevailing(cfg: Config, station: str) -> dict[int, float] | None:
    p = climo_dir(cfg) / f"{station}_prevailing.json"
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return {int(k): v for k, v in json.load(f).items()}
