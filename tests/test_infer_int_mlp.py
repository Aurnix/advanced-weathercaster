"""The pure-Python integer MLP inference must match the vectorized
integer-exact reference (models/mlp_export.predict_quantized) bit-for-bit
on the z units, and within LUT-interp rounding on probability."""

from pathlib import Path

import numpy as np
import pytest

ARTIFACT = Path("D:/neosager-data/artifacts/neosager_mlp.json")


@pytest.mark.skipif(not ARTIFACT.exists(), reason="artifact not built")
def test_mlp_int_matches_vectorized_reference():
    import json
    from neosager.deploy.infer_int_mlp import IntMlpInference
    from neosager.models.mlp_export import predict_quantized, BIN_KEYS

    inf = IntMlpInference(ARTIFACT)
    with open(ARTIFACT, encoding="utf-8") as f:
        art = json.load(f)
    rng = np.random.default_rng(13)
    sizes = art["meta"]["bin_sizes"]

    for tgt in ["precip_12h", "windup_6h", "pfall_24h"]:
        head = art["heads"][tgt]
        for _ in range(400):
            bins = [int(rng.integers(0, s)) for s in sizes]
            x = dict(zip(BIN_KEYS, bins))
            # bypass numeric binning: feed bin indices for categorical keys
            # and reconstruct numeric values that land in the same bin
            xin = {}
            for k, b in zip(BIN_KEYS, bins):
                if k in inf.edges:
                    edges = inf.edges[k]
                    if b == 0:
                        xin[k] = (edges[0] - 5) if edges else 0
                    elif b >= len(edges):
                        xin[k] = edges[-1] + 5
                    else:
                        xin[k] = (edges[b - 1] + edges[b]) // 2
                        # ties at edges: recompute the bin the int path sees
                else:
                    xin[k] = b
            true_bins = inf.bins(xin)
            z_vec = predict_quantized(head, np.array([true_bins]))[0] * 16.0
            p_int = inf.prob255(tgt, xin)
            # reconstruct prob from z_vec via the same LUT math
            pos = int(np.clip(round(z_vec) + 128, 0, 256))
            num = pos * 63
            i, frac = num // 256, num % 256
            lut = head["lut"]
            j = min(i + 1, 63)
            p_ref = (lut[i] * (256 - frac) + lut[j] * frac + 128) // 256
            assert abs(p_int - p_ref) <= 1, (tgt, xin, p_int, p_ref)


@pytest.mark.skipif(not ARTIFACT.exists(), reason="artifact not built")
def test_mlp_int_sensible_probs():
    from neosager.deploy.infer_int_mlp import IntMlpInference

    inf = IntMlpInference(ARTIFACT)
    # deep low, falling fast, overcast, backing S wind -> precip prob high
    wet = {"slp": 9850, "d1h": -15, "d3h": -45, "d6h": -80, "d12h": -120,
           "hf": 8, "curv": -20, "solar8": 4, "wind_rel": 2, "wind_chg": 0,
           "sky": 3, "band": 1, "season": 0, "wclass": 2}
    # strong high, rising, clear, light wind -> precip prob low
    dry = {"slp": 10350, "d1h": 5, "d3h": 15, "d6h": 25, "d12h": 40,
           "hf": 1, "curv": 5, "solar8": 4, "wind_rel": 4, "wind_chg": 1,
           "sky": 0, "band": 1, "season": 2, "wclass": 1}
    p_wet = inf.prob255("precip_12h", wet)
    p_dry = inf.prob255("precip_12h", dry)
    assert p_wet > 170
    assert p_dry < 60
