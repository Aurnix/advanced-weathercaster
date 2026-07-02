"""Distill the GBM into GAM-style additive logit tables (plan Option A).

Model per head:
    logit(p) ~ bias + T0[slp_bin, d3h_bin] + T1[d12h_bin]
             + T2[wind_rel_bin, wind_chg_bin] + T3[sky_bin]
             + T4[lat_band, season]
fit by cyclic backfitting against the GBM teacher's logits on train rows.
Bin edges are train-set quantiles, committed into the artifact. A dense
table over all dims would be ~242k cells; additive structure gets the same
inputs into ~120 cells per head.

Quantization: table entries int8 at 1/16-logit resolution; the sigmoid AND
the head's isotonic calibration (fit on the calib fold) are composed into a
single 64-entry uint8 LUT over z in [-8, 8] — the shipped artifact is
calibrated by construction, not just its teacher.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

LOGIT_SCALE = 16          # int8 logit units: 1/16 logit
Z_RANGE = 8.0             # LUT domain [-8, 8] logits
LUT_SIZE = 64

SKY_CATS = ["clear", "partly", "mostly", "overcast", "precipitating", "missing"]
CHG_CATS = ["backing", "steady", "veering", "missing"]
BAND_CATS = ["24-35", "35-45", "45-55", "55+"]
WCLASS_CATS = ["calm", "light", "moderate", "strong", "gale", "missing"]


def season_of(month: np.ndarray) -> np.ndarray:
    return (np.asarray(month) % 12) // 3   # 0=DJF 1=MAM 2=JJA 3=SON


class Binner:
    """Train-quantile numeric bins + fixed categorical encodings."""

    def __init__(self, train: pd.DataFrame):
        def edges(col: str, n_bins: int) -> np.ndarray:
            q = np.linspace(0, 1, n_bins + 1)[1:-1]
            return np.unique(train[col].dropna().quantile(q).to_numpy())

        self.slp_edges = edges("slp", 8)
        self.d3h_edges = edges("d3h", 7)
        self.d12h_edges = edges("d12h", 5)
        self.d6h_edges = edges("d6h", 5)
        self.d1h_edges = edges("d1h", 5)
        self.hf_edges = edges("hf_var", 4)
        self.curv_edges = edges("curv3h", 5)

    @staticmethod
    def _digit(x: np.ndarray, edges: np.ndarray, missing_bin: int) -> np.ndarray:
        b = np.digitize(x, edges)
        return np.where(np.isnan(x), missing_bin, b).astype(int)

    def transform(self, df: pd.DataFrame) -> dict[str, np.ndarray]:
        n_slp = len(self.slp_edges) + 1
        n_d3h = len(self.d3h_edges) + 1
        n_d12h = len(self.d12h_edges) + 1
        out = {
            # numeric NaN -> middle bin (device always has pressure; missing
            # tendencies only at buffer warm-up)
            "slp": self._digit(df["slp"].to_numpy(), self.slp_edges, n_slp // 2),
            "d3h": self._digit(df["d3h"].to_numpy(), self.d3h_edges, n_d3h // 2),
            "d12h": self._digit(df["d12h"].to_numpy(), self.d12h_edges,
                                n_d12h // 2),
            "d6h": self._digit(df["d6h"].to_numpy(), self.d6h_edges,
                               (len(self.d6h_edges) + 1) // 2),
            "d1h": self._digit(df["d1h"].to_numpy(), self.d1h_edges,
                               (len(self.d1h_edges) + 1) // 2),
            "hf": self._digit(df["hf_var"].to_numpy(), self.hf_edges, 0),
            "curv": self._digit(df["curv3h"].to_numpy(), self.curv_edges,
                                (len(self.curv_edges) + 1) // 2),
            "solar8": (((df.index.hour + df["lon"].fillna(0) / 15.0) % 24)
                       // 3).astype(int).to_numpy().clip(0, 7),
            "wclass": df["wind_class"].map(
                {c: i for i, c in enumerate(WCLASS_CATS)}
            ).fillna(5).to_numpy(int),
            "wind_rel": np.where(np.isnan(df["wind_rel8"].to_numpy()), 8,
                                 df["wind_rel8"].to_numpy()).astype(int),
            "wind_chg": df["wind_change"].map(
                {c: i for i, c in enumerate(CHG_CATS)}).fillna(3).to_numpy(int),
            "sky": df["sky_state"].map(
                {c: i for i, c in enumerate(SKY_CATS)}).fillna(5).to_numpy(int),
            "band": df["lat_band"].map(
                {c: i for i, c in enumerate(BAND_CATS)}).fillna(1).to_numpy(int),
            "season": season_of(df.index.month.to_numpy()),
        }
        return out

    @property
    def dims(self) -> dict[str, int]:
        return {"slp": len(self.slp_edges) + 1,
                "d3h": len(self.d3h_edges) + 1,
                "d12h": len(self.d12h_edges) + 1,
                "d6h": len(self.d6h_edges) + 1,
                "d1h": len(self.d1h_edges) + 1,
                "hf": len(self.hf_edges) + 1,
                "curv": len(self.curv_edges) + 1, "solar8": 8,
                "wind_rel": 9, "wind_chg": 4, "sky": 6,
                "band": 4, "season": 4, "wclass": 6}


TABLE_SPEC = [("t_slp_d3h", ("slp", "d3h")),
              ("t_trend", ("d3h", "d6h")),      # trend persistence — pfall
              ("t_d12h", ("d12h",)),
              ("t_hf", ("hf",)),
              ("t_wind", ("wind_rel", "wind_chg")),
              ("t_wclass", ("wclass",)),        # current Beaufort — windup
              ("t_sky", ("sky",)),
              ("t_geo", ("band", "season"))]

# pfall heads: smooth curve extrapolation needs finer machinery — a dense
# 3-D fine-tendency table plus LINEAR fixed-point terms on raw tendencies
PFALL_SPEC = [("t_slp_d3h", ("slp", "d3h")),
              ("t_fine", ("d1h", "d3h", "d6h")),
              ("t_d12h", ("d12h",)),
              ("t_hf", ("hf",)),
              ("t_curv", ("curv",)),
              ("t_solar", ("solar8", "band")),  # residual semidiurnal tide
              ("t_geo", ("band", "season"))]
LINEAR_TERMS = ["d1h", "d3h", "d6h", "d12h"]   # hPa; weights Q4.12-friendly


class AdditiveTable:
    def __init__(self, binner: Binner, spec: list | None = None,
                 linear: bool = False):
        self.binner = binner
        self.spec = spec or TABLE_SPEC
        self.linear = linear
        d = binner.dims
        self.tables = {name: np.zeros([d[k] for k in keys])
                       for name, keys in self.spec}
        self.lin_w = np.zeros(len(LINEAR_TERMS))
        self.bias = 0.0

    @staticmethod
    def _lin_matrix(df: pd.DataFrame) -> np.ndarray:
        return np.nan_to_num(df[LINEAR_TERMS].to_numpy(dtype=float), nan=0.0)

    def _flat_idx(self, name: str, keys: tuple[str, ...],
                  bins: dict[str, np.ndarray]) -> np.ndarray:
        shape = self.tables[name].shape
        idx = bins[keys[0]]
        for k, s in zip(keys[1:], shape[1:]):
            idx = idx * s + bins[k]
        return idx

    def predict_logit(self, bins: dict[str, np.ndarray],
                      lin: np.ndarray | None = None) -> np.ndarray:
        z = np.full(len(bins["slp"]), self.bias)
        for name, keys in self.spec:
            z += self.tables[name].ravel()[self._flat_idx(name, keys, bins)]
        if self.linear and lin is not None:
            z += lin @ self.lin_w
        return z

    def fit(self, df: pd.DataFrame, teacher_logit: np.ndarray,
            weights: np.ndarray | None = None, n_passes: int = 12) -> "AdditiveTable":
        bins = self.binner.transform(df)
        lin = self._lin_matrix(df) if self.linear else None
        w = np.ones(len(teacher_logit)) if weights is None else weights
        ok = ~np.isnan(teacher_logit)
        z = teacher_logit
        self.bias = float(np.average(z[ok], weights=w[ok]))
        for _ in range(n_passes):
            if self.linear:
                resid = z - (self.predict_logit(bins, lin) - lin @ self.lin_w)
                x, r, ww = lin[ok], resid[ok], w[ok]
                xtw = x.T * ww
                self.lin_w = np.linalg.solve(
                    xtw @ x + 1e-3 * np.eye(x.shape[1]), xtw @ r)
            for name, keys in self.spec:
                pred_others = self.predict_logit(bins, lin) \
                    - self.tables[name].ravel()[self._flat_idx(name, keys, bins)]
                resid = z - pred_others
                flat = self._flat_idx(name, keys, bins)
                num = np.bincount(flat[ok], weights=(resid * w)[ok],
                                  minlength=self.tables[name].size)
                den = np.bincount(flat[ok], weights=w[ok],
                                  minlength=self.tables[name].size)
                upd = np.divide(num, den, out=np.zeros_like(num),
                                where=den > 20)  # ignore near-empty cells
                self.tables[name] = upd.reshape(self.tables[name].shape)
        return self

    # ---- quantization ----
    def quantize(self) -> dict:
        q = {name: np.clip(np.round(t * LOGIT_SCALE), -127, 127
                           ).astype(np.int8)
             for name, t in self.tables.items()}
        return {"tables": q,
                "bias": int(np.clip(round(self.bias * LOGIT_SCALE),
                                    -32767, 32767)),
                # linear weights in 1/256-logit-per-hPa fixed point
                "lin_w_q": np.round(self.lin_w * 256).astype(np.int16),
                "slp_edges": self.binner.slp_edges,
                "d3h_edges": self.binner.d3h_edges,
                "d12h_edges": self.binner.d12h_edges,
                "d6h_edges": self.binner.d6h_edges,
                "hf_edges": self.binner.hf_edges}

    def predict_logit_quantized(self, bins: dict[str, np.ndarray],
                                lin: np.ndarray | None = None) -> np.ndarray:
        q = self.quantize()
        z = np.full(len(bins["slp"]), q["bias"], dtype=np.int32)
        for name, keys in self.spec:
            z += q["tables"][name].ravel().astype(np.int32)[
                self._flat_idx(name, keys, bins)]
        zf = z.astype(float) / LOGIT_SCALE
        if self.linear and lin is not None:
            # device: (x_16ths * w_q) >> 12 in integer; float shim here
            zf += lin @ (q["lin_w_q"].astype(float) / 256.0)
        return zf


def make_prob_lut(z_grid_logits: np.ndarray,
                  calibrator) -> np.ndarray:
    """Compose sigmoid + isotonic calibration into a uint8 z->prob LUT."""
    p_raw = 1.0 / (1.0 + np.exp(-z_grid_logits))
    p_cal = calibrator.transform(p_raw) if calibrator is not None else p_raw
    return np.clip(np.round(p_cal * 255), 0, 255).astype(np.uint8)


def lut_lookup(z_logits: np.ndarray, lut: np.ndarray) -> np.ndarray:
    """Reference LUT lookup with linear interpolation (float shim; the
    integer-exact version lives in deploy/infer_int.py)."""
    pos = (z_logits + Z_RANGE) / (2 * Z_RANGE) * (LUT_SIZE - 1)
    pos = np.clip(pos, 0, LUT_SIZE - 1)
    lo = np.floor(pos).astype(int)
    hi = np.minimum(lo + 1, LUT_SIZE - 1)
    frac = pos - lo
    return (lut[lo] * (1 - frac) + lut[hi] * frac) / 255.0
