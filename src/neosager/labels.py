"""Predictand construction. For each hour t and lead L, labels look ONLY at
the window W = (t, t+L] (or the single obs nearest t+L for the conditions
class). Everything here is potential future information by design — labels
must never be joined into the feature matrix.

Validity policy (docs/decisions.md): a POSITIVE event observed in the window
is trusted regardless of coverage; a NEGATIVE label additionally requires
>= window_min_coverage of hours observed AND no data gap longer than
window_max_gap_h. A "no precip" verdict over a half-missing window is a lie
that would inflate every model's skill.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Config
from .pressure import device_slp
from .wxcodes import (AW_HEAVY, AW_PRECIP, AW_THUNDER, MW_HEAVY, MW_PRECIP,
                      MW_THUNDER, AU_PRECIP, any_code_in)

# Beaufort class upper bounds in m/s (class = index of first bound > speed)
BEAUFORT_BOUNDS = np.array([0.5, 1.6, 3.4, 5.5, 8.0, 10.8, 13.9, 17.2,
                            20.8, 24.5, 28.5, 32.7])

CONDITIONS = {0: "fair", 1: "unsettled", 2: "precipitating", 3: "stormy"}


def beaufort(speed_ms: pd.Series | np.ndarray) -> np.ndarray:
    """Vectorized Beaufort class; NaN-safe (NaN -> -1 sentinel)."""
    s = np.asarray(speed_ms, dtype=float)
    b = np.digitize(np.nan_to_num(s, nan=-1.0), BEAUFORT_BOUNDS)
    return np.where(np.isnan(s), -1, b)


def _forward_sum(x: np.ndarray, lead: int) -> np.ndarray:
    """out[t] = sum of x[t+1 .. t+lead] (NaN-free input expected)."""
    c = np.concatenate([[0.0], np.cumsum(x)])
    n = len(x)
    upto = np.minimum(np.arange(n) + lead + 1, n)
    out = c[upto] - c[np.arange(n) + 1]
    # entries whose window is truncated by the end of the series are invalid
    out[np.arange(n) + lead > n - 1] = np.nan
    return out


def _forward_any(flag: np.ndarray, lead: int) -> np.ndarray:
    s = _forward_sum(flag.astype(float), lead)
    return s  # >0 means any; NaN means truncated window


def _forward_max(x: np.ndarray, lead: int) -> np.ndarray:
    """out[t] = max of x[t+1 .. t+lead], NaN-aware (all-NaN -> NaN)."""
    n = len(x)
    s = pd.Series(x)
    # rolling max of window `lead` ending at t+lead == max over (t, t+lead]
    r = s.rolling(lead, min_periods=1).max().shift(-lead)
    r[np.arange(n) + lead > n - 1] = np.nan
    return r.to_numpy()


def _forward_min(x: np.ndarray, lead: int) -> np.ndarray:
    n = len(x)
    s = pd.Series(x)
    r = s.rolling(lead, min_periods=1).min().shift(-lead)
    r[np.arange(n) + lead > n - 1] = np.nan
    return r.to_numpy()


def _gap_violation(observed: np.ndarray, lead: int, max_gap: int) -> np.ndarray:
    """True at t if the window (t, t+lead] contains a run of unobserved hours
    longer than max_gap. streak[h] = consecutive missing hours ending at h;
    a violation needs streak >= max_gap+1 at some h with h-t >= max_gap+1."""
    miss = ~observed.astype(bool)
    streak = np.zeros(len(miss))
    run = 0
    for i, m in enumerate(miss):
        run = run + 1 if m else 0
        streak[i] = run
    if lead <= max_gap:
        return np.zeros(len(miss), dtype=bool)
    s = pd.Series(streak)
    # max of streak over h in [t+max_gap+1, t+lead]: rolling window of length
    # lead-max_gap ending at t+lead
    w = lead - max_gap
    m = s.rolling(w, min_periods=1).max().shift(-lead)
    viol = (m >= max_gap + 1).to_numpy(copy=True)
    viol[np.arange(len(miss)) + lead > len(miss) - 1] = True  # truncated
    return viol


def precip_evidence(hourly: pd.DataFrame) -> pd.Series:
    """Boolean: measurable precipitation evidenced at this hour."""
    mm = hourly["precip_1h_mm"] > 0
    mw = hourly["mw_codes"].map(lambda s: any_code_in(s, MW_PRECIP))
    aw = hourly["aw_codes"].map(lambda s: any_code_in(s, AW_PRECIP))
    au = hourly["au_precip_codes"].map(
        lambda s: bool(s) and any(c in AU_PRECIP for c in s.split(",")))
    return (mm | mw | aw | au).astype(bool)


def thunder_evidence(hourly: pd.DataFrame) -> pd.Series:
    mw = hourly["mw_codes"].map(lambda s: any_code_in(s, MW_THUNDER))
    aw = hourly["aw_codes"].map(lambda s: any_code_in(s, AW_THUNDER))
    return (mw | aw).astype(bool)


def heavy_evidence(hourly: pd.DataFrame) -> pd.Series:
    mw = hourly["mw_codes"].map(lambda s: any_code_in(s, MW_HEAVY))
    aw = hourly["aw_codes"].map(lambda s: any_code_in(s, AW_HEAVY))
    return (mw | aw).astype(bool)


def sky_oktas_combined(hourly: pd.DataFrame) -> pd.Series:
    """GF1 total cover, falling back to max GA layer cover (modern ASOS)."""
    return hourly["sky_oktas"].fillna(hourly["ga_max_oktas"])


def conditions_class(hourly: pd.DataFrame) -> pd.Series:
    """Instantaneous 4-class conditions state per hour (NaN if unobserved)."""
    observed = hourly["n_reports"] > 0
    precip = precip_evidence(hourly)
    thunder = thunder_evidence(hourly)
    heavy = heavy_evidence(hourly)
    b = beaufort(hourly["wind_speed_ms"])
    sky = sky_oktas_combined(hourly)
    # precip within +/-3h makes an hour "unsettled" even without cover data
    p = precip.astype(float).to_numpy()
    near = pd.Series(p).rolling(7, center=True, min_periods=1).max().to_numpy()

    cls = np.zeros(len(hourly))
    cls[(near > 0) | (sky >= 5).to_numpy()] = 1
    cls[precip.to_numpy()] = 2
    cls[thunder.to_numpy() | heavy.to_numpy() | (b >= 8)] = 3
    cls[~observed.to_numpy()] = np.nan
    return pd.Series(cls, index=hourly.index)


# 5-band wind vocabulary matching the Sager dial's mph bands:
# 0 calm(<0.5 m/s) / 1 light(B1-3) / 2 moderate-fresh(B4-5) /
# 3 strong(B6-7) / 4 gale(B8+)
def band5(speed_ms: np.ndarray) -> np.ndarray:
    b = beaufort(speed_ms).astype(float)
    out = np.select([b < 0, b == 0, b <= 3, b <= 5, b <= 7],
                    [np.nan, 0, 1, 2, 3], default=4)
    return out


# relative-direction classes at t+L vs now:
# 0 steady (|shift| <= 22.5 deg) / 1 veer one sector (22.5-90] /
# 2 veer sharply (>90) / 3 back one sector / 4 back sharply /
# 5 becomes calm or variable
WINDDIR_CLASSES = ["steady", "veer", "veer_sharp", "back", "back_sharp",
                   "calm_variable"]


def build_wind_labels(hourly: pd.DataFrame, cfg: Config,
                      leads: list[int] | None = None) -> pd.DataFrame:
    """Sager-output-style wind predictands: windband_{L}h = MAX 5-band wind
    class within (t, t+L] (what a sailor plans around); winddir_{L}h =
    direction at t+L relative to now (nearest obs within tolerance).

    Validity mirrors build_labels: the max-band label needs window coverage
    (an unobserved gale must not read as calm); direction needs a usable
    direction now and an observation near t+L."""
    lc = cfg.labels
    leads = leads or lc.leads_h
    spd = hourly["wind_speed_ms"].to_numpy()
    dirs = hourly["wind_dir_deg"].to_numpy()
    observed = (~np.isnan(spd))
    calm_now = spd < 0.5

    out = pd.DataFrame(index=hourly.index)
    for L in leads:
        min_obs = int(np.ceil(lc.window_min_coverage * L))
        n_obs = _forward_sum(observed.astype(float), L)
        gap_bad = _gap_violation(observed, L, lc.window_max_gap_h)
        valid = (n_obs >= min_obs) & ~gap_bad

        wmax = _forward_max(spd, L)
        band = band5(wmax)
        band[~valid] = np.nan
        out[f"windband_{L}h"] = band

        # direction at t+L (nearest obs within +/- tolerance)
        d = pd.Series(dirs, index=hourly.index)
        s = pd.Series(spd, index=hourly.index)
        d_fut = d.shift(-L)
        s_fut = s.shift(-L)
        tol = int(lc.endpoint_tolerance_h)
        for k in range(1, tol + 1):
            d_fut = d_fut.fillna(d.shift(-(L - k))).fillna(d.shift(-(L + k)))
            s_fut = s_fut.fillna(s.shift(-(L - k))).fillna(s.shift(-(L + k)))
        diff = (d_fut.to_numpy() - dirs + 180) % 360 - 180
        cls = np.full(len(hourly), np.nan)
        cls[np.abs(diff) <= 22.5] = 0
        cls[(diff > 22.5) & (diff <= 90)] = 1
        cls[diff > 90] = 2
        cls[(diff < -22.5) & (diff >= -90)] = 3
        cls[diff < -90] = 4
        # future calm/variable: speed known but no direction
        fut_calm = (s_fut.to_numpy() < 0.5) | (np.isnan(d_fut.to_numpy())
                                               & ~np.isnan(s_fut.to_numpy()))
        cls[fut_calm] = 5
        # need a usable direction now (calm now -> relative shift undefined)
        cls[np.isnan(dirs) | calm_now] = np.nan
        cls[np.isnan(s_fut.to_numpy())] = np.nan
        out[f"winddir_{L}h"] = cls
    return out


def build_labels(hourly: pd.DataFrame, cfg: Config,
                 leads: list[int] | None = None) -> pd.DataFrame:
    """Returns a DataFrame indexed like `hourly` with columns
    precip_{L}h / windup_{L}h / pfall_{L}h / cond_{L}h per lead (0/1/NaN,
    conditions class 0-3/NaN)."""
    lc = cfg.labels
    leads = leads or lc.leads_h
    observed = (hourly["n_reports"] > 0).to_numpy()

    precip = precip_evidence(hourly).to_numpy().astype(float)
    # hours with a report count as precip-evidence-bearing (a manual obs with
    # no MW code and no AA1 means "no weather", not "unknown")
    slp, _ = device_slp(hourly, cfg.features)
    slp_arr = slp.to_numpy()
    spd = hourly["wind_speed_ms"].to_numpy()
    b_now = beaufort(spd).astype(float)
    b_now[b_now < 0] = np.nan
    cond_now = conditions_class(hourly).to_numpy()

    out = pd.DataFrame(index=hourly.index)
    for L in leads:
        min_obs = int(np.ceil(lc.window_min_coverage * L))
        n_obs = _forward_sum(observed.astype(float), L)
        gap_bad = _gap_violation(observed, L, lc.window_max_gap_h)
        neg_valid = (n_obs >= min_obs) & ~gap_bad

        # -- precipitation --
        pos = _forward_any(precip, L) > 0
        lab = np.where(pos, 1.0, np.where(neg_valid, 0.0, np.nan))
        out[f"precip_{L}h"] = lab

        # -- wind increase >= jump Beaufort classes --
        wmax = _forward_max(np.where(np.isnan(spd), np.nan, spd), L)
        b_max = beaufort(wmax).astype(float)
        b_max[np.isnan(wmax)] = np.nan
        jump = b_max - b_now
        w_pos = jump >= lc.wind_beaufort_jump
        w_obs = _forward_sum((~np.isnan(spd)).astype(float), L)
        w_neg_valid = (w_obs >= min_obs) & ~gap_bad & ~np.isnan(b_now)
        lab = np.where(w_pos & ~np.isnan(b_now), 1.0,
                       np.where(w_neg_valid, 0.0, np.nan))
        out[f"windup_{L}h"] = lab

        # -- further pressure fall >= threshold --
        pmin = _forward_min(slp_arr, L)
        p_pos = (slp_arr - pmin) >= lc.pressure_fall_hpa
        p_obs = _forward_sum((~np.isnan(slp_arr)).astype(float), L)
        p_neg_valid = (p_obs >= min_obs) & ~gap_bad & ~np.isnan(slp_arr)
        lab = np.where(p_pos & ~np.isnan(slp_arr), 1.0,
                       np.where(p_neg_valid, 0.0, np.nan))
        out[f"pfall_{L}h"] = lab

        # -- conditions class at t+L (nearest obs within tolerance) --
        cond = pd.Series(cond_now, index=hourly.index)
        at_lead = cond.shift(-L)
        tol = int(lc.endpoint_tolerance_h)
        for d in range(1, tol + 1):
            at_lead = at_lead.fillna(cond.shift(-(L - d)))
            at_lead = at_lead.fillna(cond.shift(-(L + d)))
        out[f"cond_{L}h"] = at_lead

    return out
