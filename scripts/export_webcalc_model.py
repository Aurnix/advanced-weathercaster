"""Export FLOAT (non-quantized) MLP heads for the web calculator:
weights, bin edges, and a per-head float z->prob calibration LUT."""
import json
import numpy as np

from neosager.config import REPO_ROOT, load_config
from neosager.data.stations import load_manifest
from neosager.dataset import load_fold
from neosager.models import gbm
from neosager.models.calibrate import Calibrator
from neosager.models.distill import Binner, LUT_SIZE, Z_RANGE
from neosager.models.mlp_export import BIN_KEYS, train_head
from sklearn.preprocessing import OneHotEncoder

cfg = load_config()
train = load_fold(cfg, "train"); train = train[train["station_fold"] == "train"]
calib = load_fold(cfg, "calib"); calib = calib[calib["station_fold"] == "train"]

binner = Binner(train)
dims = binner.dims
BIN_SIZES = [dims[k] if k in dims else {"solar8": 8, "wind_rel": 9,
             "wind_chg": 4, "sky": 6, "band": 4, "season": 4,
             "wclass": 6}[k] for k in BIN_KEYS]

bins_tr = binner.transform(train)
bins_cal = binner.transform(calib)
M_tr = np.column_stack([bins_tr[k] for k in BIN_KEYS])
M_cal = np.column_stack([bins_cal[k] for k in BIN_KEYS])

rng = np.random.default_rng(11)
sub = rng.choice(len(train), size=min(2_000_000, len(train)), replace=False)
cats = [np.arange(s) for s in BIN_SIZES]
enc = OneHotEncoder(categories=cats, handle_unknown="ignore",
                    sparse_output=True).fit(M_tr[sub])
X_tr = enc.transform(M_tr[sub])
X_cal = enc.transform(M_cal)

out = {"bin_keys": BIN_KEYS, "bin_sizes": BIN_SIZES,
       "edges": {k: getattr(binner, f"{k}_edges").tolist()
                 for k in ["slp", "d3h", "d12h", "d6h", "d1h", "hf", "curv"]},
       "z_range": Z_RANGE, "lut_size": LUT_SIZE, "heads": {}}

models_dir = cfg.paths.resolved("models_dir") / "gbm_m1"
for tgt in [f"{a}_{b}h" for a in ("precip", "windup", "pfall") for b in (6, 12, 24)]:
    booster = gbm.load(models_dir / f"{tgt}.txt")
    p_t = np.clip(gbm.predict(booster, train.iloc[sub]), 1e-4, 1 - 1e-4)
    mlp = train_head(X_tr, np.log(p_t / (1 - p_t)))

    z_cal = mlp.predict(X_cal)
    cal = Calibrator().fit(1 / (1 + np.exp(-z_cal)), calib[tgt].to_numpy())
    z_grid = np.linspace(-Z_RANGE, Z_RANGE, LUT_SIZE)
    p_grid = cal.transform(1 / (1 + np.exp(-z_grid)))

    W1, W2, w3 = mlp.coefs_
    b1, b2, b3 = mlp.intercepts_
    out["heads"][tgt] = {
        "W1": np.round(W1, 5).tolist(), "b1": np.round(b1, 5).tolist(),
        "W2": np.round(W2, 5).tolist(), "b2": np.round(b2, 5).tolist(),
        "w3": np.round(w3.ravel(), 5).tolist(), "b3": round(float(b3[0]), 5),
        "lut": np.round(p_grid, 4).tolist(),
    }
    print(f"exported {tgt}", flush=True)

path = REPO_ROOT / "webcalc" / "neosager_float.json"
path.parent.mkdir(exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
    json.dump(out, f)
print(f"wrote {path} ({path.stat().st_size/1024:.0f} KB)")

# reference vectors for the JS implementation test
wet_bins = {"slp": 1, "d3h": 0, "d6h": 0, "d12h": 0, "d1h": 0, "hf": 3,
            "curv": 0, "solar8": 4, "wind_rel": 2, "wind_chg": 0, "sky": 3,
            "band": 1, "season": 0, "wclass": 2}
dry_bins = {"slp": 7, "d3h": 6, "d6h": 5, "d12h": 4, "d1h": 4, "hf": 0,
            "curv": 4, "solar8": 4, "wind_rel": 4, "wind_chg": 1, "sky": 0,
            "band": 1, "season": 2, "wclass": 1}
for name, bd in [("wet", wet_bins), ("dry", dry_bins)]:
    row = np.array([[bd[k] for k in BIN_KEYS]])
    X = enc.transform(row)
    for tgt in ["precip_12h"]:
        h = out["heads"][tgt]
        z = mlp.predict(X)  # placeholder; recompute per-head below
    # manual forward with exported weights for exactness
    for tgt in ["precip_12h", "pfall_12h"]:
        h = out["heads"][tgt]
        offs = np.concatenate([[0], np.cumsum(BIN_SIZES)[:-1]])
        a1 = np.asarray(h["b1"], float).copy()
        for f_i, k in enumerate(BIN_KEYS):
            a1 += np.asarray(h["W1"], float)[offs[f_i] + bd[k]]
        a1 = np.maximum(a1, 0)
        a2 = np.maximum(np.asarray(h["W2"], float).T @ a1
                        + np.asarray(h["b2"], float), 0)
        z = float(np.asarray(h["w3"], float) @ a2 + h["b3"])
        print(f"REF {name} {tgt}: z={z:.4f}")
