"""Ablations (plan §Eval):

A. Feature tiers on the precip heads — pressure-only vs +auto(temp) vs
   +manual(user inputs). Quantifies what the watch's manual-entry UX buys.
B. Tide correction on/off — precip + pfall heads, trained on the _notide
   dataset variant (config_notide.yaml), scored on identical test rows.
C. Missing-input robustness — the saved full models scored with manual
   inputs masked at 0/50/100% (seeded, reproducible).

All scores are BSS vs station climatology on cell A (train stations,
2020-2024).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..baselines.climatology import ClimatologyBaseline
from ..config import Config, load_config, REPO_ROOT
from ..dataset import load_fold
from ..features import mask_manual_inputs
from ..models import gbm
from ..models.calibrate import Calibrator
from .metrics import brier_skill
from .report import write_report

PRESSURE_ONLY = ["slp", "d1h", "d3h", "d6h", "d12h", "curv3h", "hf_var",
                 "doy_sin", "doy_cos", "solar_sin", "solar_cos",
                 "lat", "lon", "lat_band", "slp_source"]
PLUS_AUTO = PRESSURE_ONLY + ["temp_c"]
FULL = gbm.FEATURES

TIERS = [("pressure_only", PRESSURE_ONLY), ("plus_auto", PLUS_AUTO),
         ("full_manual", FULL)]

PRECIP = ["precip_6h", "precip_12h", "precip_24h"]
TIDE_TARGETS = PRECIP + ["pfall_6h", "pfall_12h", "pfall_24h"]


def _folds(cfg: Config):
    train = load_fold(cfg, "train")
    train = train[train["station_fold"] == "train"]
    val = load_fold(cfg, "val")
    val = val[val["station_fold"] == "train"]
    calib = load_fold(cfg, "calib")
    calib = calib[calib["station_fold"] == "train"]
    test = load_fold(cfg, "test")
    cell_a = test[test["station_fold"] == "train"]
    return train, val, calib, cell_a


def _train_score(train, val, calib, cell_a, climo, target, features) -> float:
    booster = gbm.train_binary(train, val, target, features=features)
    cal = Calibrator().fit(gbm.predict(booster, calib, features),
                           calib[target].to_numpy())
    p = cal.transform(gbm.predict(booster, cell_a, features))
    months = cell_a.index.month.to_numpy()
    p_ref = climo.predict(cell_a["station_id"], months, target,
                          cell_a["regime"])
    return brier_skill(cell_a[target].to_numpy(), p, p_ref)


def run(manifest: pd.DataFrame, report_name: str) -> Path:
    cfg = load_config()
    train, val, calib, cell_a = _folds(cfg)
    climo = ClimatologyBaseline(cfg, manifest)
    rows = []

    # --- A: feature tiers ---
    for tier_name, feats in TIERS:
        for tgt in PRECIP:
            print(f"[tiers] {tier_name} {tgt}", flush=True)
            bss = _train_score(train, val, calib, cell_a, climo, tgt, feats)
            rows.append({"ablation": "feature_tier", "variant": tier_name,
                         "target": tgt, "bss": bss})

    # --- C: missing-input robustness (saved full models) ---
    models_dir = cfg.paths.resolved("models_dir") / "gbm_m1"
    rng = np.random.default_rng(2027)
    mask50 = rng.random(len(cell_a)) < 0.5
    variants = {"mask_0pct": cell_a,
                "mask_50pct": mask_manual_inputs(cell_a, mask50),
                "mask_100pct": mask_manual_inputs(
                    cell_a, np.ones(len(cell_a), dtype=bool))}
    months = cell_a.index.month.to_numpy()
    for tgt in PRECIP + ["windup_12h", "pfall_12h"]:
        booster = gbm.load(models_dir / f"{tgt}.txt")
        cal = Calibrator().fit(gbm.predict(booster, calib),
                               calib[tgt].to_numpy())
        p_ref = climo.predict(cell_a["station_id"], months, tgt,
                              cell_a["regime"])
        y = cell_a[tgt].to_numpy()
        for vname, vdf in variants.items():
            p = cal.transform(gbm.predict(booster, vdf))
            rows.append({"ablation": "missing_inputs", "variant": vname,
                         "target": tgt, "bss": brier_skill(y, p, p_ref)})
            print(f"[robustness] {vname} {tgt}", flush=True)

    # --- B: tide on/off (uses the _notide dataset built beforehand) ---
    cfg_nt = load_config(REPO_ROOT / "config" / "config_notide.yaml")
    train_nt, val_nt, calib_nt, cell_a_nt = _folds(cfg_nt)
    climo_nt = ClimatologyBaseline(cfg_nt, manifest)
    for tgt in TIDE_TARGETS:
        print(f"[tide] off {tgt}", flush=True)
        bss_off = _train_score(train_nt, val_nt, calib_nt, cell_a_nt,
                               climo_nt, tgt, FULL)
        rows.append({"ablation": "tide", "variant": "off", "target": tgt,
                     "bss": bss_off})
    # tide-ON numbers: precip heads reuse the full_manual tier results
    # (identical training run); pfall heads need a fresh tide-on run
    rows += [{"ablation": "tide", "variant": "on", "target": r["target"],
              "bss": r["bss"]}
             for r in rows
             if r["ablation"] == "feature_tier"
             and r["variant"] == "full_manual"]
    for tgt in ["pfall_6h", "pfall_12h", "pfall_24h"]:
        print(f"[tide] on {tgt}", flush=True)
        bss_on = _train_score(train, val, calib, cell_a, climo, tgt, FULL)
        rows.append({"ablation": "tide", "variant": "on", "target": tgt,
                     "bss": bss_on})

    res = pd.DataFrame(rows)
    res.to_csv(Path("D:/OneDrive/Desktop/neosager/reports")
               / f"{report_name}_results.csv", index=False)

    sections = []
    for abl, title in [("feature_tier", "Feature tiers (what manual inputs buy)"),
                       ("missing_inputs", "Missing-input robustness"),
                       ("tide", "Tide correction on/off")]:
        piv = res[res["ablation"] == abl].pivot_table(
            index="target", columns="variant", values="bss")
        sections += [f"## {title}", "", piv.to_markdown(floatfmt=".3f"), ""]
    return write_report(report_name, sections,
                        [{"metric": "bss", "value": r["bss"],
                          "target": r["target"], "model": r["variant"]}
                         for r in rows])
