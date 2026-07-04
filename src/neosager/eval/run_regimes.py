"""Per-regime breakout (plan §Eval): where does the learned model gain most
over Sager, and where is skill thin? Scores GBM, calibrated Sager, and
climatology per climate regime on cell A, with paired block-bootstrap CIs
on the GBM-minus-Sager difference per regime."""

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
from .metrics import brier_skill, heidke
from .run_baselines import empirical_rate_by_key
from .report import write_report

from ..config import REPO_ROOT as REPO
TARGETS = ["precip_6h", "precip_12h", "precip_24h", "windup_12h", "pfall_12h"]


def run(cfg: Config, manifest: pd.DataFrame, report_name: str) -> Path:
    train = load_fold(cfg, "train")
    train = train[train["station_fold"] == "train"]
    calib = load_fold(cfg, "calib")
    calib = calib[calib["station_fold"] == "train"]
    test = load_fold(cfg, "test")
    cell_a = test[test["station_fold"] == "train"]

    climo = ClimatologyBaseline(cfg, manifest)
    sager = SagerCaster()
    print("sager on train (for calibration)...", flush=True)
    sager_train = sager.predict_frame(train)
    s_cal = {t: empirical_rate_by_key(sager_train["sager_forecast_idx"],
                                      train[t]) for t in TARGETS}
    del sager_train, train

    print("sager on cell A...", flush=True)
    s_cell = sager.predict_frame(cell_a)
    models_dir = cfg.paths.resolved("models_dir") / "gbm_m1"

    rows = []
    for tgt in TARGETS:
        booster = gbm.load(models_dir / f"{tgt}.txt")
        cal = Calibrator().fit(gbm.predict(booster, calib),
                               calib[tgt].to_numpy())
        p_gbm_all = cal.transform(gbm.predict(booster, cell_a))
        p_sager_all = s_cell["sager_forecast_idx"].map(
            s_cal[tgt]).to_numpy(dtype=float)
        months_all = cell_a.index.month.to_numpy()

        for regime, grp_idx in cell_a.groupby("regime", observed=True).indices.items():
            grp = cell_a.iloc[grp_idx]
            y = grp[tgt].to_numpy()
            p_ref = climo.predict(grp["station_id"],
                                  months_all[grp_idx], tgt, grp["regime"])
            p_g = p_gbm_all[grp_idx]
            p_s = p_sager_all[grp_idx]
            blocks = block_ids(grp["station_id"], grp.index)

            def _diff(idx, y=y, pg=p_g, ps=p_s, r=p_ref):
                return (brier_skill(y[idx], pg[idx], r[idx])
                        - brier_skill(y[idx], ps[idx], r[idx]))
            d, lo, hi = bootstrap_ci(_diff, blocks, len(y), n_boot=300, seed=3)
            rows.append({
                "target": tgt, "regime": regime,
                "n": int((~np.isnan(y)).sum()),
                "base_rate": float(np.nanmean(y)),
                "bss_gbm": brier_skill(y, p_g, p_ref),
                "bss_sager": brier_skill(y, p_s, p_ref),
                "gbm_minus_sager": d, "diff_lo": lo, "diff_hi": hi,
            })
            print(f"  {tgt} {regime}: gbm {rows[-1]['bss_gbm']:.3f} "
                  f"sager {rows[-1]['bss_sager']:.3f}", flush=True)

    res = pd.DataFrame(rows)
    res.to_csv(REPO / "reports" / f"{report_name}_results.csv", index=False)
    sections = []
    for tgt in TARGETS:
        t = res[res["target"] == tgt].sort_values("bss_gbm", ascending=False)
        sections += [f"## {tgt}", "",
                     t.drop(columns="target").to_markdown(
                         index=False, floatfmt=".3f"), ""]
    return write_report(report_name, sections,
                        [{"metric": "bss", "value": r["bss_gbm"],
                          "target": r["target"], "model": "gbm"}
                         for r in rows])
