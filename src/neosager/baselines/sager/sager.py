"""Python port of the 1942 Sager Weathercaster.

Lookup tables extracted verbatim from the MIT-licensed
Aurnix/Sager-Weather-Forecaster JavaScript (sager_table.json; see
LICENSE.aurnix). Golden tests cross-check every one of the 5,400 input
combinations against the original JS executed under Node
(tests/fixtures/sager_golden.json).

Input digitization decisions (the dial's prose has no machine-precise
cutoffs; these are the conventional inHg-based ones, committed here):
- pressure band: sea-level pressure vs the bounds printed in the dial doc
  (1029.5 / 1019 / 1012 / 1005 / 999 / 988 / 975 hPa)
- 6h trend: steady = |d6h| < 0.68 hPa (0.02 inHg); rapid = |d6h| >= 2.03 hPa
  (0.06 inHg); slow in between
- wind: 16-point sector collapsed to the dial's 8 points; calm = speed class
  'calm'; direction change: our backing/steady/veering feature (missing ->
  STEADY, the dial's neutral position)
- clouds: clear/partly/mostly/overcast/precipitating -> 1..5

The forecast is only defined when the manual inputs exist; rows with missing
sky are NaN (Sager cannot run without a sky observation — a real property of
the method that the missing-input ablation measures).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

_HERE = Path(__file__).parent

PRESSURE_BOUNDS = [1029.5, 1019.0, 1012.0, 1005.0, 999.0, 988.0, 975.0]
TREND_STEADY = 0.68   # hPa / 6h
TREND_RAPID = 2.03

# 16-point sector index (N=0) -> dial 8-point name
_SECTOR16_TO_8 = ["N", "N", "NE", "NE", "E", "E", "SE", "SE",
                  "S", "S", "SW", "SW", "W", "W", "NW", "NW"]

_SKY_TO_NUBES = {"clear": 1, "partly": 2, "mostly": 3, "overcast": 4,
                 "precipitating": 5}


class SagerCaster:
    def __init__(self):
        with open(_HERE / "sager_table.json", encoding="utf-8") as f:
            t = json.load(f)
        self.table = t["SAGER_TABLE"]
        self.wind_letter = t["WIND_LETTER"]
        self.forecast_text = t["z_forecast"]
        self.velocity_text = t["z_wind_velocities"]
        self.direction_text = t["z_wind_direction"]
        with open(_HERE / "prose_mapping.yaml", encoding="utf-8") as f:
            self.mapping = yaml.safe_load(f)

    # ---- scalar core, mirrors sager_cast.js exactly ----
    def cast(self, wind: str, rumbo: str, hpa_band: int, trend: int,
             nubes: int) -> tuple[str, list[int]] | None:
        letter = "Z" if wind == "calm" else self.wind_letter.get(
            f"{wind},{rumbo}")
        if letter is None:
            return None
        entry = self.table.get(f"{letter},{hpa_band},{trend},{nubes}")
        if entry is None:
            return None
        if len(entry) == 3:
            text = (self.forecast_text[entry[0]]
                    + self.direction_text[entry[1]]
                    + self.velocity_text[entry[2]])
        else:
            text = (self.forecast_text[entry[0]]
                    + self.direction_text[entry[1]]
                    + "early, changing to  "
                    + self.direction_text[entry[2]]
                    + self.velocity_text[entry[3]])
        return text, list(entry)

    # ---- input digitization from the feature frame ----
    @staticmethod
    def pressure_band(slp: np.ndarray) -> np.ndarray:
        band = np.digitize(-np.asarray(slp, dtype=float),
                           [-b for b in PRESSURE_BOUNDS]) + 1
        return np.where(np.isnan(slp), np.nan, band)

    @staticmethod
    def trend_class(d6h: np.ndarray) -> np.ndarray:
        d = np.asarray(d6h, dtype=float)
        t = np.full(d.shape, np.nan)
        t[d >= TREND_RAPID] = 1
        t[(d >= TREND_STEADY) & (d < TREND_RAPID)] = 2
        t[np.abs(d) < TREND_STEADY] = 3
        t[(d <= -TREND_STEADY) & (d > -TREND_RAPID)] = 4
        t[d <= -TREND_RAPID] = 5
        return t

    def predict_frame(self, feats: pd.DataFrame) -> pd.DataFrame:
        """Vector interface over a feature frame -> per-row forecast indices
        and mapped predictand classes (NaN where Sager cannot run)."""
        band = self.pressure_band(feats["slp"].to_numpy())
        trend = self.trend_class(feats["d6h"].to_numpy())
        sky = feats["sky_state"].map(_SKY_TO_NUBES)

        sector = feats["wind_sector"].to_numpy()
        calm = (feats["wind_class"] == "calm").to_numpy()
        rumbo = feats["wind_change"].str.upper().replace("MISSING", "STEADY")

        n = len(feats)
        f_idx = np.full(n, np.nan)
        v_idx = np.full(n, np.nan)
        cache: dict[tuple, tuple[float, float]] = {}
        band_l = band
        trend_l = trend
        sky_l = sky.to_numpy()
        rumbo_l = rumbo.to_numpy()
        for i in range(n):
            if np.isnan(band_l[i]) or np.isnan(trend_l[i]) or np.isnan(sky_l[i]):
                continue
            if calm[i]:
                wind = "calm"
            elif not np.isnan(sector[i]):
                wind = _SECTOR16_TO_8[int(sector[i])]
            else:
                continue  # no direction, not calm -> dial cannot be set
            key = (wind, rumbo_l[i], int(band_l[i]), int(trend_l[i]),
                   int(sky_l[i]))
            if key not in cache:
                r = self.cast(*key)
                cache[key] = (np.nan, np.nan) if r is None else (
                    float(r[1][0]), float(r[1][-1]))
            f_idx[i], v_idx[i] = cache[key]

        out = pd.DataFrame(index=feats.index)
        out["sager_forecast_idx"] = f_idx
        out["sager_velocity_idx"] = v_idx
        fmap = {int(k): v for k, v in self.mapping["forecast_to_class"].items()}
        cls = pd.Series(f_idx, index=feats.index).map(fmap)
        stormy_vel = set(self.mapping["stormy_velocity_idx"])
        cls = cls.mask(pd.Series(v_idx, index=feats.index).isin(stormy_vel), 3)
        out["sager_class4"] = cls
        out["sager_precip"] = (cls >= 2).astype(float).where(cls.notna())
        windup_vel = set(self.mapping["windup_velocity_idx"])
        out["sager_windup"] = (pd.Series(v_idx, index=feats.index)
                               .isin(windup_vel).astype(float)
                               .where(~np.isnan(v_idx)))
        return out
