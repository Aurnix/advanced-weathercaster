"""Wind-output label tests (windband max-in-window + relative direction)."""

import numpy as np

from neosager.config import load_config
from neosager.labels import build_wind_labels, band5
from helpers import make_hourly

CFG = load_config()


def test_band5_mapping():
    assert list(band5(np.array([0.2, 2.0, 8.0, 12.0, 20.0]))) == [0, 1, 2, 3, 4]
    assert np.isnan(band5(np.array([np.nan]))[0])


def test_windband_max_in_window():
    h = make_hourly(wind_speed_ms=2.0)                       # light
    h.iloc[20, h.columns.get_loc("wind_speed_ms")] = 15.0    # strong spike
    lab = build_wind_labels(h, CFG)
    assert lab.iloc[15]["windband_6h"] == 3    # window catches the spike
    assert lab.iloc[30]["windband_6h"] == 1    # back to light


def test_windband_invalid_on_gap():
    h = make_hourly(wind_speed_ms=2.0)
    idx = h.index[10:15]
    h.loc[idx, "wind_speed_ms"] = np.nan
    h.loc[idx, "n_reports"] = 0
    lab = build_wind_labels(h, CFG)
    assert np.isnan(lab.iloc[8]["windband_6h"])   # unobserved gale possible


def test_winddir_veer_and_back():
    h = make_hourly(n=48, wind_dir_deg=180.0)
    d = np.full(48, 180.0)
    d[24:] = 235.0     # +55 deg -> veer one sector
    h["wind_dir_deg"] = d
    lab = build_wind_labels(h, CFG)
    assert lab.iloc[12]["winddir_12h"] == 1
    assert lab.iloc[30]["winddir_12h"] == 0    # steady after the shift
    d2 = np.full(48, 180.0)
    d2[24:] = 60.0     # -120 -> back sharply
    h["wind_dir_deg"] = d2
    lab2 = build_wind_labels(h, CFG)
    assert lab2.iloc[12]["winddir_12h"] == 4


def test_winddir_calm_now_is_nan_future_calm_is_class5():
    h = make_hourly(n=48, wind_dir_deg=180.0, wind_speed_ms=4.0)
    # future goes calm
    idx = h.columns.get_loc("wind_speed_ms")
    h.iloc[30:, idx] = 0.0
    h.iloc[30:, h.columns.get_loc("wind_dir_deg")] = np.nan
    lab = build_wind_labels(h, CFG)
    assert lab.iloc[18]["winddir_12h"] == 5
    # calm now -> relative shift undefined
    h2 = make_hourly(n=48, wind_speed_ms=0.0)
    h2["wind_dir_deg"] = np.nan
    lab2 = build_wind_labels(h2, CFG)
    assert np.isnan(lab2.iloc[10]["winddir_12h"])
