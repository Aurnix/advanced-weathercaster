"""Integer-only reference inference for the distilled artifact.

No floats, no numpy — every operation here maps 1:1 onto Monkey C integer
arithmetic. This file IS the deployment spec; a watch port should follow it
line by line (see deploy/README.md for the byte/op budget).

Fixed-point conventions:
- pressures & tendencies: tenths of hPa (int) — the device's native unit
- table entries: 1/16-logit units (int8)
- linear weights: 1/256 logit per hPa (int16);
  contribution in 1/16-logit units = (w * x_tenths) rounddiv 160
- probabilities: 0..255 (uint8), via per-head 64-entry LUT over [-8, +8]
  logits with integer linear interpolation
"""

from __future__ import annotations

import json
from pathlib import Path

LOGIT_SCALE = 16
LUT_SIZE = 64
Z_UNITS_RANGE = 128           # 8 logits * 16 units


def _rounddiv(a: int, b: int) -> int:
    """Round-half-away-from-zero integer division (Monkey C friendly)."""
    if a >= 0:
        return (a + b // 2) // b
    return -((-a + b // 2) // b)


def _bin(x_tenths: int | None, edges_tenths: list[int],
         missing_bin: int) -> int:
    if x_tenths is None:
        return missing_bin
    b = 0
    for e in edges_tenths:
        if x_tenths >= e:
            b += 1
    return b


class IntInference:
    """Loads the JSON artifact and answers with 0-255 probabilities."""

    # table-name -> input key tuple (mirrors distill.TABLE_SPEC/PFALL_SPEC)
    SPEC_KEYS = {
        "t_slp_d3h": ("slp", "d3h"), "t_trend": ("d3h", "d6h"),
        "t_fine": ("d1h", "d3h", "d6h"), "t_d12h": ("d12h",),
        "t_hf": ("hf",), "t_curv": ("curv",),
        "t_solar": ("solar8", "band"),
        "t_wind": ("wind_rel", "wind_chg"), "t_wclass": ("wclass",),
        "t_sky": ("sky",), "t_geo": ("band", "season"),
    }
    LINEAR_KEYS = ("d1h", "d3h", "d6h", "d12h")

    def __init__(self, artifact_path: Path):
        with open(artifact_path, encoding="utf-8") as f:
            art = json.load(f)
        m = art["meta"]
        self.edges = {
            "slp": [round(e * 10) for e in m["slp_edges"]],
            "d3h": [round(e * 10) for e in m["d3h_edges"]],
            "d12h": [round(e * 10) for e in m["d12h_edges"]],
            "d6h": [round(e * 10) for e in m["d6h_edges"]],
            "d1h": [round(e * 10) for e in m["d1h_edges"]],
            "hf": [round(e * 10) for e in m["hf_edges"]],
            "curv": [round(e * 10) for e in m["curv_edges"]],
        }
        self.heads = art["heads"]
        # flatten nested table lists once at load
        for h in self.heads.values():
            h["_flat"] = {name: _flatten(t)
                          for name, t in h["tables"].items()}
            h["_shape"] = {name: _shape(t)
                           for name, t in h["tables"].items()}

    def bins(self, x: dict) -> dict[str, int]:
        """x: raw integer inputs. Numeric keys in tenths of hPa (None ok);
        categorical keys already small ints."""
        out = {}
        for k, edges in self.edges.items():
            n = len(edges) + 1
            missing = 0 if k == "hf" else n // 2
            out[k] = _bin(x.get(k), edges, missing)
        for k in ("wind_rel", "wind_chg", "sky", "band", "season",
                  "wclass", "solar8"):
            out[k] = int(x[k])
        return out

    def prob255(self, target: str, x: dict) -> int:
        head = self.heads[target]
        b = self.bins(x)
        z = head["bias"]
        for name in head["spec"]:
            keys = self.SPEC_KEYS[name]
            shape = head["_shape"][name]
            idx = b[keys[0]]
            for k, s in zip(keys[1:], shape[1:]):
                idx = idx * s + b[k]
            z += head["_flat"][name][idx]
        if head.get("lin_w_q"):
            for w, k in zip(head["lin_w_q"], self.LINEAR_KEYS):
                xt = x.get(k)
                if xt is not None:
                    z += _rounddiv(w * xt, 160)
        # LUT lookup with integer interpolation
        pos = z + Z_UNITS_RANGE            # 0..256 within range
        if pos < 0:
            pos = 0
        if pos > 2 * Z_UNITS_RANGE:
            pos = 2 * Z_UNITS_RANGE
        num = pos * (LUT_SIZE - 1)         # 0..256*63
        i = num // (2 * Z_UNITS_RANGE)
        frac = num % (2 * Z_UNITS_RANGE)
        lut = head["lut"]
        j = i + 1 if i + 1 < LUT_SIZE else i
        return _rounddiv(lut[i] * (2 * Z_UNITS_RANGE - frac)
                         + lut[j] * frac, 2 * Z_UNITS_RANGE)


def _flatten(t) -> list[int]:
    if isinstance(t[0], list):
        return [v for sub in t for v in _flatten(sub)]
    return list(t)


def _shape(t) -> list[int]:
    s = []
    while isinstance(t, list):
        s.append(len(t))
        t = t[0]
    return s
