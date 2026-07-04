"""Label-definition tests on synthetic hourly fixtures.

Fixtures use lat=89 so the tide correction is numerically negligible and
elev=0 so sea-level reduction is the identity — pressure assertions then work
in plain hPa.
"""

import numpy as np
import pandas as pd
import pytest

from neosager.config import load_config
from neosager.labels import build_labels, conditions_class
from helpers import make_hourly

CFG = load_config()


def test_precip_positive_and_negative():
    h = make_hourly()
    h.iloc[12, h.columns.get_loc("mw_codes")] = "61"  # rain at hour 12
    lab = build_labels(h, CFG)
    assert lab.iloc[6]["precip_6h"] == 1.0    # window (6,12] catches it
    assert lab.iloc[12]["precip_6h"] == 0.0   # window (12,18] clear
    assert lab.iloc[0]["precip_12h"] == 1.0
    assert lab.iloc[0]["precip_6h"] == 0.0


def test_trace_is_not_measurable():
    h = make_hourly()
    h.iloc[12, h.columns.get_loc("precip_1h_mm")] = 0.0
    h.iloc[12, h.columns.get_loc("precip_trace")] = True
    lab = build_labels(h, CFG)
    assert lab.iloc[6]["precip_6h"] == 0.0


def test_gap_invalidates_negative_but_not_positive():
    h = make_hourly()
    h.iloc[10:15, h.columns.get_loc("n_reports")] = 0   # 5h hole
    hole = h.index[10:15]
    h.loc[hole, ["wind_speed_ms", "stn_p_hpa", "sky_oktas"]] = np.nan
    h.loc[hole, "mw_codes"] = ""
    lab = build_labels(h, CFG)
    # negative label with the hole inside its window is untrustworthy
    assert np.isnan(lab.iloc[8]["precip_6h"])
    # but an observed positive in the same broken window is still a positive
    h2 = h.copy()
    h2.iloc[16, h2.columns.get_loc("mw_codes")] = "63"
    lab2 = build_labels(h2, CFG)
    assert lab2.iloc[10]["precip_12h"] == 1.0


def test_wind_jump():
    h = make_hourly(wind_speed_ms=2.0)          # Beaufort 2
    h.iloc[20, h.columns.get_loc("wind_speed_ms")] = 9.0   # Beaufort 5
    lab = build_labels(h, CFG)
    assert lab.iloc[15]["windup_6h"] == 1.0
    assert lab.iloc[30]["windup_6h"] == 0.0


def test_pressure_fall():
    h = make_hourly(n=96)
    p = np.full(96, 1013.0)
    p[40:] = 1008.0                              # 5 hPa drop at hour 40
    h["stn_p_hpa"] = p
    lab = build_labels(h, CFG)
    assert lab.iloc[36]["pfall_6h"] == 1.0       # window (36,42] sees the drop
    assert lab.iloc[60]["pfall_6h"] == 0.0       # flat afterwards


def test_conditions_precedence():
    h = make_hourly()
    i = h.columns.get_loc
    h.iloc[10, i("mw_codes")] = "95"             # thunderstorm -> stormy
    h.iloc[20, i("mw_codes")] = "61"             # rain -> precipitating
    h.iloc[30, i("sky_oktas")] = 7.0             # overcast-ish -> unsettled
    cls = conditions_class(h)
    assert cls.iloc[10] == 3
    assert cls.iloc[20] == 2
    assert cls.iloc[30] == 1
    assert cls.iloc[50] == 0
    # neighbours of the rain hour are unsettled via the +/-3h rule
    assert cls.iloc[22] == 1


def test_conditions_label_at_lead():
    h = make_hourly()
    h.iloc[24, h.columns.get_loc("mw_codes")] = "61"
    lab = build_labels(h, CFG)
    assert lab.iloc[12]["cond_12h"] == 2.0


def test_truncated_windows_are_nan():
    h = make_hourly(n=30)
    lab = build_labels(h, CFG)
    assert np.isnan(lab.iloc[29]["precip_6h"])
    assert np.isnan(lab.iloc[25]["precip_6h"])
    assert lab.iloc[23]["precip_6h"] == 0.0
