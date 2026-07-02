"""Persistence baseline: current conditions continue. Deterministic 0/1
probabilities by design — that IS the persistence forecast; its Brier score
equals its error rate.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def persistence_precip(df: pd.DataFrame) -> np.ndarray:
    """Precipitating now (sky_state from features) -> precip in window."""
    return (df["sky_state"] == "precipitating").to_numpy().astype(float)


def persistence_pfall(df: pd.DataFrame) -> np.ndarray:
    """Falling >= 1 hPa/3h now -> will fall >= 3 hPa further."""
    return (df["d3h"] <= -1.0).to_numpy().astype(float)


def persistence_windup(df: pd.DataFrame) -> np.ndarray:
    """Wind rarely jumps 2 Beaufort classes; persistence predicts 'no'."""
    return np.zeros(len(df))


def persistence_conditions(df: pd.DataFrame) -> np.ndarray:
    """Conditions class at t+L = class now (derived from feature columns)."""
    cls = np.zeros(len(df))
    sky = df["sky_state"]
    cls[(sky == "mostly") | (sky == "overcast")] = 1
    cls[sky == "precipitating"] = 2
    gale = df["wind_class"] == "gale"
    cls[gale.to_numpy()] = 3
    return cls
