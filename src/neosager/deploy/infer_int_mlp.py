"""Integer-only reference inference for the PRIMARY (MLP) artifact
`neosager_mlp.json`. Pure Python ints; maps 1:1 onto Monkey C.

Forward pass per head (see models/mlp_export.py for the training-side
contract):
  a1[16] = relu( sum over 14 input fields of W1row(field, bin) + b1 )
  a2[12] = relu( (W2 @ a1 + b2) >> S2 )
  z      = (w3 . a2 + b3) >> out_shift          # 1/16-logit units
  prob   = LUT64 interp (identical to the tables path)

Layer 1 is 14 row-lookups summed — the artifact stores W1 as
sum(bin_sizes) rows of 16 int8, grouped per input field.
"""

from __future__ import annotations

import json
from pathlib import Path

from .infer_int import _rounddiv  # shared LUT/rounding helpers

LUT_SIZE = 64
Z_UNITS_RANGE = 128


def _shift(x: int, s: int) -> int:
    """Arithmetic right shift (floor), matching numpy floor_divide."""
    if s >= 0:
        return x // (1 << s)
    return x * (1 << (-s))


class IntMlpInference:
    def __init__(self, artifact_path: Path):
        with open(artifact_path, encoding="utf-8") as f:
            art = json.load(f)
        m = art["meta"]
        self.bin_keys = m["bin_keys"]
        self.bin_sizes = m["bin_sizes"]
        self.offsets = []
        off = 0
        for s in self.bin_sizes:
            self.offsets.append(off)
            off += s
        self.edges = {k: [round(e * 10) for e in m[f"{k}_edges"]]
                      for k in ["slp", "d3h", "d12h", "d6h", "d1h",
                                "hf", "curv"]}
        self.heads = art["heads"]

    def bins(self, x: dict) -> list[int]:
        out = []
        for k in self.bin_keys:
            if k in self.edges:
                v = x.get(k)
                n = len(self.edges[k]) + 1
                if v is None:
                    b = 0 if k == "hf" else n // 2
                else:
                    b = 0
                    for e in self.edges[k]:
                        if v >= e:
                            b += 1
                out.append(b)
            else:
                out.append(int(x[k]))
        return out

    def prob255(self, target: str, x: dict) -> int:
        h = self.heads[target]
        b = self.bins(x)

        a1 = list(h["b1"])                       # int32 accumulators
        W1 = h["W1"]
        for f, bin_i in enumerate(b):
            row = W1[self.offsets[f] + bin_i]
            for j in range(16):
                a1[j] += row[j]
        for j in range(16):
            if a1[j] < 0:
                a1[j] = 0

        a2 = []
        for i, (w_row, b2i) in enumerate(zip(h["W2"], h["b2"])):
            acc = b2i
            for j in range(16):
                acc += w_row[j] * a1[j]
            acc = _shift(acc, h["S2"])
            a2.append(acc if acc > 0 else 0)

        z_acc = h["b3"]
        for i in range(12):
            z_acc += h["w3"][i] * a2[i]
        z = _shift(z_acc, h["out_shift"])

        pos = z + Z_UNITS_RANGE
        if pos < 0:
            pos = 0
        if pos > 2 * Z_UNITS_RANGE:
            pos = 2 * Z_UNITS_RANGE
        num = pos * (LUT_SIZE - 1)
        i = num // (2 * Z_UNITS_RANGE)
        frac = num % (2 * Z_UNITS_RANGE)
        lut = h["lut"]
        j = i + 1 if i + 1 < LUT_SIZE else i
        return _rounddiv(lut[i] * (2 * Z_UNITS_RANGE - frac)
                         + lut[j] * frac, 2 * Z_UNITS_RANGE)
