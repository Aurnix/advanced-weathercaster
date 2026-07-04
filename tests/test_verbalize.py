"""Verbalizer v2 property tests: Sager-format output, probability-shape
narratives, wind clause reconstruction, monotonicity, degradation."""

import itertools

import numpy as np
import pytest

from neosager.deploy.verbalize import (verbalize, wording_rank,
                                       weather_narrative, wind_clause)


def probs(p6=None, p12=None, p24=None, w12=None, f12=None):
    return {"precip_6h": p6, "precip_12h": p12, "precip_24h": p24,
            "windup_12h": w12, "pfall_12h": f12}


def test_grid_all_combinations_valid():
    grid = [0.02, 0.1, 0.25, 0.45, 0.6, 0.75, 0.92]
    for p6, p12, p24 in itertools.product(grid, grid, grid):
        out = verbalize(probs(p6=p6, p12=p12, p24=p24, w12=0.3, f12=0.3),
                        local_hour=9)
        assert out.startswith("Forecast for the next 12-24 hours: ")
        assert out.endswith(("High confidence.", "Fairly confident.",
                             "Uncertain."))
        assert out.count(".") <= 4


def test_monotone_in_p12():
    ranks = [wording_rank(verbalize(probs(p12=p), local_hour=9))
             for p in np.linspace(0.01, 0.99, 25)]
    assert all(a <= b for a, b in zip(ranks, ranks[1:])), ranks


def test_temporal_shapes():
    # rain now, clearing later -> "followed by improvement"
    out = verbalize(probs(p6=0.85, p12=0.5, p24=0.2), local_hour=9)
    assert "followed by improvement" in out
    # dry now, rain later -> "increasing cloudiness" (the classic)
    out = verbalize(probs(p6=0.1, p12=0.78, p24=0.8), local_hour=9)
    assert "Increasing cloudiness followed by rain" in out
    # rain throughout
    out = verbalize(probs(p6=0.8, p12=0.85, p24=0.8), local_hour=9)
    assert "continuing through the period" in out
    # rain only at 24h
    out = verbalize(probs(p6=0.05, p12=0.2, p24=0.75), local_hour=9)
    assert "Fair at first" in out


def test_fair_and_improving_needs_rising():
    assert "improving" in verbalize(probs(p12=0.05), trend_hpa_3h=1.2)
    assert "improving" not in verbalize(probs(p12=0.05), trend_hpa_3h=0.0)


def test_barometer_clause():
    out = verbalize(probs(p6=0.8, p12=0.8, p24=0.8, f12=0.75), local_hour=9)
    assert "barometer still falling" in out


def test_wind_clause_sager_pairs():
    # current SW (sector 10), veering -> "Southwest or West winds"
    band = [0.05, 0.15, 0.6, 0.17, 0.03]
    dirs = [0.2, 0.55, 0.05, 0.1, 0.05, 0.05]     # veer one sector
    c = wind_clause(10, band, dirs, None)
    assert c == "Southwest or West winds, moderate to fresh (13-24 mph)"
    # backing sharply from N (sector 0) -> "North or Southwest"? no:
    # back two sectors from N(0) -> West is -2 -> index 6
    dirs_back = [0.1, 0.05, 0.05, 0.1, 0.6, 0.1]
    c2 = wind_clause(0, band, dirs_back, None)
    assert c2.startswith("North or West winds")


def test_wind_clause_gale_risk():
    band = [0.05, 0.15, 0.45, 0.15, 0.20]
    dirs = [0.6, 0.1, 0.1, 0.1, 0.05, 0.05]
    c = wind_clause(8, band, dirs, None)
    assert "gale risk (20%)" in c


def test_wind_clause_fallback_to_windup():
    assert wind_clause(None, None, None, 0.75) == "Wind increasing markedly"
    assert wind_clause(None, None, None, 0.55) == "Wind freshening"
    assert wind_clause(None, None, None, 0.2) is None


def test_missing_everything():
    assert verbalize(probs()) == "No forecast: insufficient data."


def test_full_sager_format_example():
    band = [0.02, 0.08, 0.25, 0.50, 0.15]
    dirs = [0.15, 0.5, 0.1, 0.1, 0.05, 0.1]
    out = verbalize(probs(p6=0.88, p12=0.6, p24=0.25, f12=0.7),
                    local_hour=15, band_probs_12h=band, dir_probs_12h=dirs,
                    current_sector16=10)
    assert out.startswith("Forecast for the next 12-24 hours: Rain or "
                          "showers within a few hours")
    assert "followed by improvement within 12 hours" in out
    assert "Southwest or West winds, strong (25-38 mph); gale risk (15%)" in out
