"""Sager port verification: golden cross-execution against the original JS
(all 5,400 input combinations), mapping completeness, and physical sanity."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from neosager.baselines.sager import SagerCaster

FIXTURE = Path(__file__).parent / "fixtures" / "sager_golden.json"


@pytest.fixture(scope="module")
def caster():
    return SagerCaster()


def test_golden_full_grid(caster):
    with open(FIXTURE, encoding="utf-8") as f:
        golden = json.load(f)
    assert len(golden) == 5400
    mismatches = []
    for key, expected in golden.items():
        wind, rumbo, hpa, tr, nb = key.split("|")
        r = caster.cast(wind, rumbo, int(hpa), int(tr), int(nb))
        got = "Exceptional weather, " if r is None else r[0]
        if got != expected:
            mismatches.append((key, expected, got))
    assert not mismatches, f"{len(mismatches)} mismatches, first: {mismatches[0]}"


def test_mapping_complete(caster):
    fmap = caster.mapping["forecast_to_class"]
    assert set(int(k) for k in fmap) == set(range(21))
    assert all(v in (0, 1, 2) for v in fmap.values())


def test_pressure_bands(caster):
    bands = caster.pressure_band(np.array([1035.0, 1025.0, 1015.0, 1008.0,
                                           1002.0, 992.0, 980.0, 970.0]))
    assert list(bands) == [1, 2, 3, 4, 5, 6, 7, 8]


def test_trend_classes(caster):
    t = caster.trend_class(np.array([3.0, 1.0, 0.0, -1.0, -3.0]))
    assert list(t) == [1, 2, 3, 4, 5]


def test_physical_sanity_falling_backing_south(caster):
    """Falling pressure + backing southerly + overcast must forecast
    deterioration (precip class), not fair."""
    r = caster.cast("S", "BACKING", 5, 5, 4)
    assert r is not None
    fmap = caster.mapping["forecast_to_class"]
    assert fmap[r[1][0]] == 2


def test_physical_sanity_high_rising_clear(caster):
    """High pressure, rising, clear sky, steady NW wind -> fair."""
    r = caster.cast("NW", "STEADY", 2, 2, 1)
    assert r is not None
    fmap = caster.mapping["forecast_to_class"]
    assert fmap[r[1][0]] == 0


def test_predict_frame_missing_inputs(caster):
    idx = pd.date_range("2020-01-01", periods=3, freq="h", tz="UTC")
    feats = pd.DataFrame({
        "slp": [1013.0, 1013.0, np.nan],
        "d6h": [-2.5, -2.5, -2.5],
        "sky_state": ["overcast", "missing", "overcast"],
        "wind_sector": [8.0, 8.0, 8.0],
        "wind_class": ["moderate", "moderate", "moderate"],
        "wind_change": ["backing", "backing", "backing"],
    }, index=idx)
    out = caster.predict_frame(feats)
    assert not np.isnan(out["sager_forecast_idx"].iloc[0])
    assert np.isnan(out["sager_forecast_idx"].iloc[1])  # no sky obs
    assert np.isnan(out["sager_forecast_idx"].iloc[2])  # no pressure
