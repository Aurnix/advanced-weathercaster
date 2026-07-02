"""Zambretti sanity tests against well-known behavior of the dial."""

import numpy as np

from neosager.baselines.zambretti import (Z_TO_CLASS, zambretti_z,
                                          ZAMBRETTI_TEXT)


def _z(p, d3h, sector=np.nan, month=6, lat=45.0):
    return zambretti_z(np.array([p]), np.array([d3h]), np.array([sector]),
                       np.array([month]), np.array([lat]))[0]


def test_high_pressure_rising_is_settled():
    z = _z(1035.0, 2.5)
    assert z <= 3
    assert Z_TO_CLASS[int(z)] == 0


def test_low_pressure_falling_is_rain():
    z = _z(980.0, -3.0)
    assert z >= 20
    assert Z_TO_CLASS[int(z)] == 2


def test_mid_pressure_steady_is_fairish():
    z = _z(1015.0, 0.0)
    assert 1 <= z <= 14          # fair-to-mildly-unsettled band
    assert _z(1015.0, -2.5) > z  # falling at same pressure is worse


def test_falling_worse_than_rising_at_same_pressure():
    assert _z(1005.0, -2.5) > _z(1005.0, 2.5)


def test_missing_inputs_are_nan():
    assert np.isnan(_z(np.nan, -2.0))
    assert np.isnan(_z(1010.0, np.nan))


def test_all_z_have_text():
    assert set(ZAMBRETTI_TEXT) == set(range(1, 27))
