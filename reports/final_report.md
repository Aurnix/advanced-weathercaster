# NEOSAGER — Final Report

**Question:** How much forecast skill is extractable from Sager-class
instruments (barometer history, GPS, clock, optional human wind/sky
observations), and does a lookup table fit to 35 years of data beat the one
Raymond Sager fit by hand in 1942?

**Answer:** A great deal more than the 1942 dial extracts — and yes,
decisively, everywhere, at every lead time, including after compression to
a 15 KB integer artifact that runs in under ~2,000 integer ops.

All numbers below are Brier Skill Score (BSS) vs per-station-month
climatology on held-out test years 2020–2024 at 283 North-American stations
(cell A; splits by station AND year, purged windows, calibration on a
dedicated 2019 fold; block-bootstrap CIs by station-week). Full methodology:
`docs/decisions.md`; per-milestone detail in the sibling reports.

## 1. The Sager verification (first published large-scale test, we believe)

3.5M test forecasts, identical information diet as all other models:

| P(precip in window) | 6h | 12h | 24h | 36h |
|---|---|---|---|---|
| Sager (calibrated)  | **0.209** | 0.128 | 0.050 | 0.002 |
| Zambretti (calibrated) | −0.058 | −0.065 | −0.080 | — |
| Persistence | 0.105 | −0.179 | −0.654 | — |

- **The dial has genuine skill and its marketing was honest**: real skill in
  its claimed 12–24h envelope, decaying to exactly zero at 36h.
- **Sager ≫ Zambretti.** Pressure-only Zambretti cannot beat station
  climatology at all; Sager's wind/sky inputs carry the real information.
- **Regime fingerprint** (6h precip BSS): NE-continental 0.27 and Great
  Plains 0.23 (frontal weather — its design domain) down to Mountain West
  0.09, negative by 24h (orographic/convective precip defeats sea-level
  pressure logic). Conditions-class Heidke 0.15 (vs Zambretti 0.06);
  generalizes to never-seen stations nearly without loss.

## 2. The learned model (LightGBM, ~18M training examples)

| P(precip) | 6h | 12h | 24h | 36h |
|---|---|---|---|---|
| GBM | **0.377** | 0.311 | 0.243 | 0.199 |
| GBM − Sager (95% CI) | +0.169 ±0.002 | +0.183 ±0.002 | +0.194 ±0.003 | ~+0.20 |

- Roughly **2× Sager's skill at 6h, 5× at 24h**, and still +0.20 at 36h
  where Sager is exhausted — the same instruments carry useful information
  well past the dial's horizon when read optimally.
- Regime-uniform (0.33–0.41 at 6h across all six regimes); largest edge over
  Sager exactly where the dial fails (Mountain West +0.28).
- Wind-increase 0.36–0.41, pressure-fall 0.24–0.48. Conditions Heidke 0.36
  — beats persistence (0.28), which neither hand dial could do.
- Calibration: "likely"-band forecasts verify at 76%, ">85%" at 93%.
  Val-test gaps ≤ 0.012; no leakage tripwires.

## 3. What the human contributes

Feature-tier ablation (precip 6h): pressure-only 0.12 → +temperature 0.16 →
+manual sky/wind **0.39**. The user's 30-second observation more than
doubles short-lead skill — the strongest justification for keeping the
Sager-style manual entry UX. Trained with input-masking, one model degrades
gracefully: 100%-masked (pressure-only mode) still scores 0.15, beating a
dedicated pressure-only model.

## 4. The deployable artifact

Two compressed forms were built (per plan Options A/B), both with the
isotonic calibration baked into per-head z→prob LUTs and integer-exact
reference implementations:

| | size | precip 6/12/24h | pfall 6h | windup 12h |
|---|---|---|---|---|
| GBM (teacher) | ~5 MB | 0.377 / 0.311 / 0.243 | 0.481 | 0.411 |
| **B: int8 MLP (SHIPPED)** | **15.1 KB** | 0.332 / 0.244 / 0.158 | 0.294 | 0.353 |
| A: additive int8 tables (fallback) | 2.5 KB | 0.316 / 0.222 / 0.133 | 0.191 | 0.286 |
| Sager dial (1942) | ~2 KB equiv. | 0.209 / 0.128 / 0.050 | — | ~0.02 |

- The MLP wins every head within the 32–64 KB budget (int8 quantization with
  power-of-two scales costs ≈0.001 BSS; verified integer-exact).
- Even the 2.5 KB fallback — the same byte class as the dial itself — beats
  Sager on every precipitation head.
- Reference implementations: `deploy/infer_int_mlp.py` (primary),
  `deploy/infer_int.py` (fallback), both pure-integer, < ~2,000 ops per
  full 9-head refresh, equivalence-tested. Verbalizer
  (`deploy/verbalize.py`) is threshold-only and property-tested; its verbal
  categories verify within their bands on test data.

## 5. Honest limitations

- pfall retains only ~60% of teacher skill even in the MLP — smooth
  curve-extrapolation resists small-model compression; the distilled pfall
  gains came largely from an explicit solar-time input (residual
  atmospheric tide).
- Training simulates watch inputs from ISD observations: hourly (not
  10-min) pressure for the HF-variance feature, professional sky reports as
  a proxy for user observations, cloud-type mostly missing in the modern
  era. Device-side behavior on real user-entered data is unvalidated.
- North America only (user decision to defer the global set); regimes
  outside Florida–Alaska analogs are extrapolation.
- The tide on/off ablation is label-confounded for pfall (documented in
  decisions.md); only the precip rows are a clean feature-side comparison.

## 6. Reproduction

`README.md` → pipeline stages; every stage is config-driven, idempotent and
resumable; every filtering decision logged to `<data_root>/ledger.jsonl`;
49-test pytest suite covers parsers, labels, causality, Sager goldens
(5,400 cross-executed combinations), verbalizer properties, and both
integer inference paths.
