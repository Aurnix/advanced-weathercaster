"""Parse NOAA ISD global-hourly CSV (one station-year) into a typed per-report
DataFrame. All ISD field/sentinel/QC knowledge lives in this module.

Field layout reference: docs/isd-format-document.pdf (committed). ISD encodes
each composite field as comma-separated subfields inside one CSV cell, with
all-9s sentinels for missing and a per-element QC flag.

Decisions (see also docs/decisions.md):
- REPORT_TYPE whitelist first: SOD/SOM daily/monthly summaries carry 24h precip
  totals that would poison hourly labels.
- Element QC flags in cfg.qc_reject_flags ({2,3,6,7} = suspect/erroneous) null
  out that element only; the row survives.
- The row-level QUALITY_CONTROL column names the QC *process* (V01/V02/V03...),
  not a pass/fail — we keep all values and rely on element QC.
- Precipitation depth: only period==1h AA entries are used (precip_1h_mm).
  Longer accumulation periods (3h/6h SYNOP totals) cannot be placed within the
  hour and would leak precip from before the label window; stations without
  hourly AA reporting rely on present-weather codes instead.
- Trace precip (AA condition code 2) is flagged but depth stays 0.0 —
  "measurable" excludes trace.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..config import IngestCfg

# Columns we ask pandas for; absent ones (e.g. AA3 at stations that never
# report it) are silently tolerated.
_WANTED = [
    "STATION", "DATE", "REPORT_TYPE", "LATITUDE", "LONGITUDE", "ELEVATION",
    "WND", "TMP", "SLP", "MA1",
    "AA1", "AA2", "AA3", "AA4",
    "AW1", "AW2", "AW3", "AW4",
    "MW1", "MW2", "MW3", "MW4", "MW5", "MW6", "MW7",
    "AU1", "AU2", "AU3", "AU4", "AU5",
    "GF1", "GA1", "GA2", "GA3",
]

_SCALE = 10.0  # ISD stores most numerics as value*10


def _sub(col: pd.Series, i: int, n: int) -> pd.Series:
    """i-th comma-separated subfield of an ISD composite column (padded)."""
    parts = col.str.split(",", expand=True)
    if parts.shape[1] <= i:
        return pd.Series("", index=col.index)
    return parts[i].fillna("")


def _num(values: pd.Series, qc: pd.Series, sentinels: set[str],
         reject_flags: set[str], scale: float = _SCALE) -> pd.Series:
    """Numeric subfield -> float; sentinel or rejected-QC -> NaN."""
    v = values.str.strip()
    bad = v.isin(sentinels) | (v == "") | qc.str.strip().isin(reject_flags)
    out = pd.to_numeric(v.where(~bad, None), errors="coerce") / scale
    return out.astype("float64")


def _codes(cols: list[pd.Series], qc_idx: int, code_idx: int,
           reject_flags: set[str], index: pd.Index) -> pd.Series:
    """Join valid 2-digit codes from several AW/MW-style columns: '61,80'."""
    keep: list[pd.Series] = []
    for col in cols:
        code = _sub(col, code_idx, 2).str.strip()
        qc = _sub(col, qc_idx, 2).str.strip()
        valid = (code != "") & ~qc.isin(reject_flags) & code.str.isdigit()
        keep.append(code.where(valid, ""))
    if not keep:
        return pd.Series("", index=index)
    joined = keep[0]
    for s in keep[1:]:
        joined = joined + "," + s
    return joined.str.strip(",").str.replace(r",+", ",", regex=True)


def parse_isd_csv(path: Path, cfg: IngestCfg) -> tuple[pd.DataFrame, dict]:
    """Returns (per-report DataFrame sorted by time, drop-count dict)."""
    reject = set(cfg.qc_reject_flags)

    header = pd.read_csv(path, nrows=0)
    usecols = [c for c in _WANTED if c in header.columns]
    raw = pd.read_csv(path, usecols=usecols, dtype=str, keep_default_na=False)
    drops: dict = {"rows_total": int(len(raw))}

    # --- REPORT_TYPE whitelist (before anything else) ---
    rt = raw["REPORT_TYPE"].str.strip()
    keep_mask = rt.isin(cfg.report_types_keep)
    drops["report_type_dropped"] = (
        rt[~keep_mask].value_counts().to_dict()
    )
    raw = raw[keep_mask].copy()
    rt = rt[keep_mask]
    drops["rows_kept"] = int(len(raw))
    if raw.empty:
        return pd.DataFrame(), drops

    def col(name: str) -> pd.Series:
        if name in raw.columns:
            return raw[name].astype(str)
        return pd.Series("", index=raw.index)

    out = pd.DataFrame(index=raw.index)
    out["ts"] = pd.to_datetime(raw["DATE"], utc=True, format="ISO8601")
    out["report_type"] = rt
    out["lat"] = pd.to_numeric(raw["LATITUDE"], errors="coerce")
    out["lon"] = pd.to_numeric(raw["LONGITUDE"], errors="coerce")
    out["elev"] = pd.to_numeric(raw["ELEVATION"], errors="coerce")

    # --- WND: dir(3),dirQC,typecode,speed(4),speedQC ---
    wnd = col("WND")
    w_dir = _sub(wnd, 0, 3)
    w_dirqc = _sub(wnd, 1, 1)
    w_type = _sub(wnd, 2, 1).str.strip()
    w_spd = _sub(wnd, 3, 4)
    w_spdqc = _sub(wnd, 4, 1)
    dir_deg = _num(w_dir, w_dirqc, {"999"}, reject, scale=1.0)
    spd_ms = _num(w_spd, w_spdqc, {"9999"}, reject, scale=_SCALE)
    calm = w_type == "C"
    variable = w_type == "V"
    dir_deg = dir_deg.where(~(calm | variable))  # calm/variable: no direction
    spd_ms = spd_ms.mask(calm, 0.0)
    out["wind_dir_deg"] = dir_deg
    out["wind_speed_ms"] = spd_ms
    out["wind_variable"] = variable

    # --- TMP / SLP: value,QC ---
    tmp = col("TMP")
    out["temp_c"] = _num(_sub(tmp, 0, 5), _sub(tmp, 1, 1), {"+9999", "9999"}, reject)
    slp = col("SLP")
    out["slp_hpa"] = _num(_sub(slp, 0, 5), _sub(slp, 1, 1), {"99999"}, reject)

    # --- MA1: altimeter,QC,station_pressure,QC ---
    ma1 = col("MA1")
    out["altimeter_hpa"] = _num(_sub(ma1, 0, 5), _sub(ma1, 1, 1), {"99999"}, reject)
    out["stn_p_hpa"] = _num(_sub(ma1, 2, 5), _sub(ma1, 3, 1), {"99999"}, reject)

    # --- AA1-AA4: period_h(2),depth(4),condition(1),QC ---
    depth_1h = pd.Series(np.nan, index=raw.index)
    trace = pd.Series(False, index=raw.index)
    for name in ["AA1", "AA2", "AA3", "AA4"]:
        if name not in raw.columns:
            continue
        aa = col(name)
        period = pd.to_numeric(_sub(aa, 0, 2), errors="coerce")
        depth = _num(_sub(aa, 1, 4), _sub(aa, 3, 1), {"9999"}, reject)
        cond = _sub(aa, 2, 1).str.strip()
        hourly = period == 1
        depth_1h = np.fmax(depth_1h, depth.where(hourly))
        trace |= (hourly & (cond == "2")).fillna(False)
    out["precip_1h_mm"] = depth_1h
    out["precip_trace"] = trace

    # --- present weather ---
    out["aw_codes"] = _codes(
        [col(n) for n in ["AW1", "AW2", "AW3", "AW4"] if n in raw.columns],
        qc_idx=1, code_idx=0, reject_flags=reject, index=raw.index)
    out["mw_codes"] = _codes(
        [col(n) for n in ["MW1", "MW2", "MW3", "MW4", "MW5", "MW6", "MW7"]
         if n in raw.columns],
        qc_idx=1, code_idx=0, reject_flags=reject, index=raw.index)
    # AU (automated, METAR-style) kept as fallback precip evidence: subfield 3
    # is the precipitation/obscuration code (2=rain,3=snow... per format doc);
    # we record the descriptor+precip code pair compactly as "d:p".
    au_parts = []
    for name in ["AU1", "AU2", "AU3", "AU4", "AU5"]:
        if name not in raw.columns:
            continue
        au = col(name)
        qc = _sub(au, 6, 1).str.strip()
        prec = _sub(au, 3, 1).str.strip()
        valid = (prec != "") & (prec != "9") & ~qc.isin(reject)
        au_parts.append(prec.where(valid, ""))
    if au_parts:
        joined = au_parts[0]
        for s in au_parts[1:]:
            joined = joined + "," + s
        out["au_precip_codes"] = joined.str.strip(",").str.replace(
            r",+", ",", regex=True)
    else:
        out["au_precip_codes"] = ""

    # --- sky: GF1 total coverage + low genus; GA layer cloud types ---
    gf1 = col("GF1")
    cov = pd.to_numeric(_sub(gf1, 0, 2), errors="coerce")
    covqc = _sub(gf1, 2, 1).str.strip()
    cov = cov.mask(covqc.isin(reject))
    # 00-08 oktas; 09 = sky obscured -> treat as overcast; 10 = partial
    # obscuration and 99 = missing -> NaN
    cov = cov.mask(cov > 9).mask(cov == 9, 8.0)
    out["sky_oktas"] = cov
    genus = pd.to_numeric(_sub(gf1, 5, 2), errors="coerce")
    out["gf1_low_genus"] = genus.mask(genus == 99)

    # GA layer coverage doubles as a sky-cover fallback: modern ASOS stations
    # often report sky only via GA layers, not GF1 (max layer oktas ~ total).
    ga_types = []
    ga_oktas = pd.Series(np.nan, index=raw.index)
    for name in ["GA1", "GA2", "GA3"]:
        if name not in raw.columns:
            continue
        ga = col(name)
        cov = pd.to_numeric(_sub(ga, 0, 2), errors="coerce")
        covqc = _sub(ga, 1, 1).str.strip()
        cov = cov.mask(covqc.isin(reject)).mask(cov > 9).mask(cov == 9, 8.0)
        ga_oktas = np.fmax(ga_oktas, cov)
        ct = _sub(ga, 4, 2).str.strip()
        ctqc = _sub(ga, 5, 1).str.strip()
        valid = ct.str.isdigit() & (ct != "99") & ~ctqc.isin(reject)
        ga_types.append(ct.where(valid, ""))
    out["ga_max_oktas"] = ga_oktas
    if ga_types:
        joined = ga_types[0]
        for s in ga_types[1:]:
            joined = joined + "," + s
        out["ga_cloud_types"] = joined.str.strip(",").str.replace(
            r",+", ",", regex=True)
    else:
        out["ga_cloud_types"] = ""

    out = out.sort_values("ts").reset_index(drop=True)
    return out, drops
