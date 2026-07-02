"""Faithful Zambretti forecaster (Negretti & Zambra dial, 1915/1920s).

Structure follows the canonical 'beteljuice' digitization used by nearly all
modern ports: sea-level pressure (wind- and season-adjusted) is binned into
22 steps across 950-1050 hPa, and a TREND-SPECIFIC array (rising / steady /
falling, 3h trend, +/-1.6 hPa thresholds) maps the bin to one of 26 forecast
texts. Note the trend-specific arrays are what make rising-at-high-pressure
settled and falling-at-low-pressure stormy — single linear formulas get the
rising branch physically backwards (caught by tests/test_zambretti.py).

Scored two ways:
- 'faithful': text -> committed class map (fair/unsettled/precip/stormy).
- 'calibrated': empirical event frequency per Z number fit on train years —
  the fair probabilistic comparison.
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

# committed text -> class map (0 fair, 1 unsettled, 2 precipitating);
# Z >= 25 additionally maps to "stormy" in the 4-class comparison
Z_TO_CLASS = {z: (0 if z <= 9 else 1 if z <= 17 else 2)
              for z in range(1, 27)}
Z_TO_CLASS4 = {z: (0 if z <= 9 else 1 if z <= 17 else 2 if z <= 24 else 3)
               for z in range(1, 27)}

BARO_BOTTOM, BARO_TOP = 950.0, 1050.0
_STEP = (BARO_TOP - BARO_BOTTOM) / 22.0

FALLING_THRESH = -1.6  # hPa per 3h
RISING_THRESH = 1.6

# forecast-text index (0-based) per pressure bin 0-21, per trend
_RISE = [25, 25, 25, 24, 24, 19, 16, 12, 11, 9, 8, 6, 5, 2, 1, 1,
         0, 0, 0, 0, 0, 0]
_STEADY = [25, 25, 25, 25, 25, 25, 23, 23, 22, 18, 15, 13, 10, 4, 1, 1,
           0, 0, 0, 0, 0, 0]
_FALL = [25, 25, 25, 25, 25, 25, 25, 25, 23, 23, 21, 20, 17, 14, 7, 3,
         1, 1, 1, 0, 0, 0]

# wind-direction pressure adjustment, % of the 100 hPa range, 16 sectors N=0
# (southerlies depress effective pressure -> worse forecast)
_WIND_ADJ_PCT = [6.0, 5.0, 5.0, 2.0, -0.5, -2.0, -5.0, -8.5,
                 -12.0, -10.0, -6.0, -4.5, -3.0, -0.5, 1.5, 3.0]


def zambretti_z(slp_hpa: np.ndarray, d3h_hpa: np.ndarray,
                wind_sector16: np.ndarray, month: np.ndarray,
                lat: np.ndarray) -> np.ndarray:
    """Vectorized Z number 1-26 (NaN where pressure or trend missing)."""
    p = np.asarray(slp_hpa, dtype=float).copy()
    d = np.asarray(d3h_hpa, dtype=float)
    w = np.asarray(wind_sector16, dtype=float)
    m = np.asarray(month)
    nh = np.asarray(lat, dtype=float) >= 0

    # wind adjustment (no adjustment for calm/missing direction)
    has_w = ~np.isnan(w)
    adj = np.zeros_like(p)
    adj[has_w] = np.take(_WIND_ADJ_PCT, w[has_w].astype(int))
    p = p + adj

    falling = d <= FALLING_THRESH
    rising = d >= RISING_THRESH

    # season adjustment: local summer amplifies the trend's meaning
    summer = np.where(nh, np.isin(m, [4, 5, 6, 7, 8, 9]),
                      np.isin(m, [10, 11, 12, 1, 2, 3]))
    p = p + np.where(summer & rising, 7.0, 0.0)
    p = p - np.where(summer & falling, 7.0, 0.0)

    bins = np.clip(np.floor((p - BARO_BOTTOM) / _STEP), 0, 21)
    bins = np.nan_to_num(bins, nan=0.0).astype(int)

    z = np.where(falling, np.take(_FALL, bins),
                 np.where(rising, np.take(_RISE, bins),
                          np.take(_STEADY, bins))).astype(float) + 1.0
    z[np.isnan(np.asarray(slp_hpa, dtype=float)) | np.isnan(d)] = np.nan
    return z


def zambretti_from_features(feats: pd.DataFrame) -> pd.Series:
    return pd.Series(
        zambretti_z(feats["slp"].to_numpy(), feats["d3h"].to_numpy(),
                    feats["wind_sector"].to_numpy(),
                    feats.index.month.to_numpy(),
                    feats["lat"].to_numpy()),
        index=feats.index, name="zambretti_z")
