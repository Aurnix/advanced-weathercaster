"""Assemble feature+label matrices per station from hourly parquet.

Per station: concatenate ALL years (tendencies and label windows must cross
year boundaries), compute climatology (train years only) -> features ->
labels over the continuous series, then thin/purge and write one parquet per
(year_fold, station) under datasets/.

The manual-input masking augmentation (train fold only) simulates users who
entered nothing: mask_manual_group_frac of rows get the whole manual group
set to missing, mask_cloud_only_frac get cloud-type-only masked.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .climo import (event_climatology, load_prevailing, prevailing_wind,
                    save_station_climo, split_hash)
from .config import Config
from .features import build_features, mask_manual_inputs
from .labels import build_labels
from .splits import example_mask, train_mask_rng, year_fold

META_COLS = ["station_id", "regime", "coastal", "station_fold"]


def load_station_hourly(cfg: Config, station: str) -> pd.DataFrame | None:
    pdir = cfg.paths.resolved("parquet_dir") / station
    if not pdir.exists():
        return None
    frames = []
    for y in range(cfg.years.start, cfg.years.end + 1):
        p = pdir / f"{y}.parquet"
        if p.exists():
            frames.append(pd.read_parquet(p))
    if not frames:
        return None
    return pd.concat(frames).sort_index()


def build_station_dataset(cfg: Config, station_row: dict,
                          leads: list[int] | None = None) -> dict:
    """Process one station end-to-end. Returns row-count summary."""
    station = station_row["station_id"]
    hourly = load_station_hourly(cfg, station)
    if hourly is None or hourly.empty:
        return {"station": station, "status": "no_data"}

    a, b = cfg.splits.train_years
    train_hours = hourly[(hourly.index.year >= a) & (hourly.index.year <= b)]

    prevailing = load_prevailing(cfg, station)
    if prevailing is None:
        prevailing = prevailing_wind([train_hours])
        # event climatology from train years only, saved alongside
        train_labels = build_labels(train_hours, cfg)
        save_station_climo(cfg, station, prevailing,
                           event_climatology(train_labels, station))

    feats = build_features(hourly, cfg, prevailing or None)
    labels = build_labels(hourly, cfg, leads)

    keep = example_mask(hourly.index, cfg)
    df = feats[keep].join(labels[keep])
    df["station_id"] = station
    df["regime"] = station_row.get("regime", "unknown")
    df["coastal"] = bool(station_row.get("coastal", False))
    df["station_fold"] = station_row.get("station_fold", "train")

    # drop rows with no usable pressure signal at all — the device always
    # has pressure; such rows exist only where the station was down
    df = df[df["slp"].notna()]

    out_root = cfg.paths.resolved("datasets_dir") / split_hash(cfg)
    counts = {}
    rng = train_mask_rng(station, cfg)
    for yf, grp in df.groupby(
            pd.Series([year_fold(y, cfg) for y in df.index.year],
                      index=df.index)):
        grp = grp.copy()
        if yf == "train":
            fc = cfg.features
            u = rng.random(len(grp))
            grp_masked = mask_manual_inputs(grp, u < fc.mask_manual_group_frac)
            cloud_only = ((u >= fc.mask_manual_group_frac)
                          & (u < fc.mask_manual_group_frac
                             + fc.mask_cloud_only_frac))
            grp_masked.loc[cloud_only, "cloud_coarse"] = "missing"
            grp = grp_masked
        d = out_root / yf
        d.mkdir(parents=True, exist_ok=True)
        grp.to_parquet(d / f"{station}.parquet")
        counts[yf] = len(grp)
    return {"station": station, "status": "ok", **counts}


def build_all(cfg: Config, manifest: pd.DataFrame,
              leads: list[int] | None = None) -> pd.DataFrame:
    results = []
    for _, row in manifest.iterrows():
        r = build_station_dataset(cfg, row.to_dict(), leads)
        results.append(r)
        print(f"  dataset {r['station']}: {r['status']} "
              f"{ {k: v for k, v in r.items() if k not in ('station', 'status')} }",
              flush=True)
    summary = pd.DataFrame(results)
    out_root = cfg.paths.resolved("datasets_dir") / split_hash(cfg)
    with open(out_root / "split_manifest.json", "w", encoding="utf-8") as f:
        json.dump({"split_hash": split_hash(cfg),
                   "stations": summary.to_dict(orient="records")}, f, indent=1)
    return summary


def load_fold(cfg: Config, fold: str, columns: list[str] | None = None
              ) -> pd.DataFrame:
    d = cfg.paths.resolved("datasets_dir") / split_hash(cfg) / fold
    frames = [pd.read_parquet(p, columns=columns)
              for p in sorted(d.glob("*.parquet"))]
    return pd.concat(frames) if frames else pd.DataFrame()
