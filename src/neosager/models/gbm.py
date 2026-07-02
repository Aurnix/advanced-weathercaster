"""LightGBM models: one binary model per predictand x lead, plus a 4-class
conditions model per lead.

Design decisions (plan §7): monotone-decreasing constraints in slp and d3h
for the precip and pfall heads (physically sound; makes distilled tables
smoother); per-station weights proportional to 1/row-count so every station
gets equal voice; NO class reweighting — we need calibrated probabilities and
imbalance is handled by calibration, not by distorting the loss.
"""

from __future__ import annotations

from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

NUMERIC = ["slp", "d1h", "d3h", "d6h", "d12h", "curv3h", "hf_var",
           "temp_c", "doy_sin", "doy_cos", "solar_sin", "solar_cos",
           "lat", "lon"]
CATEGORICAL = ["slp_source", "wind_class", "wind_change", "sky_state",
               "cloud_coarse", "lat_band"]
CIRCULAR_INT = ["wind_sector", "wind_rel8"]   # categorical ints with NaN
FEATURES = NUMERIC + CATEGORICAL + CIRCULAR_INT

MONOTONE_TARGETS = ("precip", "pfall")   # decreasing in slp and d3h

PARAMS = dict(
    objective="binary",
    num_leaves=63,
    learning_rate=0.05,
    min_data_in_leaf=200,
    feature_fraction=0.8,
    bagging_fraction=0.8,
    bagging_freq=1,
    verbosity=-1,
)


def prep_matrix(df: pd.DataFrame,
                features: list[str] | None = None) -> pd.DataFrame:
    features = features or FEATURES
    x = df[features].copy()
    for c in CATEGORICAL:
        if c in features:
            x[c] = x[c].astype("category")
    for c in CIRCULAR_INT:
        if c in features:
            x[c] = x[c].fillna(-1).astype(int).astype("category")
    return x


def station_weights(station_ids: pd.Series) -> np.ndarray:
    counts = station_ids.value_counts()
    w = station_ids.map(1.0 / counts).to_numpy()
    return w * len(w) / w.sum()


def monotone_constraints(target: str,
                         features: list[str] | None = None) -> list[int] | None:
    if not target.startswith(MONOTONE_TARGETS):
        return None
    features = features or FEATURES
    cons = [0] * len(features)
    for f in ("slp", "d3h"):
        if f in features:
            cons[features.index(f)] = -1
    return cons


def train_binary(train: pd.DataFrame, val: pd.DataFrame, target: str,
                 num_boost_round: int = 2000,
                 features: list[str] | None = None) -> lgb.Booster:
    features = features or FEATURES
    cats = [c for c in CATEGORICAL + CIRCULAR_INT if c in features]
    ok_tr = train[target].notna()
    ok_va = val[target].notna()
    x_tr = prep_matrix(train[ok_tr.to_numpy()], features)
    x_va = prep_matrix(val[ok_va.to_numpy()], features)
    params = dict(PARAMS)
    cons = monotone_constraints(target, features)
    if cons:
        params["monotone_constraints"] = cons
    dtrain = lgb.Dataset(
        x_tr, label=train.loc[ok_tr, target].astype(int),
        weight=station_weights(train.loc[ok_tr, "station_id"]),
        categorical_feature=cats)
    dval = lgb.Dataset(
        x_va, label=val.loc[ok_va, target].astype(int),
        weight=station_weights(val.loc[ok_va, "station_id"]),
        reference=dtrain)
    return lgb.train(params, dtrain, num_boost_round=num_boost_round,
                     valid_sets=[dval],
                     callbacks=[lgb.early_stopping(50, verbose=False)])


def train_conditions(train: pd.DataFrame, val: pd.DataFrame, lead: int,
                     num_boost_round: int = 2000) -> lgb.Booster:
    target = f"cond_{lead}h"
    ok_tr = train[target].notna()
    ok_va = val[target].notna()
    params = dict(PARAMS, objective="multiclass", num_class=4)
    dtrain = lgb.Dataset(
        prep_matrix(train[ok_tr.to_numpy()]),
        label=train.loc[ok_tr, target].astype(int),
        weight=station_weights(train.loc[ok_tr, "station_id"]),
        categorical_feature=CATEGORICAL + CIRCULAR_INT)
    dval = lgb.Dataset(
        prep_matrix(val[ok_va.to_numpy()]),
        label=val.loc[ok_va, target].astype(int),
        weight=station_weights(val.loc[ok_va, "station_id"]),
        reference=dtrain)
    return lgb.train(params, dtrain, num_boost_round=num_boost_round,
                     valid_sets=[dval],
                     callbacks=[lgb.early_stopping(50, verbose=False)])


def predict(booster: lgb.Booster, df: pd.DataFrame,
            features: list[str] | None = None) -> np.ndarray:
    return booster.predict(prep_matrix(df, features))


def save(booster: lgb.Booster, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    booster.save_model(str(path))


def load(path: Path) -> lgb.Booster:
    return lgb.Booster(model_file=str(path))
