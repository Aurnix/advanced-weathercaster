"""Device-faithful pressure chain, shared by labels and features.

The deployed watch has station pressure + GPS elevation + optional
(low-trust) temperature. We therefore reduce MA1 station pressure to sea
level OURSELVES rather than using the ISD SLP field (which is the station's
own reduction — non-device information). ISD SLP is used only as a flagged
fallback where MA1 is absent.

Includes the climatological S1/S2 atmospheric-tide correction: a systematic
~0.3-1.5 hPa semidiurnal swing that corrupts raw 3h/6h tendencies if left in.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import FeaturesCfg

_G = 9.80665        # m/s^2
_M = 0.0289644      # kg/mol dry air
_R = 8.31446        # J/(mol K)
_LAPSE = 0.0065     # K/m
_T0 = 288.15        # K standard surface temperature


def reduce_to_sea_level(stn_p_hpa: pd.Series, elev_m: float,
                        temp_c: pd.Series | None = None) -> pd.Series:
    """Hydrostatic reduction using mean column temperature (measured surface
    temp when available, standard atmosphere otherwise)."""
    if temp_c is not None:
        t_surface = temp_c.fillna(_T0 - 273.15) + 273.15
    else:
        t_surface = pd.Series(_T0, index=stn_p_hpa.index)
    t_mean = t_surface + _LAPSE * elev_m / 2.0
    return stn_p_hpa * np.exp(_G * _M * elev_m / (_R * t_mean))


def tide_hpa(lat_deg: float, lon_deg: float, hours_utc: pd.DatetimeIndex,
             cfg: FeaturesCfg) -> np.ndarray:
    """Climatological S2 (semidiurnal) + S1 (diurnal) pressure tide."""
    t_solar = (hours_utc.hour + hours_utc.minute / 60.0
               + lon_deg / 15.0) % 24.0
    phi = np.radians(lat_deg)
    s2 = (cfg.tide_s2_amp * np.cos(phi) ** 3
          * np.cos(4 * np.pi / 24.0 * (t_solar - cfg.tide_s2_phase_h)))
    s1 = (cfg.tide_s1_amp * np.cos(phi)
          * np.cos(2 * np.pi / 24.0 * (t_solar - cfg.tide_s1_phase_h)))
    return np.asarray(s2 + s1)


def device_slp(hourly: pd.DataFrame, cfg: FeaturesCfg,
               apply_tide: bool | None = None) -> tuple[pd.Series, pd.Series]:
    """Returns (corrected sea-level pressure series, source flag series).

    source: 'ma1' = our reduction of station pressure (device-faithful),
            'isd_slp' = ISD's own sea-level value (fallback), '' = missing.
    """
    elev = float(hourly["elev"].dropna().median()) if hourly["elev"].notna().any() else 0.0
    lat = float(hourly["lat"].dropna().median()) if hourly["lat"].notna().any() else 45.0
    lon = float(hourly["lon"].dropna().median()) if hourly["lon"].notna().any() else 0.0

    ours = reduce_to_sea_level(hourly["stn_p_hpa"], elev, hourly["temp_c"])
    slp = ours.fillna(hourly["slp_hpa"])
    source = pd.Series("", index=hourly.index)
    source[ours.notna()] = "ma1"
    source[ours.isna() & hourly["slp_hpa"].notna()] = "isd_slp"

    if apply_tide is None:
        apply_tide = cfg.tide_correction
    if apply_tide:
        slp = slp - tide_hpa(lat, lon, hourly.index, cfg)
    return slp, source
