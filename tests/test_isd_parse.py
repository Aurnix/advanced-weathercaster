"""Parser/regularizer unit tests on hand-crafted ISD CSV fixtures.

Every branch that nulls or drops data is exercised: report-type whitelist,
element QC rejection, missing sentinels, calm/variable wind, trace precip,
multi-period AA entries, sky obscured/missing, sub-hourly dedup and union.
"""

import csv
import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from neosager.config import load_config
from neosager.data.isd_parse import parse_isd_csv
from neosager.data.regularize import to_hourly

CFG = load_config().ingest

COLS = ["STATION", "DATE", "REPORT_TYPE", "LATITUDE", "LONGITUDE",
        "ELEVATION", "WND", "TMP", "SLP", "MA1", "AA1", "AW1", "MW1",
        "GF1", "GA1"]


def make_csv(tmp_path: Path, rows: list[dict]) -> Path:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLS, quoting=csv.QUOTE_ALL)
    w.writeheader()
    for r in rows:
        base = {c: "" for c in COLS}
        base.update({"STATION": "99999912345", "LATITUDE": "25.0",
                     "LONGITUDE": "-80.0", "ELEVATION": "10.0"})
        base.update(r)
        w.writerow(base)
    p = tmp_path / "fixture.csv"
    p.write_text(buf.getvalue(), encoding="utf-8")
    return p


def parse(tmp_path, rows):
    return parse_isd_csv(make_csv(tmp_path, rows), CFG)


def test_report_type_whitelist(tmp_path):
    df, drops = parse(tmp_path, [
        {"DATE": "2020-01-01T00:00:00", "REPORT_TYPE": "FM-15"},
        {"DATE": "2020-01-01T01:00:00", "REPORT_TYPE": "SOD"},
        {"DATE": "2020-01-01T02:00:00", "REPORT_TYPE": "SOM"},
        {"DATE": "2020-01-01T03:00:00", "REPORT_TYPE": "BOGUS"},
        {"DATE": "2020-01-01T04:00:00", "REPORT_TYPE": "FM-12"},
    ])
    assert len(df) == 2
    assert drops["rows_total"] == 5 and drops["rows_kept"] == 2
    assert drops["report_type_dropped"] == {"SOD": 1, "SOM": 1, "BOGUS": 1}


def test_wind_parsing(tmp_path):
    df, _ = parse(tmp_path, [
        # normal: 340 deg, 2.1 m/s
        {"DATE": "2020-01-01T00:00:00", "REPORT_TYPE": "FM-15",
         "WND": "340,1,N,0021,1"},
        # calm: no direction, speed forced 0
        {"DATE": "2020-01-01T01:00:00", "REPORT_TYPE": "FM-15",
         "WND": "999,9,C,0000,1"},
        # variable: no direction, speed kept
        {"DATE": "2020-01-01T02:00:00", "REPORT_TYPE": "FM-15",
         "WND": "999,9,V,0031,1"},
        # missing sentinels
        {"DATE": "2020-01-01T03:00:00", "REPORT_TYPE": "FM-15",
         "WND": "999,9,9,9999,9"},
        # QC-rejected direction (flag 3), speed fine
        {"DATE": "2020-01-01T04:00:00", "REPORT_TYPE": "FM-15",
         "WND": "180,3,N,0050,1"},
    ])
    assert df.loc[0, "wind_dir_deg"] == 340 and df.loc[0, "wind_speed_ms"] == pytest.approx(2.1)
    assert np.isnan(df.loc[1, "wind_dir_deg"]) and df.loc[1, "wind_speed_ms"] == 0.0
    assert np.isnan(df.loc[2, "wind_dir_deg"]) and df.loc[2, "wind_speed_ms"] == pytest.approx(3.1)
    assert bool(df.loc[2, "wind_variable"])
    assert np.isnan(df.loc[3, "wind_dir_deg"]) and np.isnan(df.loc[3, "wind_speed_ms"])
    assert np.isnan(df.loc[4, "wind_dir_deg"]) and df.loc[4, "wind_speed_ms"] == pytest.approx(5.0)


def test_pressure_and_temp(tmp_path):
    df, _ = parse(tmp_path, [
        {"DATE": "2020-01-01T00:00:00", "REPORT_TYPE": "FM-15",
         "TMP": "+0233,1", "SLP": "10171,1", "MA1": "99999,9,10163,1"},
        {"DATE": "2020-01-01T01:00:00", "REPORT_TYPE": "FM-15",
         "TMP": "+9999,9", "SLP": "99999,9", "MA1": "10170,1,99999,9"},
        {"DATE": "2020-01-01T02:00:00", "REPORT_TYPE": "FM-15",
         "TMP": "-0055,1", "SLP": "09876,2", "MA1": ""},
    ])
    assert df.loc[0, "temp_c"] == pytest.approx(23.3)
    assert df.loc[0, "slp_hpa"] == pytest.approx(1017.1)
    assert df.loc[0, "stn_p_hpa"] == pytest.approx(1016.3)
    assert np.isnan(df.loc[0, "altimeter_hpa"])
    assert np.isnan(df.loc[1, "temp_c"]) and np.isnan(df.loc[1, "slp_hpa"])
    assert np.isnan(df.loc[1, "stn_p_hpa"])
    assert df.loc[1, "altimeter_hpa"] == pytest.approx(1017.0)
    assert df.loc[2, "temp_c"] == pytest.approx(-5.5)
    # QC flag 2 (suspect) rejected
    assert np.isnan(df.loc[2, "slp_hpa"])


def test_precip_only_hourly_periods_count(tmp_path):
    df, _ = parse(tmp_path, [
        # 1h depth 2.5 mm
        {"DATE": "2020-01-01T00:00:00", "REPORT_TYPE": "FM-15",
         "AA1": "01,0025,3,1"},
        # 6h accumulation ignored (cannot be placed within the hour)
        {"DATE": "2020-01-01T01:00:00", "REPORT_TYPE": "FM-12",
         "AA1": "06,0100,3,1"},
        # trace: condition 2, depth stays 0, flag set
        {"DATE": "2020-01-01T02:00:00", "REPORT_TYPE": "FM-15",
         "AA1": "01,0000,2,1"},
        # missing depth sentinel
        {"DATE": "2020-01-01T03:00:00", "REPORT_TYPE": "FM-15",
         "AA1": "01,9999,9,9"},
    ])
    assert df.loc[0, "precip_1h_mm"] == pytest.approx(2.5)
    assert np.isnan(df.loc[1, "precip_1h_mm"])
    assert df.loc[2, "precip_1h_mm"] == 0.0 and bool(df.loc[2, "precip_trace"])
    assert np.isnan(df.loc[3, "precip_1h_mm"])


def test_present_weather_codes(tmp_path):
    df, _ = parse(tmp_path, [
        {"DATE": "2020-01-01T00:00:00", "REPORT_TYPE": "FM-15",
         "AW1": "61,1", "MW1": "60,1"},
        # QC-rejected code excluded
        {"DATE": "2020-01-01T01:00:00", "REPORT_TYPE": "FM-15",
         "AW1": "61,3", "MW1": ""},
    ])
    assert df.loc[0, "aw_codes"] == "61" and df.loc[0, "mw_codes"] == "60"
    assert df.loc[1, "aw_codes"] == "" and df.loc[1, "mw_codes"] == ""


def test_missing_code_columns_entirely(tmp_path):
    """Pre-ASOS files can lack AW/MW/GA columns altogether; the code columns
    must still come back as aligned empty strings, not NaN floats."""
    buf = io.StringIO()
    cols = ["STATION", "DATE", "REPORT_TYPE", "LATITUDE", "LONGITUDE",
            "ELEVATION", "WND", "TMP"]
    w = csv.DictWriter(buf, fieldnames=cols, quoting=csv.QUOTE_ALL)
    w.writeheader()
    w.writerow({"STATION": "x", "DATE": "1995-01-01T00:00:00",
                "REPORT_TYPE": "SAO", "LATITUDE": "25", "LONGITUDE": "-80",
                "ELEVATION": "10", "WND": "180,1,N,0040,1", "TMP": "+0100,1"})
    p = tmp_path / "old.csv"
    p.write_text(buf.getvalue(), encoding="utf-8")
    df, _ = parse_isd_csv(p, CFG)
    for c in ["aw_codes", "mw_codes", "au_precip_codes", "ga_cloud_types"]:
        assert df.loc[0, c] == ""
    hourly, _ = to_hourly(df, 1995, CFG)  # must not raise
    assert hourly.loc[pd.Timestamp("1995-01-01 00:00", tz="UTC"), "mw_codes"] == ""


def test_sky_parsing(tmp_path):
    df, _ = parse(tmp_path, [
        {"DATE": "2020-01-01T00:00:00", "REPORT_TYPE": "FM-15",
         "GF1": "02,99,1,99,9,99,9,00800,1,99,9,99,9"},
        # sky obscured (09) -> overcast 8
        {"DATE": "2020-01-01T01:00:00", "REPORT_TYPE": "FM-15",
         "GF1": "09,99,1,99,9,07,1,00100,1,99,9,99,9"},
        # missing
        {"DATE": "2020-01-01T02:00:00", "REPORT_TYPE": "FM-15",
         "GF1": "99,99,9,99,9,99,9,99999,9,99,9,99,9"},
    ])
    assert df.loc[0, "sky_oktas"] == 2.0
    assert df.loc[1, "sky_oktas"] == 8.0
    assert df.loc[1, "gf1_low_genus"] == 7
    assert np.isnan(df.loc[2, "sky_oktas"])
    assert np.isnan(df.loc[2, "gf1_low_genus"])


def test_hourly_regularization(tmp_path):
    df, _ = parse(tmp_path, [
        # :53 METAR rounds forward to 01:00
        {"DATE": "2020-01-01T00:53:00", "REPORT_TYPE": "FM-15",
         "WND": "180,1,N,0040,1", "TMP": "+0100,1", "SLP": "10100,1"},
        # SPECI in the same hour bin carries a shower onset; its scalars are
        # farther from the top of the hour so the METAR wins scalars
        {"DATE": "2020-01-01T01:20:00", "REPORT_TYPE": "FM-16",
         "WND": "200,1,N,0090,1", "TMP": "+0120,1", "MW1": "80,1",
         "AA1": "01,0012,3,1"},
        # lone report at 03:02 -> hour 03
        {"DATE": "2020-01-01T03:02:00", "REPORT_TYPE": "FM-12",
         "WND": "999,9,C,0000,1", "SLP": "10200,1"},
    ])
    hourly, stats = to_hourly(df, 2020, CFG)
    assert len(hourly) == 366 * 24  # 2020 is a leap year
    h1 = hourly.loc[pd.Timestamp("2020-01-01 01:00", tz="UTC")]
    # scalar from nearest (the :53 METAR, 7 min away)
    assert h1["temp_c"] == pytest.approx(10.0)
    assert h1["slp_hpa"] == pytest.approx(1010.0)
    # wind pair coherent from the METAR
    assert h1["wind_dir_deg"] == 180 and h1["wind_speed_ms"] == pytest.approx(4.0)
    # union picked up the SPECI shower code and precip
    assert h1["mw_codes"] == "80"
    assert h1["precip_1h_mm"] == pytest.approx(1.2)
    assert h1["n_reports"] == 2
    h3 = hourly.loc[pd.Timestamp("2020-01-01 03:00", tz="UTC")]
    assert h3["wind_speed_ms"] == 0.0 and np.isnan(h3["wind_dir_deg"])
    # untouched hour stays NaN / empty
    h5 = hourly.loc[pd.Timestamp("2020-01-01 05:00", tz="UTC")]
    assert np.isnan(h5["temp_c"]) and h5["mw_codes"] == "" and h5["n_reports"] == 0
    assert stats["hours_with_data"] == 2  # hours 01 (two reports) and 03
