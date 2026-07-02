"""Distill all 9 binary heads from the saved GBMs, measure the skill-vs-KB
curve (GBM -> float additive -> int8 quantized), and write the packed
artifact. Scores on cell A, BSS vs station climatology, identical rows."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..baselines.climatology import ClimatologyBaseline
from ..config import Config
from ..dataset import load_fold
from ..models import gbm
from ..models.calibrate import Calibrator
from ..models.distill import (AdditiveTable, Binner, LUT_SIZE, PFALL_SPEC,
                              Z_RANGE, make_prob_lut, lut_lookup)
from .metrics import brier_skill
from .report import write_report

REPO = Path("D:/OneDrive/Desktop/neosager")
TARGETS = [f"{p}_{L}h" for p in ["precip", "windup", "pfall"]
           for L in [6, 12, 24]]


def run(cfg: Config, manifest: pd.DataFrame, report_name: str) -> Path:
    train = load_fold(cfg, "train")
    train = train[train["station_fold"] == "train"]
    calib = load_fold(cfg, "calib")
    calib = calib[calib["station_fold"] == "train"]
    test = load_fold(cfg, "test")
    cell_a = test[test["station_fold"] == "train"]
    climo = ClimatologyBaseline(cfg, manifest)
    models_dir = cfg.paths.resolved("models_dir") / "gbm_m1"

    binner = Binner(train)
    bins_train = binner.transform(train)
    bins_calib = binner.transform(calib)
    bins_a = binner.transform(cell_a)
    months = cell_a.index.month.to_numpy()

    artifact = {"heads": {}, "meta": {
        "logit_scale": 16, "z_range": Z_RANGE, "lut_size": LUT_SIZE,
        "slp_edges": binner.slp_edges.tolist(),
        "d3h_edges": binner.d3h_edges.tolist(),
        "d12h_edges": binner.d12h_edges.tolist()}}
    rows = []
    total_bytes = 0

    for tgt in TARGETS:
        print(f"distilling {tgt}...", flush=True)
        booster = gbm.load(models_dir / f"{tgt}.txt")
        p_teacher = np.clip(gbm.predict(booster, train), 1e-4, 1 - 1e-4)
        z_teacher = np.log(p_teacher / (1 - p_teacher))

        is_pfall = tgt.startswith("pfall")
        table = AdditiveTable(
            binner, spec=PFALL_SPEC if is_pfall else None,
            linear=is_pfall).fit(train, z_teacher)
        lin_c = table._lin_matrix(calib) if is_pfall else None
        lin_a = table._lin_matrix(cell_a) if is_pfall else None

        # per-variant scoring
        y = cell_a[tgt].to_numpy()
        p_ref = climo.predict(cell_a["station_id"], months, tgt,
                              cell_a["regime"])
        p_gbm_cal = Calibrator().fit(
            gbm.predict(booster, calib), calib[tgt].to_numpy()
        ).transform(gbm.predict(booster, cell_a))

        variants = {}
        # float additive + isotonic on calib
        z_cal = table.predict_logit(bins_calib, lin_c)
        cal_f = Calibrator().fit(1 / (1 + np.exp(-z_cal)),
                                 calib[tgt].to_numpy())
        variants["additive_float"] = cal_f.transform(
            1 / (1 + np.exp(-table.predict_logit(bins_a, lin_a))))
        # quantized int8 + composed LUT
        z_grid = np.linspace(-Z_RANGE, Z_RANGE, LUT_SIZE)
        zq_cal = table.predict_logit_quantized(bins_calib, lin_c)
        cal_q = Calibrator().fit(1 / (1 + np.exp(-zq_cal)),
                                 calib[tgt].to_numpy())
        lut = make_prob_lut(z_grid, cal_q)
        variants["quantized_int8"] = lut_lookup(
            table.predict_logit_quantized(bins_a, lin_a), lut)

        bss_gbm = brier_skill(y, p_gbm_cal, p_ref)
        row = {"target": tgt, "bss_gbm": bss_gbm}
        for vname, p in variants.items():
            row[f"bss_{vname}"] = brier_skill(y, p, p_ref)
        rows.append(row)

        q = table.quantize()
        head_bytes = (sum(t.size for t in q["tables"].values()) + 2
                      + LUT_SIZE + (8 if is_pfall else 0))
        total_bytes += head_bytes
        artifact["heads"][tgt] = {
            "tables": {k: v.tolist() for k, v in q["tables"].items()},
            "bias": q["bias"], "lut": lut.tolist(), "bytes": head_bytes,
            "lin_w_q": q["lin_w_q"].tolist() if is_pfall else None,
            "spec": [name for name, _ in table.spec]}
        print(f"  {tgt}: GBM {bss_gbm:.3f} -> float "
              f"{row['bss_additive_float']:.3f} -> int8 "
              f"{row['bss_quantized_int8']:.3f} ({head_bytes} B)", flush=True)

    edges_bytes = 2 * (len(binner.slp_edges) + len(binner.d3h_edges)
                       + len(binner.d12h_edges))
    artifact["meta"]["total_bytes"] = total_bytes + edges_bytes
    out_json = cfg.paths.resolved("artifacts_dir") / "neosager_tables.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(artifact, f)

    res = pd.DataFrame(rows)
    res.to_csv(REPO / "reports" / f"{report_name}_results.csv", index=False)
    sections = [
        "## Skill retained through distillation (cell A, BSS vs climatology)",
        "", res.to_markdown(index=False, floatfmt=".3f"), "",
        f"**Artifact size: {(total_bytes + edges_bytes)} bytes "
        f"({(total_bytes + edges_bytes) / 1024:.2f} KB) for 9 heads + bin "
        f"edges** (budget: 32-64 KB).", "",
        f"Artifact written to `{out_json}`.",
    ]
    return write_report(report_name, sections,
                        [{"metric": "bss", "value": r.get("bss_quantized_int8"),
                          "target": r["target"], "model": "distilled"}
                         for r in rows])
