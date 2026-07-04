"""Skill-vs-lead-time curve, 3-36h, per regime — the project's core
scientific figure: how far out do Sager-class instruments carry useful
information?

Three phases, each resumable:
1. Extra-lead precip labels (3,9,15,...,36h) per station from hourly
   parquet, aligned to the existing dataset example grid.
2. One precip GBM per extra lead (existing 6/12/24h models reused).
3. BSS per lead x regime on cell A + calibrated-Sager and persistence
   reference curves; matplotlib figure + report.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..baselines.climatology import ClimatologyBaseline
from ..baselines.sager import SagerCaster
from ..climo import split_hash
from ..config import Config
from ..dataset import load_fold, load_station_hourly
from ..labels import _forward_any, _gap_violation, precip_evidence
from ..models import gbm
from ..models.calibrate import Calibrator
from ..splits import example_mask
from .metrics import brier_skill
from .run_baselines import empirical_rate_by_key
from .report import write_report

from ..config import REPO_ROOT as REPO
EXTRA_LEADS = [3, 9, 15, 18, 21, 27, 30, 33, 36]
ALL_LEADS = sorted(EXTRA_LEADS + [6, 12, 24])


def _labels_dir(cfg: Config) -> Path:
    d = cfg.paths.resolved("datasets_dir") / split_hash(cfg) / "labels_extra"
    d.mkdir(parents=True, exist_ok=True)
    return d


def build_extra_labels(cfg: Config, manifest: pd.DataFrame) -> None:
    lc = cfg.labels
    out_dir = _labels_dir(cfg)
    for i, sid in enumerate(manifest["station_id"]):
        out = out_dir / f"{sid}.parquet"
        if out.exists():
            continue
        hourly = load_station_hourly(cfg, sid)
        if hourly is None or hourly.empty:
            continue
        observed = (hourly["n_reports"] > 0).to_numpy()
        precip = precip_evidence(hourly).to_numpy().astype(float)
        lab = pd.DataFrame(index=hourly.index)
        for L in EXTRA_LEADS:
            min_obs = int(np.ceil(lc.window_min_coverage * L))
            from ..labels import _forward_sum
            n_obs = _forward_sum(observed.astype(float), L)
            gap_bad = _gap_violation(observed, L, lc.window_max_gap_h)
            pos = _forward_any(precip, L) > 0
            lab[f"precip_{L}h"] = np.where(
                pos, 1.0, np.where((n_obs >= min_obs) & ~gap_bad, 0.0, np.nan))
        keep = example_mask(hourly.index, cfg)
        lab = lab[keep]
        lab["station_id"] = sid
        lab.to_parquet(out)
        if (i + 1) % 25 == 0:
            print(f"  labels_extra {i + 1}/{len(manifest)}", flush=True)


def load_extra_labels(cfg: Config) -> pd.DataFrame:
    frames = [pd.read_parquet(p)
              for p in sorted(_labels_dir(cfg).glob("*.parquet"))]
    df = pd.concat(frames)
    df.index.name = "hour"
    return df


def _join_extra(fold_df: pd.DataFrame, extra: pd.DataFrame) -> pd.DataFrame:
    a = fold_df.reset_index(names="hour")
    b = extra.reset_index()
    merged = a.merge(b, on=["hour", "station_id"], how="left")
    return merged.set_index("hour")


def run(cfg: Config, manifest: pd.DataFrame, report_name: str) -> Path:
    print("phase 1: extra-lead labels", flush=True)
    build_extra_labels(cfg, manifest)
    extra = load_extra_labels(cfg)

    print("phase 2: assemble folds", flush=True)
    train = load_fold(cfg, "train")
    train = _join_extra(train[train["station_fold"] == "train"], extra)
    val = load_fold(cfg, "val")
    val = _join_extra(val[val["station_fold"] == "train"], extra)
    calib = load_fold(cfg, "calib")
    calib = _join_extra(calib[calib["station_fold"] == "train"], extra)
    test = load_fold(cfg, "test")
    cell_a = _join_extra(test[test["station_fold"] == "train"], extra)
    del extra, test

    climo = ClimatologyBaseline(cfg, manifest)
    sager = SagerCaster()
    print("sager frames...", flush=True)
    sager_train_idx = sager.predict_frame(train)["sager_forecast_idx"]
    sager_a_idx = sager.predict_frame(cell_a)["sager_forecast_idx"]
    months = cell_a.index.month.to_numpy()

    models_dir = cfg.paths.resolved("models_dir") / "gbm_leadtime"
    rows = []
    for L in ALL_LEADS:
        tgt = f"precip_{L}h"
        existing = cfg.paths.resolved("models_dir") / "gbm_m1" / f"{tgt}.txt"
        mpath = existing if L in (6, 12, 24) else models_dir / f"{tgt}.txt"
        if mpath.exists():
            booster = gbm.load(mpath)
        else:
            print(f"training {tgt}...", flush=True)
            booster = gbm.train_binary(train, val, tgt)
            gbm.save(booster, mpath)
        cal = Calibrator().fit(gbm.predict(booster, calib),
                               calib[tgt].to_numpy())
        p_g = cal.transform(gbm.predict(booster, cell_a))
        s_rate = empirical_rate_by_key(sager_train_idx, train[tgt])
        p_s = sager_a_idx.map(s_rate).to_numpy(dtype=float)
        # climatology reference at extra leads: month rate of THIS lead's
        # label measured on train (station climo tables only know 6/12/24)
        y = cell_a[tgt].to_numpy()
        # per-station-month climatology from train years for this lead
        tr_key = pd.MultiIndex.from_arrays(
            [train["station_id"], train.index.month])
        rate = train.groupby(
            [train["station_id"], train.index.month])[tgt].mean()
        te_key = pd.MultiIndex.from_arrays(
            [cell_a["station_id"], cell_a.index.month])
        p_ref = rate.reindex(te_key).to_numpy()

        row = {"lead_h": L,
               "bss_gbm": brier_skill(y, p_g, p_ref),
               "bss_sager": brier_skill(y, p_s, p_ref),
               "n": int((~np.isnan(y)).sum())}
        for regime, gidx in cell_a.groupby("regime", observed=True).indices.items():
            row[f"gbm_{regime}"] = brier_skill(
                y[gidx], p_g[gidx], p_ref[gidx])
        rows.append(row)
        print(f"  lead {L}h: gbm {row['bss_gbm']:.3f} "
              f"sager {row['bss_sager']:.3f}", flush=True)

    res = pd.DataFrame(rows).sort_values("lead_h")
    res.to_csv(REPO / "reports" / f"{report_name}_results.csv", index=False)

    # figure: overall + per-regime
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    ax1.plot(res["lead_h"], res["bss_gbm"], "o-",
             label="Advanced Weathercaster (GBM)")
    ax1.plot(res["lead_h"], res["bss_sager"], "s--", label="Sager (calibrated)")
    ax1.axhline(0, color="k", lw=0.8)
    ax1.set_xlabel("lead time (h)")
    ax1.set_ylabel("Brier skill vs station climatology")
    ax1.set_title("P(precip within lead) — all regimes")
    ax1.legend()
    regimes = [c[4:] for c in res.columns if c.startswith("gbm_")]
    for r in regimes:
        ax2.plot(res["lead_h"], res[f"gbm_{r}"], "o-", ms=3, label=r)
    ax2.axhline(0, color="k", lw=0.8)
    ax2.set_xlabel("lead time (h)")
    ax2.set_title("GBM by regime")
    ax2.legend(fontsize=7)
    fig.tight_layout()
    png = REPO / "reports" / "figures" / "leadtime_curves.png"
    png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png, dpi=130)
    plt.close(fig)

    sections = ["## Skill vs lead time (cell A)", "",
                res.to_markdown(index=False, floatfmt=".3f"), "",
                "![](reports/figures/leadtime_curves.png)"]
    return write_report(report_name, sections,
                        [{"metric": "bss", "value": r["bss_gbm"],
                          "target": f"precip_{r['lead_h']}h", "model": "gbm"}
                         for r in rows])
