"""M4 finalization: (1) verbal-threshold verification of the distilled
artifact's precip probs on cell A; (2) MLP Option-B skill-per-KB comparison
against the additive tables."""
import json
import numpy as np
import pandas as pd

from neosager.config import REPO_ROOT, load_config
from neosager.data.stations import load_manifest
from neosager.dataset import load_fold
from neosager.baselines.climatology import ClimatologyBaseline
from neosager.models import gbm
from neosager.models.calibrate import Calibrator
from neosager.models.distill import Binner, LUT_SIZE, Z_RANGE
from neosager.eval.metrics import brier_skill

cfg = load_config()
manifest = load_manifest(REPO_ROOT / "config" / "stations_full.yaml")

with open("D:/neosager-data/artifacts/neosager_tables.json", encoding="utf-8") as f:
    art = json.load(f)

train = load_fold(cfg, "train")
train = train[train["station_fold"] == "train"]
calib = load_fold(cfg, "calib")
calib = calib[calib["station_fold"] == "train"]
test = load_fold(cfg, "test")
cell_a = test[test["station_fold"] == "train"]

binner = Binner(train)   # deterministic re-fit of the committed quantiles
bins_a = binner.transform(cell_a)

SPEC_KEYS = {
    "t_slp_d3h": ("slp", "d3h"), "t_trend": ("d3h", "d6h"),
    "t_fine": ("d1h", "d3h", "d6h"), "t_d12h": ("d12h",),
    "t_hf": ("hf",), "t_curv": ("curv",), "t_solar": ("solar8", "band"),
    "t_wind": ("wind_rel", "wind_chg"), "t_wclass": ("wclass",),
    "t_sky": ("sky",), "t_geo": ("band", "season"),
}


def artifact_probs(tgt, bins, df):
    h = art["heads"][tgt]
    z = np.full(len(df), h["bias"], dtype=np.int64)
    for name in h["spec"]:
        t = np.asarray(h["tables"][name])
        keys = SPEC_KEYS[name]
        idx = bins[keys[0]]
        for k, s in zip(keys[1:], t.shape[1:]):
            idx = idx * s + bins[k]
        z = z + t.ravel()[idx]
    zf = z / 16.0
    if h.get("lin_w_q"):
        lin = np.nan_to_num(df[["d1h", "d3h", "d6h", "d12h"]].to_numpy(float))
        zf = zf + lin @ (np.asarray(h["lin_w_q"]) / 256.0)
    pos = np.clip((zf + Z_RANGE) / (2 * Z_RANGE) * (LUT_SIZE - 1), 0, LUT_SIZE - 1)
    lo = np.floor(pos).astype(int)
    hi = np.minimum(lo + 1, LUT_SIZE - 1)
    frac = pos - lo
    lut = np.asarray(h["lut"], dtype=float)
    return (lut[lo] * (1 - frac) + lut[hi] * frac) / 255.0

print("=== VERBAL THRESHOLD VERIFICATION (distilled artifact, cell A) ===")
for tgt in ["precip_6h", "precip_12h", "precip_24h"]:
    p = artifact_probs(tgt, bins_a, cell_a)
    y = cell_a[tgt].to_numpy()
    ok = ~np.isnan(y)
    p, y = p[ok], y[ok]
    for name, lo_t, hi_t in [("unlikely(<=0.15)", 0.0, 0.15),
                             ("possible(0.40-0.70)", 0.40, 0.70),
                             ("likely(0.70-0.85)", 0.70, 0.85),
                             ("very_likely(>=0.85)", 0.85, 1.01)]:
        m = (p >= lo_t) & (p < hi_t)
        if m.sum() > 100:
            print(f"  {tgt} {name:>22}: issued {m.mean():6.2%} "
                  f"-> observed {y[m].mean():6.2%}")

print("\n=== MLP OPTION-B COMPARISON ===")
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import OneHotEncoder

climo = ClimatologyBaseline(cfg, manifest)
months_a = cell_a.index.month.to_numpy()

rng = np.random.default_rng(11)
sub = rng.choice(len(train), size=min(2_000_000, len(train)), replace=False)
tr = train.iloc[sub]
bins_tr = binner.transform(tr)
bins_cal = binner.transform(calib)

BIN_KEYS = ["slp", "d3h", "d6h", "d12h", "d1h", "hf", "curv", "solar8",
            "wind_rel", "wind_chg", "sky", "band", "season", "wclass"]
X_tr = np.column_stack([bins_tr[k] for k in BIN_KEYS])
X_cal = np.column_stack([bins_cal[k] for k in BIN_KEYS])
X_a = np.column_stack([bins_a[k] for k in BIN_KEYS])
enc = OneHotEncoder(handle_unknown="ignore", sparse_output=True).fit(X_tr)
X_tr_e, X_cal_e, X_a_e = enc.transform(X_tr), enc.transform(X_cal), enc.transform(X_a)

rows = []
models_dir = cfg.paths.resolved("models_dir") / "gbm_m1"
for tgt in [f"{a}_{b}h" for a in ("precip", "windup", "pfall")
            for b in (6, 12, 24)]:
    booster = gbm.load(models_dir / f"{tgt}.txt")
    p_teacher = np.clip(gbm.predict(booster, tr), 1e-4, 1 - 1e-4)
    z_teacher = np.log(p_teacher / (1 - p_teacher))
    mlp = MLPRegressor(hidden_layer_sizes=(16, 12), max_iter=80,
                       early_stopping=False, random_state=0)
    mlp.fit(X_tr_e, z_teacher)
    n_params = sum(w.size for w in mlp.coefs_) + sum(b.size for b in mlp.intercepts_)

    # int8 weight quantization (per-layer scale), simulated in float
    def q_predict(X):
        a = X.toarray() if hasattr(X, "toarray") else X
        for i, (W, b) in enumerate(zip(mlp.coefs_, mlp.intercepts_)):
            s = np.abs(W).max() / 127 or 1.0
            Wq = np.round(W / s) * s
            a = a @ Wq + b
            if i < len(mlp.coefs_) - 1:
                a = np.maximum(a, 0)
        return a.ravel()

    zq_cal = q_predict(X_cal_e)
    calbr = Calibrator().fit(1 / (1 + np.exp(-zq_cal)), calib[tgt].to_numpy())
    p_mlp = calbr.transform(1 / (1 + np.exp(-q_predict(X_a_e))))
    y = cell_a[tgt].to_numpy()
    p_ref = climo.predict(cell_a["station_id"], months_a, tgt, cell_a["regime"])
    bss = brier_skill(y, p_mlp, p_ref)
    kb = n_params / 1024
    rows.append({"target": tgt, "bss_mlp_int8": round(bss, 3),
                 "params": n_params, "kb_int8": round(kb, 2)})
    print(f"  {tgt}: MLP int8 BSS {bss:.3f} ({n_params} params ~{kb:.1f} KB)")

pd.DataFrame(rows).to_csv(
    REPO_ROOT / "reports" / "mlp_optionB_full_results.csv", index=False)
print("done")
