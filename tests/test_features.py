"""Feature tests, most importantly CAUSALITY: poisoning every observation
strictly after t must not change any feature at t."""

import numpy as np
import pandas as pd
import pytest

from neosager.config import load_config
from neosager.features import build_features, mask_manual_inputs
from neosager.pressure import reduce_to_sea_level, tide_hpa
from helpers import make_hourly

CFG = load_config()


def test_causality_poisoned_future():
    h = make_hourly(n=96)
    # give the series some structure so features are non-trivial
    h["stn_p_hpa"] = 1013 + 3 * np.sin(np.arange(96) / 10)
    h["wind_dir_deg"] = (np.arange(96) * 7) % 360
    feats_clean = build_features(h, CFG, {6: 270.0})

    t = 48
    poisoned = h.copy()
    future = poisoned.index[t + 1:]
    for c in poisoned.columns:
        if poisoned[c].dtype.kind == "f":
            poisoned.loc[future, c] = np.nan
    poisoned.loc[future, "mw_codes"] = "95"
    poisoned.loc[future, "n_reports"] = 0
    # keep station identity columns (constant metadata, not observations)
    poisoned.loc[future, ["lat", "lon", "elev"]] = h.loc[future, ["lat", "lon", "elev"]]
    feats_poisoned = build_features(poisoned, CFG, {6: 270.0})

    row_c = feats_clean.iloc[: t + 1]
    row_p = feats_poisoned.iloc[: t + 1]
    for col in feats_clean.columns:
        a, b = row_c[col], row_p[col]
        if a.dtype.kind == "f":
            assert np.allclose(a.fillna(-999), b.fillna(-999)), \
                f"feature {col} looked at the future"
        else:
            assert (a == b).all(), f"feature {col} looked at the future"


def test_tendencies():
    h = make_hourly(n=48)
    p = np.full(48, 1013.0)
    p[24:] = 1010.0
    h["stn_p_hpa"] = p
    f = build_features(h, CFG)
    assert f.iloc[26]["d3h"] == pytest.approx(-3.0, abs=0.05)
    assert f.iloc[40]["d3h"] == pytest.approx(0.0, abs=0.05)


def test_manual_input_simulation():
    h = make_hourly()
    h["wind_dir_deg"] = 200.0
    h["wind_speed_ms"] = 9.0
    h["sky_oktas"] = 8.0
    f = build_features(h, CFG)
    assert f.iloc[10]["wind_class"] == "moderate"
    assert f.iloc[10]["wind_sector"] == 9  # SSW
    assert f.iloc[10]["sky_state"] == "overcast"
    assert f.iloc[10]["wind_change"] == "steady"


def test_wind_change_veering_backing():
    h = make_hourly(n=24)
    d = np.full(24, 180.0)
    d[12:] = 250.0  # +70 deg -> veering
    h["wind_dir_deg"] = d
    f = build_features(h, CFG)
    assert f.iloc[14]["wind_change"] == "veering"
    d2 = np.full(24, 180.0)
    d2[12:] = 100.0  # -80 -> backing
    h["wind_dir_deg"] = d2
    f2 = build_features(h, CFG)
    assert f2.iloc[14]["wind_change"] == "backing"


def test_sea_level_reduction_magnitude():
    # ~1600 m (Denver): reduction adds roughly 160-190 hPa at 850-ish hPa
    p = pd.Series([835.0])
    slp = reduce_to_sea_level(p, 1600.0, pd.Series([15.0]))
    assert 990 < slp.iloc[0] < 1030


def test_tide_amplitude_by_latitude():
    idx = pd.date_range("2020-06-01", periods=48, freq="h", tz="UTC")
    equator = tide_hpa(0.0, 0.0, idx, CFG.features)
    high_lat = tide_hpa(65.0, 0.0, idx, CFG.features)
    assert equator.max() - equator.min() > 2.0        # ~2x S2 amplitude
    assert high_lat.max() - high_lat.min() < 1.5
    # the full tide (S2+S1) repeats every 24 h
    assert np.corrcoef(equator[:24], np.roll(equator, -24)[:24])[0, 1] > 0.99


def test_masking():
    h = make_hourly()
    f = build_features(h, CFG)
    mask = np.zeros(len(f), dtype=bool)
    mask[:10] = True
    m = mask_manual_inputs(f, mask)
    assert (m.iloc[:10]["sky_state"] == "missing").all()
    assert m.iloc[:10]["wind_sector"].isna().all()
    assert (m.iloc[10:]["sky_state"] == f.iloc[10:]["sky_state"]).all()
