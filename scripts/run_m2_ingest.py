"""Milestone-2 full-scale ingest, user-approved 2026-07-02 (~100-250 GB):
1. Draw up to 80 candidates/regime from the 561 survivors.
2. Probe all drawn stations (2 years each; already-probed skip via ledger).
3. Write config/stations_full.yaml with folds assigned.
4. Ingest all accepted stations x 1990-2024.
Fully resumable at every step.
"""

import pandas as pd

from neosager.config import REPO_ROOT, load_config
from neosager.data.isd_download import ingest_bulk
from neosager.data.stations import (build_candidate_frame, probe_and_accept,
                                    stratified_draw, write_manifest)
from neosager.splits import assign_station_folds

cfg = load_config()

print("== candidates ==", flush=True)
cand = build_candidate_frame(cfg)
print(f"{len(cand)} candidates", flush=True)

drawn = stratified_draw(cand, per_regime=80, seed=cfg.splits.seed)
print(f"{len(drawn)} drawn for probe "
      f"({drawn.groupby('regime', observed=True)['station_id'].size().to_dict()})",
      flush=True)

print("== probe ==", flush=True)
probed = probe_and_accept(cfg, drawn)
acc = probed[probed["accepted"]].copy()
print(f"accepted {len(acc)}/{len(probed)}", flush=True)
print(probed[~probed["accepted"]]["probe_reject"].value_counts().to_string(),
      flush=True)

acc = assign_station_folds(acc, cfg)
# keep the M1 core-50 fold assignments stable: stations already in
# stations_core50.yaml retain their committed fold
core = pd.DataFrame(
    __import__("yaml").safe_load(
        open(REPO_ROOT / "config" / "stations_core50.yaml",
             encoding="utf-8"))["stations"])
fold_map = dict(zip(core["station_id"], core["station_fold"]))
acc["station_fold"] = [
    fold_map.get(s, f) for s, f in zip(acc["station_id"], acc["station_fold"])]

write_manifest(probed, REPO_ROOT / "config" / "stations_probe_full.yaml")
write_manifest(acc, REPO_ROOT / "config" / "stations_full.yaml")
import yaml
with open(REPO_ROOT / "config" / "stations_full.yaml", encoding="utf-8") as f:
    d = yaml.safe_load(f)
folds = dict(zip(acc["station_id"], acc["station_fold"]))
for rec in d["stations"]:
    rec["station_fold"] = folds[rec["station_id"]]
with open(REPO_ROOT / "config" / "stations_full.yaml", "w",
          encoding="utf-8") as f:
    yaml.safe_dump(d, f, sort_keys=False, allow_unicode=True)
print(f"wrote stations_full.yaml with {len(acc)} stations", flush=True)

print("== full ingest ==", flush=True)
pairs = [(s, y) for s in acc["station_id"]
         for y in range(cfg.years.start, cfg.years.end + 1)]
print(f"{len(pairs)} station-years", flush=True)
counts = ingest_bulk(cfg, pairs)
print(f"M2 INGEST DONE: {counts}", flush=True)
