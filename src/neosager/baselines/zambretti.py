"""Faithful Zambretti forecaster (Negretti & Zambra, 1915/1920s dial).

Standard algorithm: sea-level pressure is mapped to a Z number 1-26 through
one of three linear formulas selected by the 3h trend (falling / steady /
rising, thresholds +/-1.6 hPa/3h), with a wind-direction correction and a
summer/winter adjustment for northerly winds. References: the widely
reproduced Beteljuice/emontnemery implementations of the original dial.

Two scored variants:
- 'faithful': Z number -> forecast text -> committed text->class map (in
  prose_mapping terms: fair / unsettled / precipitating), deterministic.
- 'calibrated': empirical event frequency per Z number measured on TRAIN
  years — the fair probabilistic comparison (fit in baselines/fit.py).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

ZAMBRETTI_TEXT = {
    1: "Settled fine", 2: "Fine weather", 3: "Becoming fine",
    4: "Fine, becoming less settled", 5: "Fine, possible showers",
    6: "Fairly fine, improving", 7: "Fairly fine, possible showers early",
    8: "Fairly fine, showery later", 9: "Showery early, improving",
    10: "Changeable, mending", 11: "Fairly fine, showers likely",
    12: "Rather unsettled clearing later", 13: "Unsettled, probably improving",
    14: "Showery, bright intervals", 15: "Showery, becoming less settled",
    16: "Changeable, some rain", 17: "Unsettled, short fine intervals",
    18: "Unsettled, rain later", 19: "Unsettled, some rain",
    20: "Mostly very unsettled", 21: "Occasional rain, worsening",
    22: "Rain at times, very unsettled", 23: "Rain at frequent intervals",
    24: "Rain, very unsettled", 25: "Stormy, may improve",
    26: "Stormy, much rain",
}

# committed text -> conditions-class map (0 fair, 1 unsettled, 2 precip/stormy)
Z_TO_CLASS = {z: (0 if z <= 9 else 1 if z <= 17 else 2)
              for z in range(1, 27)}
# Z >= 25 maps to "stormy" for the 4-class comparison
Z_TO_CLASS4 = {z: (0 if z <= 9 else 1 if z <= 17 else 2 if z <= 24 else 3)
               for z in range(1, 27)}

FALLING_THRESH = -1.6  # hPa per 3h
RISING_THRESH = 1.6


def zambretti_z(slp_hpa: np.ndarray, d3h_hpa: np.ndarray,
                wind_sector16: np.ndarray, month: np.ndarray,
                lat: np.ndarray) -> np.ndarray:
    """Vectorized Z number 1-26 (NaN where pressure or trend missing)."""
    p = np.asarray(slp_hpa, dtype=float)
    d = np.asarray(d3h_hpa, dtype=float)

    z = np.full(p.shape, np.nan)
    falling = d <= FALLING_THRESH
    rising = d >= RISING_THRESH
    steady = ~falling & ~rising

    z = np.where(falling, 127 - 0.12 * p, z)
    z = np.where(steady, 144 - 0.13 * p, z)
    z = np.where(rising, 185 - 0.16 * p, z)

    # wind correction (dial "set against wind"): traditional adjustments,
    # sectors 0..15 with N=0. Northerly quadrants worsen, southerly improve
    # slightly less; calm/missing (NaN sector) no adjustment.
    w = np.asarray(wind_sector16, dtype=float)
    adj = np.zeros_like(z)
    with np.errstate(invalid="ignore"):
        northerly = (w <= 2) | (w >= 14)          # NNE..N..NNW
        easterly = (w > 2) & (w <= 6)
        southerly = (w > 6) & (w <= 10)
        westerly = (w > 10) & (w < 14)
    adj[northerly & ~np.isnan(w)] += 1
    adj[easterly & ~np.isnan(w)] += 1
    adj[southerly & ~np.isnan(w)] -= 2
    adj[westerly & ~np.isnan(w)] += 0
    # summer northerly in the NH is drier; winter northerly colder/snowier
    nh = np.asarray(lat, dtype=float) >= 0
    summer = np.isin(np.asarray(month), [6, 7, 8]) & nh
    winter = np.isin(np.asarray(month), [12, 1, 2]) & nh
    adj[northerly & summer & ~np.isnan(w)] -= 1
    adj[northerly & winter & ~np.isnan(w)] += 1

    z = z + adj
    z = np.clip(np.round(z), 1, 26)
    z[np.isnan(p) | np.isnan(d)] = np.nan
    return z


def zambretti_from_features(feats: pd.DataFrame) -> pd.Series:
    return pd.Series(
        zambretti_z(feats["slp"].to_numpy(), feats["d3h"].to_numpy(),
                    feats["wind_sector"].to_numpy(),
                    feats.index.month.to_numpy(),
                    feats["lat"].to_numpy()),
        index=feats.index, name="zambretti_z")
