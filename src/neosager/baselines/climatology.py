"""Climatology baseline AND the Brier-skill reference: P(event | station,
month, label) measured on train years, Laplace-smoothed toward the
regime x month rate for thin cells.

For test stations the station's own train-year climatology is used — that is
what a deployed product would ship for a location, and it contains no
test-year information.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..climo import climo_dir
from ..config import Config

SMOOTH_N = 200  # pseudo-count weight of the regime prior


def load_event_counts(cfg: Config, manifest: pd.DataFrame) -> pd.DataFrame:
    """All stations' per-month event counts + regime metadata."""
    d = climo_dir(cfg)
    frames = []
    for _, row in manifest.iterrows():
        p = d / f"{row['station_id']}_events.parquet"
        if not p.exists():
            continue
        e = pd.read_parquet(p)
        e["regime"] = row.get("regime", "unknown")
        frames.append(e)
    return pd.concat(frames, ignore_index=True)


class ClimatologyBaseline:
    def __init__(self, cfg: Config, manifest: pd.DataFrame):
        counts = load_event_counts(cfg, manifest)
        regime = (counts.groupby(["regime", "label", "month"])
                  .agg(n=("n", "sum"), k=("k", "sum")).reset_index())
        regime["p_regime"] = regime["k"] / regime["n"].clip(lower=1)
        counts = counts.merge(
            regime[["regime", "label", "month", "p_regime"]],
            on=["regime", "label", "month"], how="left")
        counts["p"] = ((counts["k"] + SMOOTH_N * counts["p_regime"])
                       / (counts["n"] + SMOOTH_N))
        self.table = counts.set_index(["station", "label", "month"])["p"]
        self.regime_table = regime.set_index(["regime", "label", "month"])["p_regime"]

    def predict(self, station_ids: pd.Series, months: np.ndarray,
                label: str, regimes: pd.Series | None = None) -> np.ndarray:
        keys = pd.MultiIndex.from_arrays(
            [station_ids, np.full(len(station_ids), label), months])
        p = self.table.reindex(keys).to_numpy(copy=True)
        if regimes is not None and np.isnan(p).any():
            rkeys = pd.MultiIndex.from_arrays(
                [regimes, np.full(len(regimes), label), months])
            p_r = self.regime_table.reindex(rkeys).to_numpy()
            p = np.where(np.isnan(p), p_r, p)
        return p
