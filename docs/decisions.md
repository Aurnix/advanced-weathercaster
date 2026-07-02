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
