# NEOSAGER deployment spec

**Primary artifact: `neosager_mlp.json` (15.1 KB)** — 9 probability heads
(precip/windup/pfall × 6/12/24 h), each a binned-input int8 MLP
(one-hot bins → 16 → 12 → logit) with power-of-two layer scales and the
isotonic calibration composed into a per-head 64-entry probability LUT.
`infer_int_mlp.py` is the normative integer-only reference. Because inputs
are one-hot bins, layer 1 is 14 row-lookups summed — no matmul; layers 2/3
are tiny int8 MACs with bit-shift requantization. Full 9-head refresh:
< ~2,000 integer ops.

**Fallback artifact: `neosager_tables.json` (2.5 KB)** — GAM-style additive
int8 logit tables (`infer_int.py` reference), for extreme memory budgets;
retains less skill (see reports/final_report.md §4) but still beats the
1942 Sager dial on every precipitation head at the dial's own byte size.
The sections below document the fallback's original budget; input
conventions (bottom) are IDENTICAL for both artifacts.

## Byte budget (52-station artifact, v4)

| component | bytes |
|---|---|
| precip/windup heads: 6 × 230 B (tables 164 + bias 2 + LUT 64) | 1,380 |
| pfall heads: 3 × 367 B (tables ~293 + bias 2 + lin 8 + LUT 64) | 1,101 |
| shared bin edges (7 numeric dims, int16 tenths) | ~80 |
| **total** | **~2.6 KB** |

Budget from the project brief: 32–64 KB. Headroom ≈ 25×.

## Op budget per head (worst case, pfall)

| step | integer ops |
|---|---|
| bin 7 numeric inputs (edge compares) | ≤ 40 cmp |
| 7 table lookups (index arithmetic + fetch) | ~25 |
| 4 linear terms (mul + rounddiv) | ~12 |
| LUT interpolation | ~10 |
| **total** | **< 100 ops/head, < 900 for all 9** |

No floats, no exp/log, no division except by constants. A 12-entry forecast
refresh is microseconds even on a watch MCU.

## Input conventions

- Pressure quantities in **tenths of hPa** (int): sea-level-reduced station
  pressure after the tide correction (see below), tendencies d1h/d3h/d6h/
  d12h, curvature (d3h(t) − d3h(t−3h)), hf variability (std of detrended
  hourly pressure, trailing 6 h, tenths).
- Sea-level reduction: `p_sl = p_stn * exp(g M h / (R T))` — on device use
  the standard lookup/approximation with GPS elevation h; temperature term
  optional (watch temp is body-heat polluted; standard atmosphere is fine).
- Tide correction (subtract BEFORE tendencies):
  `1.16 cos³(lat) cos(2π(t_solar − 9.97)/12) + 0.55 cos(lat) cos(2π(t_solar − 5.0)/24)` hPa,
  `t_solar = UTC_h + lon/15`. Precompute per fix; a 24-entry per-location
  table refreshed daily is equivalent.
- Categorical inputs: wind_rel (8 sectors relative to shipped prevailing-
  wind-by-month table, 8 = missing), wind_chg (0 backing / 1 steady /
  2 veering / 3 missing), sky (0 clear / 1 partly / 2 mostly / 3 overcast /
  4 precipitating / 5 missing), lat band (0: 24–35, 1: 35–45, 2: 45–55,
  3: 55+), season ((month%12)/3), wclass (0 calm / 1 light / 2 moderate /
  3 strong / 4 gale / 5 missing), solar8 (t_solar // 3).
- ALL manual inputs may be "missing" — the tables are trained with masking
  and degrade gracefully (measured: precip_12h BSS 0.23 full → 0.14 masked).

## C-like pseudocode

```c
int prob255(Head h, Inputs x) {
    int z = h.bias;                       // 1/16-logit units
    for (t in h.tables)                   // additive tables
        z += t.data[flat_index(t, x)];    // int8 fetch
    if (h.has_linear)                     // pfall heads only
        for (i in 0..3)                   // d1h,d3h,d6h,d12h in tenths
            z += rounddiv(h.linw[i] * x.tend[i], 160);
    int pos = clamp(z + 128, 0, 256);     // [-8,+8] logits
    int num = pos * 63;
    int i = num / 256, frac = num % 256;
    return rounddiv(h.lut[i]*(256-frac) + h.lut[min(i+1,63)]*frac, 256);
}
```

The verbalizer (`verbalize.py`) consumes the 9 probabilities (÷255) and is
equally portable: threshold compares and string selection only.
