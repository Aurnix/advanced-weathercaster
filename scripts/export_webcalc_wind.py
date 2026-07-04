"""Float MLP export of the 6 wind multiclass heads for the web calculator.
Multioutput MLP fit on per-class one-vs-rest teacher logits; per-class
isotonic composed into per-class LUTs; JS normalizes the calibrated
per-class probabilities."""
import json
import numpy as np

from neosager.config import REPO_ROOT, load_config
from neosager.data.stations import load_manifest
from neosager.dataset import load_fold
from neosager.models import gbm
from neosager.models.calibrate import Calibrator
from neosager.models.distill import Binner, LUT_SIZE, Z_RANGE
from neosager.models.mlp_export import BIN_KEYS
from neosager.eval.run_wind import _join
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import OneHotEncoder
import pandas as pd

cfg = load_config()
train = load_fold(cfg, "train"); train = train[train["station_fold"] == "train"]
calib = load_fold(cfg, "calib"); calib = calib[calib["station_fold"] == "train"]

lab_dir = cfg.paths.resolved("datasets_dir")
from neosager.climo import split_hash
wind_dir = lab_dir / split_hash(cfg) / "labels_wind"
extra = pd.concat([pd.read_parquet(p) for p in sorted(wind_dir.glob("*.parquet"))])
train = _join(train, extra)
calib = _join(calib, extra)

binner = Binner(train)
dims = binner.dims
BIN_SIZES = [dims.get(k, {"solar8": 8, "wind_rel": 9, "wind_chg": 4,
             "sky": 6, "band": 4, "season": 4, "wclass": 6}.get(k))
             for k in BIN_KEYS]
bt = binner.transform(train); bc = binner.transform(calib)
M_tr = np.column_stack([bt[k] for k in BIN_KEYS])
M_cal = np.column_stack([bc[k] for k in BIN_KEYS])

rng = np.random.default_rng(11)
sub = rng.choice(len(train), size=min(2_000_000, len(train)), replace=False)
cats = [np.arange(s) for s in BIN_SIZES]
enc = OneHotEncoder(categories=cats, handle_unknown="ignore",
                    sparse_output=True).fit(M_tr[sub])
X_tr = enc.transform(M_tr[sub]); X_cal = enc.transform(M_cal)

out = {"heads": {}}
models_dir = cfg.paths.resolved("models_dir") / "gbm_wind"
for kind, K in [("windband", 5), ("winddir", 6)]:
    for L in [6, 12, 24]:
        tgt = f"{kind}_{L}h"
        booster = gbm.load(models_dir / f"{tgt}.txt")
        P = np.clip(gbm.predict(booster, train.iloc[sub]), 1e-4, 1 - 1e-4)
        Z = np.log(P / (1 - P))                      # per-class OVR logits
        mlp = MLPRegressor(hidden_layer_sizes=(16, 12), max_iter=80,
                           early_stopping=False, random_state=0)
        mlp.fit(X_tr, Z)
        Zc = mlp.predict(X_cal)
        y_cal = calib[tgt].to_numpy()
        luts = []
        z_grid = np.linspace(-Z_RANGE, Z_RANGE, LUT_SIZE)
        for k in range(K):
            yk = np.where(np.isnan(y_cal), np.nan, (y_cal == k).astype(float))
            cal = Calibrator().fit(1 / (1 + np.exp(-Zc[:, k])), yk)
            luts.append(np.round(
                cal.transform(1 / (1 + np.exp(-z_grid))), 4).tolist())
        W1, W2, W3 = mlp.coefs_
        b1, b2, b3 = mlp.intercepts_
        out["heads"][tgt] = {
            "K": K,
            "W1": np.round(W1, 5).tolist(), "b1": np.round(b1, 5).tolist(),
            "W2": np.round(W2, 5).tolist(), "b2": np.round(b2, 5).tolist(),
            "W3": np.round(W3, 5).tolist(), "b3": np.round(b3, 5).tolist(),
            "luts": luts}
        print(f"exported {tgt}", flush=True)

path = REPO_ROOT / "webcalc" / "neosager_wind.js"
with open(path, "w", encoding="utf-8") as f:
    f.write("const NEOSAGER_WIND = " + json.dumps(out) + ";\n")
print(f"wrote {path} ({path.stat().st_size/1024:.0f} KB)")
