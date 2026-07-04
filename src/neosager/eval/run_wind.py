"""Wind-output predictands (Sager-dial-style): max wind band in window +
relative direction shift at lead. Trains 6 multiclass GBM heads and runs the
first verification of the Sager dial's DIRECTION and VELOCITY output rings
in their own vocabulary.

Committed ring mappings (documented here, not tunable):

Velocity ring -> expected max band (5-band vocabulary):
  idx 0 "Probably increasing."        -> band(now) + 1 (clip 4)
  idx 1 "Moderate to fresh (13-24)"   -> 2
  idx 2 "Strong (25-38)"              -> 3
  idx 3/4/5 gale and above            -> 4
  idx 6 "Diminishing"                 -> band(now) - 1 (clip 0)
  idx 7 "No important change"         -> band(now)

Direction ring -> relative-shift class: ring index i in 0..7 names the
absolute pair (N/NE, NE/E, ...) with midpoint 22.5 + 45*i degrees; the
relative class is that midpoint minus the current direction, binned with
the same boundaries as the winddir label. idx 8 (shifting/variable) -> 5.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..baselines.sager import SagerCaster
from ..climo import split_hash
from ..config import Config
from ..dataset import load_fold, load_station_hourly
from ..labels import band5, build_wind_labels
from ..models import gbm
from ..splits import example_mask
from .metrics import heidke, peirce
from .report import write_report

from ..config import REPO_ROOT as REPO
TARGETS = {"windband": 5, "winddir": 6}
LEADS = [6, 12, 24]


def build_labels_pass(cfg: Config, manifest: pd.DataFrame) -> Path:
    out_dir = (cfg.paths.resolved("datasets_dir") / split_hash(cfg)
               / "labels_wind")
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, sid in enumerate(manifest["station_id"]):
        out = out_dir / f"{sid}.parquet"
        if out.exists():
            continue
        hourly = load_station_hourly(cfg, sid)
        if hourly is None or hourly.empty:
            continue
        lab = build_wind_labels(hourly, cfg, LEADS)
        keep = example_mask(hourly.index, cfg)
        lab = lab[keep]
        lab["station_id"] = sid
        lab.to_parquet(out)
        if (i + 1) % 25 == 0:
            print(f"  labels_wind {i + 1}/{len(manifest)}", flush=True)
    return out_dir


def _join(fold_df: pd.DataFrame, extra: pd.DataFrame) -> pd.DataFrame:
    a = fold_df.reset_index(names="hour")
    b = extra.reset_index(names="hour")
    return a.merge(b, on=["hour", "station_id"], how="left").set_index("hour")


def run(cfg: Config, manifest: pd.DataFrame, report_name: str) -> Path:
    print("phase 1: wind labels", flush=True)
    lab_dir = build_labels_pass(cfg, manifest)
    extra = pd.concat([pd.read_parquet(p)
                       for p in sorted(lab_dir.glob("*.parquet"))])

    print("phase 2: folds", flush=True)
    train = load_fold(cfg, "train")
    train = _join(train[train["station_fold"] == "train"], extra)
    val = load_fold(cfg, "val")
    val = _join(val[val["station_fold"] == "train"], extra)
    test = load_fold(cfg, "test")
    cell_a = _join(test[test["station_fold"] == "train"], extra)

    models_dir = cfg.paths.resolved("models_dir") / "gbm_wind"
    sager = SagerCaster()
    print("sager rings on cell A...", flush=True)
    s_cell = sager.predict_frame(cell_a)

    # current band / direction for persistence + relative ring mapping
    spd_now_band = np.select(
        [cell_a["wind_class"] == c for c in
         ["calm", "light", "moderate", "strong", "gale"]],
        [0, 1, 2, 3, 4], default=np.nan)
    dir_now = cell_a["wind_sector"].to_numpy() * 22.5   # sector -> degrees

    rows = []
    for kind, ncls in TARGETS.items():
        for L in LEADS:
            tgt = f"{kind}_{L}h"
            mpath = models_dir / f"{tgt}.txt"
            if mpath.exists():
                booster = gbm.load(mpath)
            else:
                print(f"training {tgt}...", flush=True)
                booster = gbm.train_multiclass(train, val, tgt, ncls)
                gbm.save(booster, mpath)
            y = cell_a[tgt].to_numpy()
            f_gbm = np.argmax(gbm.predict(booster, cell_a), axis=1).astype(float)

            if kind == "windband":
                pers = spd_now_band
            else:
                pers = np.zeros(len(cell_a))          # "direction holds"
            rows.append({"target": tgt, "model": "gbm",
                         "heidke": heidke(y, f_gbm, ncls),
                         "peirce": peirce(y, f_gbm, ncls),
                         "n": int((~np.isnan(y)).sum())})
            rows.append({"target": tgt, "model": "persistence",
                         "heidke": heidke(y, pers, ncls),
                         "peirce": peirce(y, pers, ncls),
                         "n": int((~np.isnan(y) & ~np.isnan(pers)).sum())})

            # Sager rings speak to the 12-24h window
            if L in (12, 24):
                if kind == "windband":
                    v = s_cell["sager_velocity_idx"].to_numpy()
                    f_s = np.full(len(v), np.nan)
                    f_s[v == 1] = 2
                    f_s[v == 2] = 3
                    f_s[(v >= 3) & (v <= 5)] = 4
                    f_s[v == 0] = np.clip(spd_now_band[v == 0] + 1, 0, 4)
                    f_s[v == 6] = np.clip(spd_now_band[v == 6] - 1, 0, 4)
                    f_s[v == 7] = spd_now_band[v == 7]
                else:
                    d = s_cell["sager_direction_idx"].to_numpy()
                    mid = 22.5 + 45.0 * d
                    diff = (mid - dir_now + 180) % 360 - 180
                    f_s = np.full(len(d), np.nan)
                    f_s[np.abs(diff) <= 22.5] = 0
                    f_s[(diff > 22.5) & (diff <= 90)] = 1
                    f_s[diff > 90] = 2
                    f_s[(diff < -22.5) & (diff >= -90)] = 3
                    f_s[diff < -90] = 4
                    f_s[d == 8] = 5
                rows.append({"target": tgt, "model": "sager_ring",
                             "heidke": heidke(y, f_s, ncls),
                             "peirce": peirce(y, f_s, ncls),
                             "n": int((~np.isnan(y) & ~np.isnan(f_s)).sum())})
            print(f"  {tgt} scored", flush=True)

    res = pd.DataFrame(rows)
    res.to_csv(REPO / "reports" / f"{report_name}_results.csv", index=False)

    # gale recall (safety): P(predicted band >= 3 | observed band >= 3), 12h
    booster = gbm.load(models_dir / "windband_12h.txt")
    y = cell_a["windband_12h"].to_numpy()
    f = np.argmax(gbm.predict(booster, cell_a), axis=1)
    strong_obs = y >= 3
    gale_line = (f"Strong-or-gale recall at 12h: "
                 f"{float((f[strong_obs & ~np.isnan(y)] >= 3).mean()):.2f} "
                 f"(n={int(strong_obs[~np.isnan(y)].sum())})")

    sections = ["## Wind-output predictands (cell A, Heidke/Peirce)", "",
                res.to_markdown(index=False, floatfmt=".3f"), "",
                gale_line, "",
                "windband classes: calm/light/moderate-fresh/strong/gale "
                "(max within window). winddir classes: steady/veer/"
                "veer-sharp/back/back-sharp/calm-variable (at lead vs now).",
                "", "Sager ring mappings are committed in "
                "eval/run_wind.py's docstring."]
    return write_report(report_name, sections, [])
