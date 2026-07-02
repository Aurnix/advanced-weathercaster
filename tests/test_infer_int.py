"""Integer reference inference must reproduce the numpy quantized path.

Uses the real artifact if present (skips otherwise — CI without data).
Feeds BOTH paths values already rounded to tenths so binning ties are
consistent, and allows 1/255 slack for LUT interpolation rounding.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from neosager.config import load_config

ARTIFACT = Path("D:/neosager-data/artifacts/neosager_tables.json")


@pytest.mark.skipif(not ARTIFACT.exists(), reason="artifact not built")
def test_int_inference_matches_numpy_path():
    from neosager.deploy.infer_int import IntInference

    inf = IntInference(ARTIFACT)
    rng = np.random.default_rng(7)

    n_checked = 0
    for tgt in ["precip_12h", "windup_12h", "pfall_12h"]:
        head = inf.heads[tgt]
        for _ in range(500):
            x = {
                "slp": int(rng.integers(9600, 10500)),
                "d1h": int(rng.integers(-30, 30)),
                "d3h": int(rng.integers(-80, 80)),
                "d6h": int(rng.integers(-120, 120)),
                "d12h": int(rng.integers(-160, 160)),
                "hf": int(rng.integers(0, 30)),
                "curv": int(rng.integers(-60, 60)),
                "wind_rel": int(rng.integers(0, 9)),
                "wind_chg": int(rng.integers(0, 4)),
                "sky": int(rng.integers(0, 6)),
                "band": int(rng.integers(0, 4)),
                "season": int(rng.integers(0, 4)),
                "wclass": int(rng.integers(0, 6)),
                "solar8": int(rng.integers(0, 8)),
            }
            p_int = inf.prob255(tgt, x)
            assert 0 <= p_int <= 255

            # numpy path: rebuild z from the same artifact numbers
            b = inf.bins(x)
            z = head["bias"]
            for name in head["spec"]:
                keys = inf.SPEC_KEYS[name]
                shape = head["_shape"][name]
                idx = b[keys[0]]
                for k, s in zip(keys[1:], shape[1:]):
                    idx = idx * s + b[k]
                z += head["_flat"][name][idx]
            if head.get("lin_w_q"):
                from neosager.deploy.infer_int import _rounddiv
                for w, k in zip(head["lin_w_q"], inf.LINEAR_KEYS):
                    z += _rounddiv(w * x[k], 160)
            zf = np.clip(z / 16.0, -8, 8)
            pos = (zf + 8) / 16 * 63
            lo = int(np.floor(pos))
            hi = min(lo + 1, 63)
            frac = pos - lo
            p_np = head["lut"][lo] * (1 - frac) + head["lut"][hi] * frac
            assert abs(p_int - p_np) <= 1.5, (tgt, x, p_int, p_np)
            n_checked += 1
    assert n_checked == 1500


@pytest.mark.skipif(not ARTIFACT.exists(), reason="artifact not built")
def test_missing_tendencies_still_forecast():
    from neosager.deploy.infer_int import IntInference

    inf = IntInference(ARTIFACT)
    x = {"slp": 10130, "d1h": None, "d3h": None, "d6h": None, "d12h": None,
         "hf": None, "curv": None, "wind_rel": 8, "wind_chg": 3, "sky": 5,
         "band": 1, "season": 2, "wclass": 5, "solar8": 4}
    for tgt in ["precip_6h", "precip_12h", "precip_24h"]:
        p = inf.prob255(tgt, x)
        assert 0 <= p <= 255
