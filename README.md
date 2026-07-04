# NEOSAGER

A data-driven successor to the 1942 Sager Weathercaster: short-range (6–24 h) local
weather forecasting from Sager-class instruments only (barometric pressure history,
GPS position/elevation, clock, and optional user-entered wind/sky observations),
trained on NOAA ISD surface observations and distilled to a few-KB integer-math
artifact deployable on a GPS watch.

Core scientific deliverables:

1. Rigorous large-scale verification of the Sager and Zambretti algorithms against
   decades of surface observations (to our knowledge never published).
2. The answer to: *does a lookup table fit to data beat the one fit by hand in 1942?*
3. A skill-vs-lead-time curve (3–36 h) for Sager-class instruments, per climate regime.

## Layout

- `config/` — `config.yaml` is the single source of truth (paths, years, splits,
  thresholds); station manifests are generated then committed.
- `src/neosager/` — pipeline stages, all runnable via `python -m neosager <stage>`.
- `tests/` — pytest suite (parser fixtures, label definitions, feature causality,
  Sager goldens, verbalizer properties).
- `reports/` — generated verification reports (committed).
- `docs/` — ISD format document, dated station history snapshot, decision log.

Bulk data lives outside the repo at the `data_root` configured in `config.yaml`
(default `D:/neosager-data`), because the repo directory is OneDrive-synced.

## Status

**Complete through milestone 4.** Headline results in
[reports/final_report.md](reports/final_report.md): the learned model
roughly doubles the 1942 Sager dial's 6h precipitation skill and quintuples
it at 24h (BSS 0.38/0.31/0.24 vs 0.21/0.13/0.05 at 6/12/24h, 283 stations,
2020–2024 held out), and survives compression to a 15 KB integer-only
artifact (`deploy/infer_int_mlp.py`) with a 2.5 KB additive-table fallback.
The Sager dial itself verifies with genuine skill inside its claimed
12–24h envelope, decaying to zero at 36h — to our knowledge its first
published large-scale verification.

## Reproduction

See `scripts/` for milestone runners. Every stage is idempotent and resumable;
every dataset filtering decision is logged to `<data_root>/ledger.jsonl`.

## Attribution

The Sager baseline lookup table is extracted from the MIT-licensed
[Aurnix/Sager-Weather-Forecaster](https://github.com/Aurnix/Sager-Weather-Forecaster)
JavaScript implementation of Raymond M. Sager's 1942 Weathercaster dial.
