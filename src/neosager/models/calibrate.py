"""Isotonic calibration fit on the 2019 calib fold. Applied to every
probabilistic model (GBM, MLP, logreg, distilled table) — reliability before/
after is a mandatory report figure.
"""

from __future__ import annotations

import numpy as np
from sklearn.isotonic import IsotonicRegression


class Calibrator:
    def __init__(self):
        self.iso = IsotonicRegression(y_min=0.0, y_max=1.0,
                                      out_of_bounds="clip")
        self.fitted = False

    def fit(self, p_raw: np.ndarray, y: np.ndarray) -> "Calibrator":
        ok = ~np.isnan(p_raw) & ~np.isnan(y)
        if ok.sum() < 100:
            # too little data to calibrate — identity
            self.fitted = False
            return self
        self.iso.fit(p_raw[ok], y[ok])
        self.fitted = True
        return self

    def transform(self, p_raw: np.ndarray) -> np.ndarray:
        if not self.fitted:
            return p_raw
        out = np.full(len(p_raw), np.nan)
        ok = ~np.isnan(p_raw)
        out[ok] = self.iso.transform(p_raw[ok])
        return out
