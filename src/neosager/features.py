"""Causal feature construction: everything at time t uses obs <= t only
(enforced by the poisoned-future test in tests/test_features.py).

Also simulates the watch's manual inputs from ISD fields (wind sector/class,
6h wind change, sky state, coarse cloud type), each with an explicit
'missing' category so one model serves pressure-only and full-input modes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Config
from .labels import beaufort, precip_evidence, sky_oktas_combined
from .pressure import device_slp

SPEED_CLASSES = ["calm", "light", "moderate", "strong", "gale"]
WIND_CHANGE = ["backing", "steady", "veering", "missing"]
SKY_STATES = ["clear", "partly", "mostly", "overcast", "precipitating", "missing"]
CLOUD_COARSE = ["none", "cirriform", "cumuliform", "stratiform", "nimbus", "missing"]

# GA cloud type code (ISD, WMO C-genus) -> coarse class
_GA_COARSE = {0: "cirriform", 1: "cirriform", 2: "cirriform",
              3: "cumuliform", 8: "cumuliform",
              4: "stratiform", 6: "stratiform", 7: "stratiform",
              5: "nimbus", 9: "nimbus"}
# GF1 low-cloud genus (WMO 0513 CL) -> coarse class
_CL_COARSE = {0: "none", 1: "cumuliform", 2: "cumuliform", 8: "cumuliform",
              3: "nimbus", 9: "nimbus",
              4: "stratiform", 5: "stratiform", 6: "stratiform",
              7: "stratiform"}
_COARSE_PRIORITY = ["nimbus", "cumuliform", "stratiform", "cirriform", "none"]


def wind_sector16(dir_deg: pd.Series) -> pd.Series:
    """0..15 (N=0, NNE=1, ...) as float with NaN for missing."""
    return np.floor(((dir_deg + 11.25) % 360) / 22.5)


def speed_class(speed_ms: pd.Series) -> pd.Series:
    b = beaufort(speed_ms)
    cls = pd.Series("missing", index=speed_ms.index)
    cls[(b >= 0) & (b <= 0)] = "calm"
    cls[(b >= 1) & (b <= 3)] = "light"
    cls[(b >= 4) & (b <= 5)] = "moderate"
    cls[(b >= 6) & (b <= 7)] = "strong"
    cls[b >= 8] = "gale"
    cls[speed_ms.isna()] = "missing"
    return cls


def circular_diff(a_deg: pd.Series, b_deg: pd.Series) -> pd.Series:
    """a - b wrapped to (-180, 180]."""
    d = (a_deg - b_deg + 180) % 360 - 180
    return d.where(d != -180, 180.0)


def wind_change_6h(dir_deg: pd.Series) -> pd.Series:
    d = circular_diff(dir_deg, dir_deg.shift(6))
    out = pd.Series("missing", index=dir_deg.index)
    out[d.notna() & (d >= 45)] = "veering"
    out[d.notna() & (d <= -45)] = "backing"
    out[d.notna() & (d.abs() < 45)] = "steady"
    return out


def sky_state(hourly: pd.DataFrame) -> pd.Series:
    oktas = sky_oktas_combined(hourly)
    precip = precip_evidence(hourly)
    out = pd.Series("missing", index=hourly.index)
    out[oktas <= 1] = "clear"
    out[(oktas >= 2) & (oktas <= 4)] = "partly"
    out[(oktas >= 5) & (oktas <= 7)] = "mostly"
    out[oktas >= 8] = "overcast"
    out[precip] = "precipitating"
    return out


def cloud_coarse(hourly: pd.DataFrame) -> pd.Series:
    def from_ga(s: str) -> str | None:
        if not s:
            return None
        classes = {_GA_COARSE.get(int(c)) for c in s.split(",") if c.isdigit()}
        classes.discard(None)
        for p in _COARSE_PRIORITY:
            if p in classes:
                return p
        return None

    ga = hourly["ga_cloud_types"].map(from_ga)
    cl = hourly["gf1_low_genus"].map(
        lambda g: _CL_COARSE.get(int(g)) if pd.notna(g) else None)
    return ga.fillna(cl).fillna("missing")


def build_features(hourly: pd.DataFrame, cfg: Config,
                   prevailing_dir_by_month: dict[int, float] | None = None
                   ) -> pd.DataFrame:
    """Feature matrix aligned to the hourly index. `prevailing_dir_by_month`
    comes from climo.py (train years only); when None the relative-wind
    feature is 'missing' everywhere (e.g. before climatology exists)."""
    fc = cfg.features
    out = pd.DataFrame(index=hourly.index)

    slp, source = device_slp(hourly, fc)
    out["slp"] = slp
    out["slp_source"] = source.where(source != "", "missing")

    for k in fc.tendency_hours:
        out[f"d{k}h"] = slp - slp.shift(k)
    out["curv3h"] = out["d3h"] - out["d3h"].shift(3)

    # high-frequency variability: std of linearly detrended trailing window
    w = fc.hf_window_h
    x = np.arange(w) - (w - 1) / 2.0
    xvar = float((x ** 2).sum())

    def _detrended_std(v: np.ndarray) -> float:
        if np.isnan(v).any():
            return np.nan
        slope = float((x * (v - v.mean())).sum()) / xvar
        resid = v - (v.mean() + slope * x)
        return float(resid.std())

    out["hf_var"] = slp.rolling(w).apply(_detrended_std, raw=True)

    out["temp_c"] = hourly["temp_c"]

    # calendar / location
    lat = float(hourly["lat"].dropna().median()) if hourly["lat"].notna().any() else np.nan
    lon = float(hourly["lon"].dropna().median()) if hourly["lon"].notna().any() else 0.0
    doy = hourly.index.dayofyear.to_numpy()
    out["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    out["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    solar = (hourly.index.hour.to_numpy() + lon / 15.0) % 24
    out["solar_sin"] = np.sin(2 * np.pi * solar / 24)
    out["solar_cos"] = np.cos(2 * np.pi * solar / 24)
    out["lat"] = lat
    out["lon"] = lon
    out["lat_band"] = pd.cut(pd.Series(lat, index=out.index),
                             [0, 35, 45, 55, 90],
                             labels=["24-35", "35-45", "45-55", "55+"]
                             ).astype(str)

    # simulated manual inputs
    wdir = hourly["wind_dir_deg"]
    out["wind_sector"] = wind_sector16(wdir).astype("float64")
    out["wind_class"] = speed_class(hourly["wind_speed_ms"])
    out["wind_change"] = wind_change_6h(wdir)
    out["sky_state"] = sky_state(hourly)
    out["cloud_coarse"] = cloud_coarse(hourly)

    if prevailing_dir_by_month is not None:
        prev = pd.Series(hourly.index.month, index=hourly.index).map(
            prevailing_dir_by_month)
        rel = circular_diff(wdir, prev)
        out["wind_rel8"] = np.floor(((rel + 202.5) % 360) / 45.0)  # 0..7
    else:
        out["wind_rel8"] = np.nan

    return out


def mask_manual_inputs(feats: pd.DataFrame, mask: np.ndarray) -> pd.DataFrame:
    """Simulate a user who entered nothing: manual-input group -> missing."""
    out = feats.copy()
    out.loc[mask, "wind_sector"] = np.nan
    out.loc[mask, "wind_class"] = "missing"
    out.loc[mask, "wind_change"] = "missing"
    out.loc[mask, "sky_state"] = "missing"
    out.loc[mask, "cloud_coarse"] = "missing"
    out.loc[mask, "wind_rel8"] = np.nan
    return out
