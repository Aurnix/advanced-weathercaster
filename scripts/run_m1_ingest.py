"""Milestone-1 full ingest: 52 core stations x 1990-2024.
Download size approved by user 2026-07-02 (~20-25 GB transfer).
Resumable: re-running skips completed station-years."""

from neosager.config import REPO_ROOT, load_config
from neosager.data.isd_download import ingest_bulk
from neosager.data.stations import load_manifest

cfg = load_config()
manifest = load_manifest(REPO_ROOT / "config" / "stations_core50.yaml")
pairs = [(s, y) for s in manifest["station_id"]
         for y in range(cfg.years.start, cfg.years.end + 1)]
print(f"{len(manifest)} stations x {cfg.years.end - cfg.years.start + 1} "
      f"years = {len(pairs)} station-years")
counts = ingest_bulk(cfg, pairs)
print(f"DONE: {counts}")
