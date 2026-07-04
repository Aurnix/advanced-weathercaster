from neosager.config import REPO_ROOT, load_config
from neosager.data.stations import load_manifest
from neosager.eval.run_leadtime import run

cfg = load_config()
manifest = load_manifest(REPO_ROOT / "config" / "stations_full.yaml")
print("wrote", run(cfg, manifest, "leadtime_report"))
