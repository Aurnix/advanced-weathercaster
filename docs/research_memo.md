# NEOSAGER — Research memo: ranked improvements to the full-model ceiling

*(Produced 2026-07-04 by a dedicated research pass over the repo + literature.
Scope: raise teacher-level skill with runtime inputs held fixed; training-side
resources unconstrained. Quantization/deployment concerns excluded by request.)*

## 0. Where the skill actually is

1. **The manual inputs are the model** at short leads (precip_6h: 0.12
   pressure-only -> 0.39 full; sky_state alone = 49% of GBM gain). Short-lead
   headroom = extract more from the pressure buffer + don't degrade when real
   amateurs replace ISD professionals.
2. **The lead-time curve is remarkably flat** (0.44 @ 3h -> 0.20 @ 36h,
   regime-uniform): the 12-36h skill carrier is synoptic, pressure-visible
   structure — sharpen it with better labels/teachers and low-frequency
   pressure features. Convective regimes (Gulf 0.33 @ 6h) won't be rescued by
   any fixed-input change.
3. **The weakest heads are noisiest-labeled or rarest** (direction 0.26-0.28,
   gale recall 0.28): label engineering + distributional losses, not features.

Honest ceiling: obs-only point forecasting cannot see upstream air. NWS
TPB 483 found local-obs predictors' contribution "decreased rapidly by 18
hours"; nowcasting literature hits an information wall ~7-8h without
surrounding-area data. Everything below combined ~ +0.04-0.08 BSS at 6-12h
precip and +0.02-0.04 at 24-36h — worthwhile, not another doubling. The
bigger wins are new capabilities (precip type, temp trend, calibrated gale
risk) and closing sim-to-device gaps.

## 1. Ranked candidates

| # | Improvement | Heads helped | Expected gain | Cost | Risk |
|---|---|---|---|---|---|
| 1 | Sub-hourly pressure features on ASOS 1-min data (closes hf_var sim-to-device gap) | precip/windup/cond <=12h | +0.01-0.04 BSS @ 3-6h; removes unknown-sign device regression | Med | 1-min data messy; ~900 US stations post-2000 |
| 2 | ERA5-teacher LUPI distillation (privileged upstream fields -> soft labels for device-input student) | all, esp. 12-36h precip, gale | +0.01-0.03 @ 12-24h; more on rare classes | Med-high | Can be ~0 where student saturates its inputs |
| 3 | Precip-type (rain/snow) + temperature-trend heads | two new heads | New capability; ptype Heidke >=0.5 with temp input | Low | Shoulder-season errors without humidity |
| 4 | On-device online recalibration (pfall self-verifies from the watch's own barometer) + per-regime calibration | calibration everywhere | +0.01-0.03 local BSS after ~1 season | Med | Small-sample variance; gate + shrink |
| 5 | Distributional wind: quantile/CRPS speed + circular (von Mises) direction | gale risk, direction | Gale recall 0.28 -> ~0.35-0.45 @ fixed FAR; dir +0.02-0.05 | Low-med | Direction near input-limited ceiling |
| 6 | Radar/gauge-fused precip labels (Stage IV 2002+, MRMS 2014+) as negative-label veto | precip heads | +0.005-0.02; better reliability | Med | Label-definition consistency across eras |
| 7 | Amateur-observer noise augmentation (sky +/-1 class, sector +/-1...) | all manual-input skill | Insurance for the 0.27 BSS manual inputs carry | Low | None serious |
| 8 | Cloud-type rescue (train on GF1-rich 1990s subset) | precip 6h when user enters cloud | +0.005-0.015 conditional | Low | Era-shift confounding |
| 9 | Geographic-context lookups from GPS (coast distance, terrain, storm-track climatology embedding) | regime tails, direction | +0.01-0.02 in mountain/coastal tails | Med | Leakage discipline |
| 10 | Small TCN/GRU over raw 10-min buffer, ensembled with GBM | pfall, precip <=6h | +0.01-0.02; pfall 6h maybe +0.03 | Med-high | Often ties tabular incumbent |
| 11 | Multi-task/stacked heads (sibling OOF predictions as features) | rare heads | +0.005-0.015 | Low | OOF leakage discipline |
| 12 | More stations (global ISD, MADIS mesonets) | generalization | +0.005 on NA test; large for global validity | Med | Mesonet QC poor |
| 13 | 48h lead extension + trend verbalization | new leads | ~0.15 BSS @ 48h (curve extrapolation) | Low | Verbal overpromise risk |

Not ranked: per-season/per-regime model splits (GBM already learns those
interactions — the tide ablation proved it) .

**Best bang-for-buck: #1. Highest ceiling: #2 (+#6, shared infra).**

## 2. Top-5 deep dives

### 2.1 (#1) ASOS 1-min pressure features
`hf_var` is trained on hourly detrended std but the device computes it from
10-min samples — a live sim-to-device bug. The 20min-3h pressure-perturbation
band (fronts, outflows, wake lows, gravity waves; 0.2-4 hPa) is detectable by
wavelet thresholding in single-sensor series and co-occurs overwhelmingly
with frontal/winter-storm precip. Features (all device-computable from a 24h
x 10-min ring buffer): multi-scale detrended std (1/3/6h), max 30-min
drop/rise, 2-3 wavelet band powers (20-60min, 1-3h), time-since-last-jump
>=0.5 hPa/30min, d30min. Data: ASOS 1-min DSI-6406 (~900 US stations,
2000+, NCEI /pub/data/asos-onemin/, IEM mirror), decimate to 10-min, join to
existing labels/splits; features "missing" where absent (masking machinery
already handles this). Use robust stats (MAD) — 1-min pressure is dirty.

### 2.2 (#2) ERA5 privileged-information distillation
Distillation can't inject information the student's inputs lack; it replaces
noisy 0/1 labels with the teacher's conditional event probability given full
atmospheric state — variance-reduced targets. Gains concentrate where labels
are noisy or events rare (12-36h precip, gale, direction), vanish where the
student saturates (precip_3h). Build: ERA5 point + upstream (W/SW 100-500km)
predictors at station-hours (trivial volume) -> teacher GBM on [device +
ERA5] -> student on soft targets (lambda*teacher + (1-lambda)*label,
lambda 0.5-0.8 tuned on val; LightGBM xentropy). Keep 2019 isotonic. Teacher
soft labels correlate errors across nearby stations — keep station-week
block bootstrap. Twin #6: Stage IV/MRMS QPE as a veto on ISD negatives
post-2002 (cheapest form; keeps label definition stable).

### 2.3 (#3) Precip-type + temperature-trend heads
Highest user-visible value per hour. Labels already parsed (MW/AW snow/
sleet/freezing codes; temp_c in hourly frame). ptype = {rain, mixed/frz,
snow} | precip; dtemp_{6,12}h 3-class (falling>2C / steady / rising>2C).
Rain/snow threshold ~1.0C air temp (Jennings 2018, 17.8M obs) -> with device
temp + lat/elev/doy expect Heidke >=0.5. Watch temp is wrist-biased: wire as
optional masked input like the manual group. Accept shoulder-season errors
(no humidity at runtime) and calibrate.

### 2.4 (#4) Online recalibration
The watch self-verifies pfall labels (pressure is both input and outcome)
and partially verifies precip/wind via later user entries. Simulate
training-side first: per test station, chronological forecasts through a
recency-weighted isotonic / 2-param Platt update on the last N self-verified
pairs; measure BSS vs frozen calibration vs history length. Zero-risk first
step: per-regime calibration at train time (pfall base rates differ 5x
across regimes; one isotonic map is stretched thin). Gains concentrate at
stations unlike their regime average — exactly the deployment case.

### 2.5 (#5) Distributional wind heads
Speed: LightGBM quantile heads (q50/q80/q95 of window-max) or CRPS-trained
parametric head; gale risk becomes a calibrated exceedance probability
(expect recall 0.28 -> 0.35-0.45 at fixed FAR, esp. with #2's soft labels).
Rare-event categorical scores have base-rate ceilings (WAF 2013) — report
exceedance probability + reliability, don't chase Heidke on gale. Direction:
ordinal-with-sign encoding, or von Mises circular head (circular regression
forests), or ERA5-teacher soft labels; +0.02-0.05 Heidke, plausibly near the
input-limited ceiling already.

## 3. Do NOT
- Chase 36h+ skill via model changes (local-obs signal spent by ~18-24h;
  0.199 @ 36h is mostly climatology+trend). 48h is a product decision with
  honest hedging.
- Replace the GBM with a sequence model wholesale — challenger on pfall only.
- Split models per season/regime.

## 4. Sequencing
1. #7 noise augmentation + #3 new heads (days, no new data).
2. #1 ASOS 1-min ingest + buffer features (1-2 wk) — largest verified gain.
3. #2/#6 ERA5 teacher + radar veto (2-4 wk, shared infra) — ceiling raiser;
   keep per-head only where val improves.
4. #5 distributional wind heads (using teacher soft labels).
5. #4 recalibration simulation harness (informs firmware design).

*(Source links preserved in the original agent output; key ones: NCEI
DSI-6406 / asos-onemin, IEM 1-min download, AMT 2024 wavelet detection,
Karlsson et al. arXiv:2110.14993, NeurIPS 2022 privileged-features
distillation, Jennings et al. 2018 Nature Comms, circular regression forests
arXiv:2001.00412, online recalibration arXiv:2409.19157, WAF 2013 rare-event
limits, NWS TPB 483.)*
