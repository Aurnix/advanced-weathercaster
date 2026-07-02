"""Verbalizer property tests: coverage of all probability combinations,
monotone wording strength, sentence budget, missing-input degradation."""

import itertools

import numpy as np
import pytest

from neosager.deploy.verbalize import verbalize, wording_rank


def probs(p6=None, p12=None, p24=None, w12=None, f12=None):
    return {"precip_6h": p6, "precip_12h": p12, "precip_24h": p24,
            "windup_12h": w12, "pfall_12h": f12}


def test_grid_all_combinations_produce_valid_output():
    grid = [0.02, 0.1, 0.25, 0.45, 0.6, 0.75, 0.92]
    for p6, p12, w12 in itertools.product(grid, grid, [0.1, 0.6, 0.8]):
        out = verbalize(probs(p6=p6, p12=p12, p24=max(p6, p12), w12=w12),
                        local_hour=9)
        assert out and out.endswith(".")
        # budget: <= 2 sentences + confidence word
        assert out.count(".") <= 3
        assert any(c in out for c in
                   ("High confidence.", "Fairly confident.", "Uncertain."))


def test_monotone_wording_in_precip_probability():
    grid = np.linspace(0.01, 0.99, 25)
    ranks = [wording_rank(verbalize(probs(p12=p), local_hour=9))
             for p in grid]
    assert all(a <= b for a, b in zip(ranks, ranks[1:])), ranks


def test_likely_threshold():
    assert "Rain likely" in verbalize(probs(p12=0.72))
    assert "Rain very likely" in verbalize(probs(p12=0.9))
    assert "Rain possible" in verbalize(probs(p12=0.5))


def test_earliest_decisive_lead_wins():
    out = verbalize(probs(p6=0.8, p12=0.9), local_hour=9)
    assert "within a few hours" in out


def test_fair_improving_needs_rising_pressure():
    fair_rising = verbalize(probs(p12=0.05), trend_hpa_3h=1.2)
    fair_flat = verbalize(probs(p12=0.05), trend_hpa_3h=0.0)
    assert "improving" in fair_rising
    assert "improving" not in fair_flat


def test_wind_and_deterioration_clauses():
    out = verbalize(probs(p12=0.75, w12=0.75, f12=0.7), local_hour=15)
    assert "Wind increasing markedly" in out
    assert "deteriorating" in out
    assert out.count(".") <= 3


def test_prose_never_contradicts_probability():
    # high precip prob must never produce "unlikely" wording and vice versa
    assert "unlikely" not in verbalize(probs(p12=0.9))
    assert "likely" not in verbalize(probs(p12=0.05)).replace("unlikely", "")


def test_missing_inputs_degrade():
    assert verbalize(probs()) == "No forecast: insufficient data."
    out = verbalize(probs(p24=0.8), local_hour=9)   # only 24h available
    assert "Rain" in out


def test_daypart_phrasing():
    out = verbalize(probs(p12=0.8), local_hour=7)   # 7+12=19 -> evening
    assert "by evening" in out
