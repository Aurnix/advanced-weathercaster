"""Option-B final artifact: per-head MLP (binned one-hot inputs -> 16 -> 12
-> logit) trained against the GBM teacher, quantized to int8 with
POWER-OF-TWO layer scales so device requantization is pure bit-shifts.

Because inputs are one-hot bins, layer 1 is not a matmul on device: it is
14 row-lookups summed (exactly like additive tables, but into a 16-vector).
Layers 2/3 are tiny int8 MACs. The head's isotonic calibration is composed
into the final z->prob LUT, as with the tables.

Fixed-point contract (mirrored by deploy/infer_int_mlp.py):
- a1 = relu(sum W1q_rows + b1q)            # int32, scale 2^-S1 "units"
- a2 = relu((W2q @ a1 + b2q) >> S2)        # back to 2^-S1 units
- z  = ((w3q @ a2 + b3q) >> S3)            # 1/16-logit units
- prob = LUT64[z] with integer interpolation
"""

from __future__ import annotations

import numpy as np
from sklearn.neural_network import MLPRegressor

from .distill import LUT_SIZE, Z_RANGE

BIN_KEYS = ["slp", "d3h", "d6h", "d12h", "d1h", "hf", "curv", "solar8",
            "wind_rel", "wind_chg", "sky", "band", "season", "wclass"]


def _pow2_scale(w: np.ndarray) -> int:
    """Smallest shift k with max|w| <= 127 * 2^-k (k may be negative)."""
    m = float(np.abs(w).max()) or 1e-9
    k = int(np.floor(np.log2(127.0 / m)))
    return k


def train_head(X_onehot, z_teacher, seed: int = 0) -> MLPRegressor:
    mlp = MLPRegressor(hidden_layer_sizes=(16, 12), max_iter=80,
                       early_stopping=False, random_state=seed)
    mlp.fit(X_onehot, z_teacher)
    return mlp


def quantize_head(mlp: MLPRegressor, bin_sizes: list[int]) -> dict:
    """Returns the integer artifact for one head (weights, shifts, layout).

    Layer-1 rows are grouped per input field so the device can index
    field-locally: W1 has sum(bin_sizes) rows of 16.
    """
    W1, W2, w3 = mlp.coefs_
    b1, b2, b3 = mlp.intercepts_

    S1 = _pow2_scale(W1)
    W1q = np.clip(np.round(W1 * 2 ** S1), -127, 127).astype(np.int8)
    b1q = np.clip(np.round(b1 * 2 ** S1), -2**31, 2**31 - 1).astype(np.int32)

    S2 = _pow2_scale(W2)
    W2q = np.clip(np.round(W2 * 2 ** S2), -127, 127).astype(np.int8)
    # b2 lives in the accumulator scale 2^-(S1+S2)
    b2q = np.round(b2 * 2 ** (S1 + S2)).astype(np.int64)

    S3 = _pow2_scale(w3)
    w3q = np.clip(np.round(w3 * 2 ** S3), -127, 127).astype(np.int8)
    # output wanted in 1/16-logit units: z_float = acc * 2^-(S1+S3); we
    # shift by (S1 + S3 - 4) so one unit = 2^-4 logit
    b3q = np.round(b3 * 2 ** (S1 + S3)).astype(np.int64)
    out_shift = S1 + S3 - 4

    return {
        "bin_sizes": bin_sizes,
        "W1": W1q.tolist(), "b1": b1q.tolist(), "S1": S1,
        "W2": W2q.T.tolist(), "b2": b2q.tolist(), "S2": S2,
        "w3": w3q.ravel().tolist(), "b3": int(b3q.ravel()[0]),
        "S3": S3, "out_shift": out_shift,
        "bytes": int(W1q.size + W2q.size + w3q.size
                     + 4 * len(b1q) + 8 * len(b2q) + 8 + LUT_SIZE),
    }


def predict_quantized(head: dict, bins_matrix: np.ndarray) -> np.ndarray:
    """Vectorized reference of the integer forward pass (float container,
    integer-exact values). bins_matrix: (n, 14) ints in BIN_KEYS order."""
    W1 = np.asarray(head["W1"], dtype=np.int64)
    b1 = np.asarray(head["b1"], dtype=np.int64)
    W2 = np.asarray(head["W2"], dtype=np.int64)      # (12, 16)
    b2 = np.asarray(head["b2"], dtype=np.int64)
    w3 = np.asarray(head["w3"], dtype=np.int64)
    offsets = np.concatenate([[0], np.cumsum(head["bin_sizes"])[:-1]])

    idx = bins_matrix + offsets                      # (n, 14) row indices
    a1 = W1[idx].sum(axis=1) + b1                    # (n, 16)
    a1 = np.maximum(a1, 0)
    acc2 = a1 @ W2.T + b2                            # (n, 12)
    S2 = head["S2"]
    a2 = np.maximum(_shift(acc2, S2), 0)
    z_acc = a2 @ w3 + head["b3"]
    z = _shift(z_acc, head["out_shift"])
    return z.astype(float) / 16.0                    # logits


def _shift(x: np.ndarray, s: int) -> np.ndarray:
    """Arithmetic right shift by s (left shift if negative), rounding toward
    -inf like hardware >>."""
    if s >= 0:
        return np.floor_divide(x, 2 ** s)
    return x * 2 ** (-s)
