"""Shared test fixtures/helpers (importable as `helpers` because pytest
prepends the tests directory to sys.path)."""

import numpy as np
import pandas as pd


def make_hourly(n=72, **overrides):
    """Synthetic hourly frame with the full regularized-schema columns.
    lat=89 makes the tide correction negligible; elev=0 makes sea-level
    reduction the identity, so pressure assertions work in plain hPa."""
    idx = pd.date_range("2020-06-01", periods=n, freq="h", tz="UTC")
    df = pd.DataFrame({
        "n_reports": 1,
        "precip_1h_mm": np.nan,
        "precip_trace": False,
        "mw_codes": "",
        "aw_codes": "",
        "au_precip_codes": "",
        "ga_cloud_types": "",
        "wind_dir_deg": 180.0,
        "wind_speed_ms": 2.0,
        "wind_variable": False,
        "temp_c": 15.0,
        "slp_hpa": np.nan,
        "stn_p_hpa": 1013.0,
        "altimeter_hpa": np.nan,
        "sky_oktas": 2.0,
        "ga_max_oktas": np.nan,
        "gf1_low_genus": np.nan,
        "lat": 89.0,
        "lon": 0.0,
        "elev": 0.0,
    }, index=idx)
    for k, v in overrides.items():
        df[k] = v
    return df
