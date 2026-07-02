"""Train LightGBM models on the train fold (val for early stopping),
calibrate on the calib fold, score on the test cells alongside climatology
and calibrated Sager, with paired block-bootstrap CIs on the GBM-minus-Sager
BSS difference — the project's core comparison.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..baselines.climatology import ClimatologyBaseline
from ..baselines.sager import SagerCaster
from ..config import Config
from ..dataset import load_fold
from ..models import gbm
from ..models.calibrate import Calibrator
from .bootstrap import block_ids, bootstrap_ci
from .metrics import brier_skill, reliability_curve, roc_auc
from .run_baselines import BINARY_TARGETS, empirical_rate_by_key, _split_cells
from .metrics import heidke, peirce
from .report import reliability_figure, write_report

REPO = Path("D:/OneDrive/Desktop/neosager")


def run(cfg: Config, manifest: pd.DataFrame, report_name: str) -> Path:
    train = load_fold(cfg, "train")
    train = train[train["station_fold"] == "train"]
    val = load_fold(cfg, "val")
    val = val[val["station_fold"] == "train"]
    calib = load_fold(cfg, "calib")
    calib = calib[calib["station_fold"] == "train"]
    cells = _split_cells(cfg)
    print(f"train {len(train)} / val {len(val)} / calib {len(calib)}",
          flush=True)

    climo = ClimatologyBaseline(cfg, manifest)
    sager = SagerCaster()
    sager_train = sager.predict_frame(train)
    s_cal = {t: empirical_rate_by_key(sager_train["sager_forecast_idx"],
                                      train[t]) for t in BINARY_TARGETS}

    models_dir = cfg.paths.resolved("models_dir") / "gbm_m1"
    rows, tripwire, figures = [], [], []

    boosters: dict[str, object] = {}
    calibrators: dict[str, Calibrator] = {}
    for tgt in BINARY_TARGETS:
        print(f"training {tgt}...", flush=True)
        booster = gbm.train_binary(train, val, tgt)
        gbm.save(booster, models_dir / f"{tgt}.txt")
        boosters[tgt] = booster
        cal = Calibrator().fit(gbm.predict(booster, calib),
                               calib[tgt].to_numpy())
        calibrators[tgt] = cal

        # val-vs-test sanity for the leakage tripwire
        ok_v = val[tgt].notna()
        p_val = cal.transform(gbm.predict(booster, val[ok_v.to_numpy()]))
        months_v = val.index[ok_v.to_numpy()].month.to_numpy()
        p_ref_v = climo.predict(val.loc[ok_v, "station_id"], months_v, tgt,
                                val.loc[ok_v, "regime"])
        bss_val = brier_skill(val.loc[ok_v, tgt].to_numpy(), p_val, p_ref_v)

        for cell_name, cell in cells.items():
            if cell.empty:
                continue
            y = cell[tgt].to_numpy()
            months = cell.index.month.to_numpy()
            p_ref = climo.predict(cell["station_id"], months, tgt,
                                  cell["regime"])
            p_raw = gbm.predict(booster, cell)
            p = cal.transform(p_raw)
            s_cell = sager.predict_frame(cell)
            p_sager = s_cell["sager_forecast_idx"].map(
                s_cal[tgt]).to_numpy(dtype=float)

            bss = brier_skill(y, p, p_ref)
            row = {"cell": cell_name, "target": tgt, "model": "gbm",
                   "bss": bss, "bss_val": bss_val,
                   "auc": roc_auc(y, p),
                   "n": int((~np.isnan(y) & ~np.isnan(p)).sum())}
            if cell_name.startswith("A"):
                blocks = block_ids(cell["station_id"], cell.index)

                def _diff(idx, y=y, p=p, ps=p_sager, r=p_ref):
                    return (brier_skill(y[idx], p[idx], r[idx])
                            - brier_skill(y[idx], ps[idx], r[idx]))
                d, lo, hi = bootstrap_ci(_diff, blocks, len(y),
                                         n_boot=500, seed=2)
                row["bss_minus_sager"] = d
                row["diff_lo"], row["diff_hi"] = lo, hi

                if tgt == "precip_12h":
                    curves = {
                        "gbm_raw": reliability_curve(y, p_raw),
                        "gbm_calibrated": reliability_curve(y, p),
                        "sager_cal": reliability_curve(y, p_sager),
                        "climatology": reliability_curve(y, p_ref),
                    }
                    png = Path("reports/figures") / f"reliability_gbm_{tgt}.png"
                    reliability_figure(curves, f"{tgt} GBM vs Sager (cell A)",
                                       REPO / png)
                    figures.append(png)
            rows.append(row)
            tripwire.append({"metric": "bss", "value": bss, "target": tgt,
                             "model": "gbm"})

    # 4-class conditions models
    for L in (12, 24):
        print(f"training cond_{L}h...", flush=True)
        booster = gbm.train_conditions(train, val, L)
        gbm.save(booster, models_dir / f"cond_{L}h.txt")
        for cell_name, cell in cells.items():
            if cell.empty:
                continue
            y = cell[f"cond_{L}h"].to_numpy()
            f = np.argmax(gbm.predict(booster, cell), axis=1).astype(float)
            rows.append({"cell": cell_name, "target": f"cond_{L}h",
                         "model": "gbm", "heidke": heidke(y, f),
                         "peirce": peirce(y, f),
                         "n": int((~np.isnan(y)).sum())})

    res = pd.DataFrame(rows)
    res.to_csv(REPO / "reports" / f"{report_name}_results.csv", index=False)

    a = res[(res["cell"] == "A_trainstation_testyears")
            & res["target"].isin(BINARY_TARGETS)]
    sections = [
        "## GBM vs calibrated Sager — BSS vs climatology "
        "(cell A, 2020-2024)", "",
        a[["target", "bss", "bss_val", "auc", "bss_minus_sager",
           "diff_lo", "diff_hi", "n"]].to_markdown(index=False,
                                                   floatfmt=".3f"), "",
        "`bss_minus_sager` is the paired block-bootstrap difference; the "
        "CI excludes 0 when the GBM's edge over Sager is significant.", "",
        "## Conditions (Heidke/Peirce)", "",
        res[res["target"].str.startswith("cond_")].to_markdown(
            index=False, floatfmt=".3f"), "",
        "## All cells", "",
        res[res["target"].isin(BINARY_TARGETS)].to_markdown(
            index=False, floatfmt=".3f"), "",
        "## Reliability", "",
    ] + [f"![]({p.as_posix()})" for p in figures]
    return write_report(report_name, sections, tripwire)
