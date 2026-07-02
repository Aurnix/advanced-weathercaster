"""Logistic-regression baseline: how much skill is 'easy' on this feature
set. One model per predictand x lead, same calibration path as the GBM.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC = ["slp", "d1h", "d3h", "d6h", "d12h", "curv3h", "hf_var",
           "doy_sin", "doy_cos", "solar_sin", "solar_cos", "lat"]
CATEGORICAL = ["wind_class", "wind_change", "sky_state", "cloud_coarse",
               "lat_band", "slp_source"]
# wind_sector/wind_rel8 are circular ints with NaN; treat as categorical
CIRCULAR = ["wind_sector", "wind_rel8"]


def _prep(df: pd.DataFrame) -> pd.DataFrame:
    x = df[NUMERIC + CATEGORICAL + CIRCULAR].copy()
    for c in CIRCULAR:
        x[c] = x[c].fillna(-1).astype(int).astype(str)
    return x


def make_pipeline() -> Pipeline:
    return Pipeline([
        ("prep", ColumnTransformer([
            ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                              ("sc", StandardScaler())]), NUMERIC),
            ("cat", OneHotEncoder(handle_unknown="ignore"),
             CATEGORICAL + CIRCULAR),
        ])),
        ("lr", LogisticRegression(max_iter=2000, C=1.0)),
    ])


def fit_predict(train: pd.DataFrame, targets: list[str],
                eval_sets: dict[str, pd.DataFrame]
                ) -> dict[str, dict[str, np.ndarray]]:
    """Returns {target: {eval_name: p_hat}}. Rows with NaN label are dropped
    from training per-target; eval predictions cover all rows."""
    out: dict[str, dict[str, np.ndarray]] = {}
    x_train_full = _prep(train)
    for tgt in targets:
        y = train[tgt]
        ok = y.notna()
        pipe = make_pipeline()
        pipe.fit(x_train_full[ok.to_numpy()], y[ok].astype(int))
        out[tgt] = {name: pipe.predict_proba(_prep(df))[:, 1]
                    for name, df in eval_sets.items()}
    return out
