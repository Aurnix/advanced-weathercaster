"""Milestone-1 baseline scoring: climatology, persistence, Zambretti
(faithful + calibrated), Sager (faithful + calibrated), logistic regression —
all on identical test rows, with block-bootstrap CIs and reliability figures.

Test cells reported separately:
  A = train-stations x test-years (headline)
  B = test-stations  x train-years is not materialized (train-station files
      only contain train rows for the train fold) — cell B comes from the
      test-station files' train/val/calib-year rows.
  C = test-stations  x test-years.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..baselines.climatology import ClimatologyBaseline
from ..baselines.logreg import fit_predict as logreg_fit_predict
from ..baselines.persistence import (persistence_conditions,
                                     persistence_pfall, persistence_precip,
                                     persistence_windup)
from ..baselines.sager import SagerCaster
from ..baselines.zambretti import Z_TO_CLASS4, zambretti_from_features
from ..config import Config
from ..dataset import load_fold
from .bootstrap import block_ids, bootstrap_ci
from .metrics import (brier, brier_skill, heidke, peirce, reliability_curve,
                      roc_auc)
from .report import reliability_figure, write_report

BINARY_TARGETS = [f"{p}_{L}h" for p in ["precip", "windup", "pfall"]
                  for L in [6, 12, 24]]


def empirical_rate_by_key(train_key: pd.Series, train_y: pd.Series,
                          min_n: int = 50) -> dict:
    """Calibrated-variant helper: P(event | discrete forecast key), train
    years only."""
    df = pd.DataFrame({"k": train_key, "y": train_y}).dropna()
    g = df.groupby("k")["y"].agg(["mean", "size"])
    overall = df["y"].mean()
    return {k: (row["mean"] if row["size"] >= min_n else overall)
            for k, row in g.iterrows()}


def _split_cells(cfg: Config) -> dict[str, pd.DataFrame]:
    test_rows = load_fold(cfg, "test")
    cells = {
        "A_trainstation_testyears":
            test_rows[test_rows["station_fold"] == "train"],
        "C_teststation_testyears":
            test_rows[test_rows["station_fold"] == "test"],
    }
    # cell B: test stations, train-era years (train fold rows of test stations)
    train_rows = load_fold(cfg, "train")
    cells["B_teststation_trainyears"] = \
        train_rows[train_rows["station_fold"] == "test"]
    return cells


def run(cfg: Config, manifest: pd.DataFrame, report_name: str) -> Path:
    train = load_fold(cfg, "train")
    train = train[train["station_fold"] == "train"]
    cells = _split_cells(cfg)
    print(f"train rows: {len(train)}; cells: "
          f"{ {k: len(v) for k, v in cells.items()} }", flush=True)

    climo = ClimatologyBaseline(cfg, manifest)
    sager = SagerCaster()

    # fit calibrated Zambretti / Sager on train rows
    z_train = zambretti_from_features(train)
    sager_train = sager.predict_frame(train)
    z_cal = {}
    s_cal = {}
    for tgt in BINARY_TARGETS:
        z_cal[tgt] = empirical_rate_by_key(z_train, train[tgt])
        s_cal[tgt] = empirical_rate_by_key(sager_train["sager_forecast_idx"],
                                           train[tgt])

    print("fitting logistic regression...", flush=True)
    # sklearn's one-hot pipeline is the memory hog of this run; 5M rows is
    # far past the logreg learning curve plateau
    lr_train = (train.sample(5_000_000, random_state=42)
                if len(train) > 5_000_000 else train)
    logreg_preds = logreg_fit_predict(lr_train, BINARY_TARGETS, cells)

    rows = []          # long-form results
    tripwire = []
    figures = []

    for cell_name, cell in cells.items():
        if cell.empty:
            continue
        months = cell.index.month.to_numpy()
        blocks = block_ids(cell["station_id"], cell.index)
        z_cell = zambretti_from_features(cell)
        s_cell = sager.predict_frame(cell)

        preds_by_target: dict[str, dict[str, np.ndarray]] = {}
        for tgt in BINARY_TARGETS:
            p_climo = climo.predict(cell["station_id"], months, tgt,
                                    cell["regime"])
            kind = tgt.split("_")[0]
            pers = {"precip": persistence_precip, "pfall": persistence_pfall,
                    "windup": persistence_windup}[kind](cell)
            preds = {
                "climatology": p_climo,
                "persistence": pers,
                "zambretti_cal": z_cell.map(z_cal[tgt]).to_numpy(dtype=float),
                "sager_cal": s_cell["sager_forecast_idx"].map(
                    s_cal[tgt]).to_numpy(dtype=float),
                "logreg": logreg_preds[tgt][cell_name],
            }
            if kind == "precip":
                preds["sager_faithful"] = s_cell["sager_precip"].to_numpy()
            if kind == "windup":
                preds["sager_faithful"] = s_cell["sager_windup"].to_numpy()
            preds_by_target[tgt] = preds

            y = cell[tgt].to_numpy()
            for model, p in preds.items():
                bs = brier(y, p)
                bss = brier_skill(y, p, p_climo)
                auc = roc_auc(y, p)
                row = {"cell": cell_name, "target": tgt, "model": model,
                       "brier": bs, "bss": bss, "auc": auc,
                       "n": int((~np.isnan(y) & ~np.isnan(p)).sum())}
                # bootstrap CI on BSS for the headline cell only (cost)
                if cell_name.startswith("A") and model in (
                        "logreg", "zambretti_cal", "sager_cal"):
                    def _m(idx, y=y, p=p, r=p_climo):
                        return brier_skill(y[idx], p[idx], r[idx])
                    _, lo, hi = bootstrap_ci(_m, blocks, len(y),
                                             n_boot=500, seed=1)
                    row["bss_lo"], row["bss_hi"] = lo, hi
                rows.append(row)
                tripwire.append({"metric": "bss", "value": bss,
                                 "target": tgt, "model": model})

        # categorical comparison at 12h and 24h
        for L in (12, 24):
            y_cls = cell[f"cond_{L}h"].to_numpy()
            f_pers = persistence_conditions(cell)
            f_zam = pd.Series(z_cell).map(Z_TO_CLASS4).to_numpy(dtype=float)
            f_sag = s_cell["sager_class4"].to_numpy(dtype=float)
            for model, f in [("persistence", f_pers), ("zambretti", f_zam),
                             ("sager", f_sag)]:
                rows.append({"cell": cell_name, "target": f"cond_{L}h",
                             "model": model,
                             "heidke": heidke(y_cls, f),
                             "peirce": peirce(y_cls, f),
                             "n": int((~np.isnan(y_cls) & ~np.isnan(f)).sum())})

        # reliability figure for the headline target
        if cell_name.startswith("A"):
            curves = {m: reliability_curve(cell["precip_12h"].to_numpy(), p)
                      for m, p in preds_by_target["precip_12h"].items()
                      if m != "persistence"}
            png = Path("reports") / "figures" / f"reliability_precip12_{cell_name}.png"
            reliability_figure(curves, f"precip_12h — {cell_name}",
                               Path("D:/OneDrive/Desktop/neosager") / png)
            figures.append(png)

    res = pd.DataFrame(rows)
    res_path = Path("D:/OneDrive/Desktop/neosager/reports") / f"{report_name}_results.csv"
    res_path.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(res_path, index=False)

    sections = ["## Headline: BSS vs station climatology "
                "(cell A: train stations, 2020-2024)", ""]
    a = res[(res["cell"] == "A_trainstation_testyears")
            & res["target"].isin(BINARY_TARGETS)]
    piv = a.pivot_table(index="target", columns="model", values="bss")
    sections += [piv.to_markdown(floatfmt=".3f"), ""]
    sections += ["## Categorical skill (Heidke / Peirce)", ""]
    c = res[res["target"].str.startswith("cond_")]
    sections += [c.to_markdown(index=False, floatfmt=".3f"), ""]
    sections += ["## Reliability (headline cell)", ""]
    sections += [f"![]({p.as_posix()})" for p in figures]
    sections += ["", "## All cells (full table)", "",
                 res[res["target"].isin(BINARY_TARGETS)]
                 .to_markdown(index=False, floatfmt=".3f")]
    return write_report(report_name, sections, tripwire)
