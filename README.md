# Advanced Weathercaster

**A data-driven successor to the 1942 Sager Weathercaster.** Short-range
(3–36 h) probabilistic local weather forecasting from the instruments a
mariner had in 1942 and a GPS watch has today — barometric pressure history,
position, clock, and your own eyes on the wind and sky. **No internet, no
numerical weather model, no infrastructure**: in the standard taxonomy this
is *classical (observation-driven, NWP-free) statistical forecasting*,
trained on 35 years of surface observations and verified the hard way.

> Forecast for the next 12–24 hours: Rain or showers within a few hours
> (93%), continuing through the period. Southwest winds, strong (25–38 mph).
> High confidence.

## Headline results

Verified on 3.5M held-out forecasts (283 North-American stations,
2020–2024 never seen in training; splits by station *and* year; block
bootstrap CIs). Brier Skill Score vs per-station climatology:

| P(precip in window) | 6 h | 12 h | 24 h | 36 h |
|---|---|---|---|---|
| **Advanced Weathercaster (GBM)** | **0.38** | **0.31** | **0.24** | 0.20 |
| Sager Weathercaster (1942, calibrated) | 0.21 | 0.13 | 0.05 | 0.00 |
| Zambretti (calibrated) | −0.06 | −0.07 | −0.08 | — |
| Persistence | 0.11 | −0.18 | −0.65 | — |

Also predicted, all calibrated: wind increase (BSS 0.36–0.41), further
pressure fall (0.24–0.48), 4-class conditions (Heidke 0.35), max wind band
in the dial's own vocabulary (Heidke 0.49 @ 12h), and wind-direction
tendency (0.28) — with explicit gale-risk probabilities.

Three findings we believe are new:

1. **The first large-scale verification of the Sager Weathercaster** (and
   Zambretti). The 1942 dial has genuine skill exactly inside its advertised
   12–24 h envelope, decaying to zero at 36 h; it is strongest in frontal
   mid-latitude regimes and fails in the Mountain West. Its velocity ring
   carries real 24 h information; its direction ring, measured relative to
   the current wind, carries none.
2. **A skill-vs-lead-time curve for barometer-class instruments**: the same
   inputs, read optimally, still carry +0.20 BSS at 36 h — twice the dial's
   horizon ([reports/figures/leadtime_curves.png](reports/figures/leadtime_curves.png)).
3. **The human is worth more than the barometer at short leads**: entering
   sky state and wind triples 6 h precipitation skill (0.12 → 0.39). Sager's
   manual-input design philosophy was right.

Full analysis: [reports/final_report.md](reports/final_report.md) ·
per-regime and lead-time breakouts, ablations, and the Sager verification in
the sibling reports · methodology decisions in
[docs/decisions.md](docs/decisions.md) · improvement roadmap in
[docs/research_memo.md](docs/research_memo.md).

## Try it — the web calculator

A dependency-free, old-school HTML calculator running the full float model
(pressure chain, atmospheric-tide correction, 15 probability heads,
verbalizer) entirely in your browser:

```
cd webcalc && python -m http.server 8377
# open http://localhost:8377
```

Enter your barometer readings (now / 1 / 3 / 6 / 12 h ago), elevation, and
Sager-style wind & sky observations. Unknown fields are fine — the model is
trained to degrade gracefully.

## Repository layout

```
config/            config.yaml (single source of truth) + station manifests
src/neosager/      pipeline: ISD ingest → labels/features → splits → models
  baselines/       climatology, persistence, Zambretti, Sager port (golden-
                   verified against the original JS over all 5,400 inputs)
  models/          LightGBM heads, calibration, distillation (tables + MLP)
  deploy/          integer-only reference inference + verbalizer + spec
  eval/            metrics, block bootstrap, report generators
scripts/           end-to-end runners for every milestone
tests/             55 pytest tests (parsers, labels, causality, goldens,
                   verbalizer properties, integer-inference equivalence)
webcalc/           the browser calculator + exported float model
reports/           committed verification reports and figures
```

## Reproducing from scratch

Requires Python ≥3.12 and ~25 GB of NCEI downloads (resumable; ~10 GB
stored). Set `paths.data_root` in `config/config.yaml`, then:

```bash
pip install -e .[dev]
pytest -q                                     # fixture tests, no data needed
python scripts/run_m2_ingest.py               # probe + full ISD ingest
python -m neosager dataset  --manifest config/stations_full.yaml
python -m neosager baselines-report --manifest config/stations_full.yaml
python -m neosager gbm-report       --manifest config/stations_full.yaml
python scripts/run_regimes.py                 # per-regime breakout
python scripts/run_leadtime.py                # 3–36h skill curves
python scripts/run_wind.py                    # wind-output heads + Sager rings
python scripts/run_distill.py                 # compressed artifacts
python scripts/export_webcalc_model.py        # web calculator weights
python scripts/export_webcalc_wind.py
```

Every stage is idempotent and resumable; every dataset filtering decision is
logged to `<data_root>/ledger.jsonl`. Anti-leakage rules (fits on training
folds only, purged label windows, seeded splits committed to the manifests)
are documented in `docs/decisions.md` — if you get a result that looks too
good, read that file first.

## Deployment path

`deploy/` contains integer-only reference implementations (no floats, no
libm) for two compressed artifacts — a 15 KB int8 MLP and a 2.5 KB additive
table, both calibrated and equivalence-tested — plus a byte/op budget and
C-like pseudocode intended for a Monkey C (Garmin) port. The float model in
`webcalc/` is the current reference for output quality.

## Name & lineage

The **Sager Weathercaster** (Raymond M. Sager, 1942) is a mechanical dial
that turns barometer + wind + sky into a remarkably good forecast for its
era — this project verifies just how good. The **Advanced Weathercaster**
keeps Sager's inputs, output format, and offline philosophy, and replaces
the hand-fit lookup table with one fit to 18 million observations. The
Sager table used by the baseline is from
[Aurnix/Sager-Weather-Forecaster](https://github.com/Aurnix/Sager-Weather-Forecaster)
(MIT). License: MIT (see LICENSE).
