"""Collapse per-report ISD rows into one regularized hourly grid per
station-year. Gaps stay NaN — validity rules downstream decide what to trust;
nothing is ever interpolated.

Per hour-bin policy (docs/decisions.md):
- Present-weather codes and hourly precip are UNIONED across all reports in
  the bin (SPECIals carry precip onsets the top-of-hour report misses).
- Scalar fields come from the report nearest the top of the hour, tie-broken
  by report-type priority; a scalar the nearest report lacks falls back to the
  next-nearest report (per-scalar fill).
- Wind direction+speed are taken as a coherent pair from one report (never
  direction from one report and speed from another).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import IngestCfg
from ..wxcodes import AW_PRECIP, MW_PRECIP, any_code_in

_SCALARS = ["temp_c", "slp_hpa", "stn_p_hpa", "altimeter_hpa",
            "sky_oktas", "ga_max_oktas", "gf1_low_genus", "lat", "lon", "elev"]
_WIND = ["wind_dir_deg", "wind_speed_ms", "wind_variable"]


def _union_codes(s: pd.Series) -> str:
    vals: set[str] = set()
    for x in s:
        if x:
            vals.update(x.split(","))
    return ",".join(sorted(vals))


def to_hourly(reports: pd.DataFrame, year: int, cfg: IngestCfg
              ) -> tuple[pd.DataFrame, dict]:
    """Returns (hourly DataFrame indexed by a complete UTC hour grid, stats)."""
    idx = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00",
                        freq="h", tz="UTC")
    if reports.empty:
        hourly = pd.DataFrame(index=idx)
        return hourly, {"hours_expected": len(idx), "hours_with_data": 0}

    df = reports.copy()
    df["hour"] = df["ts"].dt.round("h")
    in_year = df["hour"].dt.year == year
    df = df[in_year]
    df["offset_s"] = (df["ts"] - df["hour"]).abs().dt.total_seconds()
    prio = {t: i for i, t in enumerate(cfg.scalar_type_priority)}
    df["prio"] = df["report_type"].map(prio).fillna(99).astype(int)
    df = df.sort_values(["hour", "offset_s", "prio"], kind="stable")

    g = df.groupby("hour", sort=True)

    # groupby.first() skips NaN -> "nearest report, per-scalar fallback"
    scalars = g[_SCALARS].first()

    # wind as a coherent pair: first report in sort order with a speed value
    # (df is sorted nearest-first, so drop_duplicates keeps the winner)
    wind_rows = df[df["wind_speed_ms"].notna()]
    wind = wind_rows.drop_duplicates("hour").set_index("hour")[_WIND]

    unions = g.agg(
        precip_1h_mm=("precip_1h_mm", "max"),
        precip_trace=("precip_trace", "any"),
        aw_codes=("aw_codes", _union_codes),
        mw_codes=("mw_codes", _union_codes),
        au_precip_codes=("au_precip_codes", _union_codes),
        ga_cloud_types=("ga_cloud_types", _union_codes),
        n_reports=("ts", "size"),
    )

    hourly = scalars.join(wind, how="outer").join(unions, how="outer")
    hourly = hourly.reindex(idx)
    hourly.index.name = "hour"
    hourly["n_reports"] = hourly["n_reports"].fillna(0).astype(int)
    hourly["precip_trace"] = hourly["precip_trace"].astype(object).where(
        hourly["precip_trace"].notna(), False).astype(bool)
    for c in ["aw_codes", "mw_codes", "au_precip_codes", "ga_cloud_types"]:
        hourly[c] = hourly[c].fillna("")

    stats = {
        "hours_expected": len(idx),
        "hours_with_data": int((hourly["n_reports"] > 0).sum()),
        "coverage_pressure": float(
            (hourly["stn_p_hpa"].notna() | hourly["slp_hpa"].notna()).mean()),
        "coverage_ma1": float(hourly["stn_p_hpa"].notna().mean()),
        "coverage_wind": float(hourly["wind_speed_ms"].notna().mean()),
        "coverage_sky": float(
            (hourly["sky_oktas"].notna() | hourly["ga_max_oktas"].notna()).mean()),
        "precip_hours": int(
            ((hourly["precip_1h_mm"] > 0)
             | hourly["mw_codes"].map(lambda s: any_code_in(s, MW_PRECIP))
             | hourly["aw_codes"].map(lambda s: any_code_in(s, AW_PRECIP))
             ).sum()),
    }
    return hourly, stats
