# Decision log

Running log of dataset filtering and methodology decisions, with rationale.
(Automated per-station-year drop counts live in `<data_root>/ledger.jsonl`.)

## 2026-07-01 / -02 — Milestone 1

- **Data cache outside OneDrive** (`D:\neosager-data`): the repo dir is
  OneDrive-synced; tens of GB of parquet writes would thrash sync and risk
  file locks mid-write. User approved.
- **Years 1990–2024, test 2020–2024; global station set deferred.** User approved.
- **REPORT_TYPE whitelist** keeps FM-12/15/16, SAO, SAOSP, S-S-A, SY-MT,
  SY-SA, SY-AE, SY-AU, SA-AU, AUTO, AERO. SOD/SOM are daily/monthly
  summaries whose 24h precip totals would poison hourly labels; BOGUS/SMARS
  excluded. SY-SA added after the smoke test showed 1,478 valid Miami-1995
  synoptic/airways rows being dropped (coverage 84% -> 100%).
- **Row-level QUALITY_CONTROL column not filtered**: it names the QC process
  (V01/V02/V03...), not a pass/fail verdict. Element-level QC flags
  {2,3,6,7} null the element instead.
- **Precip depth uses period==1h AA entries only.** 3h/6h SYNOP accumulations
  cannot be placed within a specific hour: a 6h total at t+2 could contain
  precip from before the forecast time. Stations without hourly AA reporting
  contribute precip evidence via present-weather codes (MW/AW/AU).
- **Trace (AA condition 2) is not "measurable"** — flagged, depth 0.
- **MW codes 20–29 ("precip within past hour, not now") excluded** from the
  precip evidence set; counting them would double-count event edges.
- **Sky cover falls back to max GA layer coverage** where GF1 is absent:
  modern ASOS reports layers, not GF1 totals (smoke test: Anchorage 2020 sky
  coverage 0.46 -> 1.00). Coverage code 09 (obscured) maps to 8 oktas.
- **Sub-hourly dedup**: present weather + hourly precip UNIONED across
  reports in the hour bin (SPECIs carry onsets); scalars from the report
  nearest the top of the hour (tie-break by type priority), per-scalar
  fallback to next-nearest; wind dir+speed kept as a coherent pair from one
  report.
- **Labels**: positives trusted regardless of window coverage (an observed
  event happened); negatives require >=75% of window hours observed and no
  gap >3h. A "no precip" verdict over a half-missing window inflates skill.
- **Pressure chain is device-faithful**: MA1 station pressure reduced to sea
  level by us (measured temp when present, standard atmosphere otherwise);
  ISD SLP used only as flagged fallback (`slp_source`). Tide correction
  (S2/S1 harmonics) applied before tendencies; ablation toggle in config.
- **Prevailing wind and event climatology for a test station use that
  station's own TRAIN-year data** — no test-year information; spatially it is
  what a deployed product would ship as a location lookup.
- **Splits**: examples every 3h; purge drops examples whose t+36h window
  crosses a year-fold boundary; station folds regime-stratified 85/15 seed
  42, committed in the manifest.
- **Repo-local git identity** set to Arzos <kb3fkj@gmail.com>.

## 2026-07-02 — Ablations (52 stations)

- **Tide ablation caveat**: the pfall on/off comparison is CONFOUNDED — the
  pfall label is defined on the corrected series in the "on" variant and the
  uncorrected series in the "off" variant, so "off" scores against an easier,
  partially-tide-predictable target. Only the precip rows (label unaffected
  by tide) are a clean feature-side comparison: tide correction is a wash for
  the GBM (-0.002 BSS), which has solar-time features and learns the tide
  implicitly. Decision: KEEP the correction in the deploy path — a few-KB
  table cannot learn pressure x solar-time interactions the way the GBM can,
  and the correction is physically right and nearly free on-device.
- **Manual inputs are the dominant skill source at short leads**: precip_6h
  BSS 0.12 pressure-only -> 0.39 with sky/wind inputs. Distillation must
  keep sky_state and the wind features.
- The masking-augmented full model in pressure-only mode (BSS 0.14-0.15)
  slightly BEATS a dedicated pressure-only model (0.12) — one model serves
  both watch modes; no separate pressure-only artifact needed.

## 2026-07-04 — M4 final artifact decision (Option A vs B)

- **Shipped: Option B, int8 MLP (15.1 KB)** — beats the additive tables on
  all 9 heads within the 32-64 KB budget (largest gaps on pfall: 0.29 vs
  0.19 at 6h, and windup: 0.35 vs 0.29 at 12h). Power-of-two layer scales
  make device requantization pure bit-shifts; int8 quantization measured
  at ~0.001 BSS cost (integer-exact evaluation, not simulated).
- **Kept: Option A additive tables (2.5 KB)** as documented fallback — the
  same byte class as the 1942 dial and still beats it on every precip head.
- MLP consumes the SAME binned integer inputs as the tables, so layer 1 is
  14 row-lookups summed (an additive table into 16 dims) — no float math
  anywhere on device.
- Verbal thresholds verified on artifact probabilities (cell A): "likely"
  73-83% observed (target 70-85), "very likely" 89-94%, "unlikely" 9-10%.
- 52-station distill_52station_report.md numbers used a 52-station
  climatology reference for non-core stations (coarser regime fallback);
  distill_fullscale_report.md is the corrected authoritative version.
