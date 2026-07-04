"""Build the final Option-B MLP artifact: train 9 heads, quantize with
power-of-2 scales, compose isotonic into LUTs, verify skill of the
INTEGER-EXACT forward pass, write neosager_mlp.json."""
import json
import numpy as np
import pandas as pd

from neosager.config import REPO_ROOT, load_config
from neosager.data.stations import load_manifest
from neosager.dataset import load_fold
from neosager.baselines.climatology import ClimatologyBaseline
from neosager.models import gbm
from neosager.models.calibrate import Calibrator
from neosager.models.distill import Binner, LUT_SIZE, Z_RANGE, make_prob_lut, lut_lookup
from neosager.models.mlp_export import (BIN_KEYS, predict_quantized,
                                        quantize_head, train_head)
from neosager.eval.metrics import brier_skill
from sklearn.preprocessing import OneHotEncoder

cfg = load_config()
manifest = load_manifest(REPO_ROOT / "config" / "stations_full.yaml")
train = load_fold(cfg, "train"); train = train[train["station_fold"] == "train"]
calib = load_fold(cfg, "calib"); calib = calib[calib["station_fold"] == "train"]
test = load_fold(cfg, "test"); cell_a = test[test["station_fold"] == "train"]
climo = ClimatologyBaseline(cfg, manifest)
months_a = cell_a.index.month.to_numpy()

binner = Binner(train)
bins_tr_d = binner.transform(train)
bins_cal_d = binner.transform(calib)
bins_a_d = binner.transform(cell_a)
dims = binner.dims
BIN_SIZES = [dims[k] if k in dims else {"solar8": 8, "wind_rel": 9,
             "wind_chg": 4, "sky": 6, "band": 4, "season": 4,
             "wclass": 6}[k] for k in BIN_KEYS]

M_tr = np.column_stack([bins_tr_d[k] for k in BIN_KEYS])
M_cal = np.column_stack([bins_cal_d[k] for k in BIN_KEYS])
M_a = np.column_stack([bins_a_d[k] for k in BIN_KEYS])

rng = np.random.default_rng(11)
sub = rng.choice(len(train), size=min(2_000_000, len(train)), replace=False)
cats = [np.arange(s) for s in BIN_SIZES]
enc = OneHotEncoder(categories=cats, handle_unknown="ignore",
                    sparse_output=True).fit(M_tr[sub])
X_tr = enc.transform(M_tr[sub])

artifact = {"heads": {}, "meta": {
    "bin_keys": BIN_KEYS, "bin_sizes": BIN_SIZES,
    "lut_size": LUT_SIZE, "z_range": Z_RANGE,
    "slp_edges": binner.slp_edges.tolist(),
    "d3h_edges": binner.d3h_edges.tolist(),
    "d12h_edges": binner.d12h_edges.tolist(),
    "d6h_edges": binner.d6h_edges.tolist(),
    "d1h_edges": binner.d1h_edges.tolist(),
    "hf_edges": binner.hf_edges.tolist(),
    "curv_edges": binner.curv_edges.tolist()}}

models_dir = cfg.paths.resolved("models_dir") / "gbm_m1"
total = 0
rows = []
for tgt in [f"{a}_{b}h" for a in ("precip", "windup", "pfall") for b in (6, 12, 24)]:
    booster = gbm.load(models_dir / f"{tgt}.txt")
    p_t = np.clip(gbm.predict(booster, train.iloc[sub]), 1e-4, 1 - 1e-4)
    mlp = train_head(X_tr, np.log(p_t / (1 - p_t)))
    head = quantize_head(mlp, BIN_SIZES)

    z_cal = predict_quantized(head, M_cal)
    cal = Calibrator().fit(1 / (1 + np.exp(-z_cal)), calib[tgt].to_numpy())
    z_grid = np.linspace(-Z_RANGE, Z_RANGE, LUT_SIZE)
    lut = make_prob_lut(z_grid, cal)
    head["lut"] = lut.tolist()

    z_a = predict_quantized(head, M_a)
    p_a = lut_lookup(np.clip(z_a, -Z_RANGE, Z_RANGE), lut)
    y = cell_a[tgt].to_numpy()
    p_ref = climo.predict(cell_a["station_id"], months_a, tgt, cell_a["regime"])
    bss = brier_skill(y, p_a, p_ref)
    total += head["bytes"]
    artifact["heads"][tgt] = head
    rows.append({"target": tgt, "bss_mlp_int": round(bss, 3),
                 "bytes": head["bytes"]})
    print(f"  {tgt}: int-exact MLP BSS {bss:.3f} ({head['bytes']} B)", flush=True)

artifact["meta"]["total_bytes"] = total
out = cfg.paths.resolved("artifacts_dir") / "neosager_mlp.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(artifact, f)
print(f"TOTAL {total} bytes ({total/1024:.1f} KB) -> {out}")
pd.DataFrame(rows).to_csv(REPO_ROOT / "reports" / "mlp_artifact_results.csv",
                          index=False)
