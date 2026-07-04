"""Run the 2-year quality probe on the 78 drawn candidates, then select the
core-50, assign station folds, and write config/stations_core50.yaml."""
import pandas as pd
from neosager.config import load_config, REPO_ROOT
from neosager.data.stations import probe_and_accept, write_manifest
from neosager.splits import assign_station_folds

cfg = load_config()
drawn = pd.read_csv("D:/neosager-data/m1_probe_candidates.csv",
                    dtype={"station_id": str, "usaf": str, "wban": str})
probed = probe_and_accept(cfg, drawn)
print(probed.groupby(["regime", "accepted"], observed=True)["station_id"].size())
print("\nrejections:")
print(probed[~probed["accepted"]][["station_id", "name", "regime",
                                   "probe_reject"]].to_string())

acc = probed[probed["accepted"]].copy()
# core-50: up to 9 per regime, keep coastal/continental spread (already
# stratified in the draw; just trim largest regimes first, seeded)
import numpy as np
rng = np.random.default_rng(cfg.splits.seed)
picks = []
for regime, grp in acc.groupby("regime", observed=True):
    k = min(9, len(grp))
    picks.append(grp.sample(k, random_state=int(rng.integers(2**32))))
core = pd.concat(picks)
print(f"\ncore set: {len(core)}")
core = assign_station_folds(core, cfg)
print(core.groupby(["regime", "station_fold"], observed=True)["station_id"].size())

write_manifest(probed, REPO_ROOT / "config" / "stations_probe_m1.yaml")
core_out = core.copy()
write_manifest(core_out.assign(station_fold=core_out["station_fold"]),
               REPO_ROOT / "config" / "stations_core50.yaml")
# station_fold column must survive into the manifest
import yaml
with open(REPO_ROOT / "config" / "stations_core50.yaml", encoding="utf-8") as f:
    d = yaml.safe_load(f)
folds = dict(zip(core_out["station_id"], core_out["station_fold"]))
for rec in d["stations"]:
    rec["station_fold"] = folds[rec["station_id"]]
with open(REPO_ROOT / "config" / "stations_core50.yaml", "w", encoding="utf-8") as f:
    yaml.safe_dump(d, f, sort_keys=False, allow_unicode=True)
print("wrote config/stations_core50.yaml")
