"""CLI: python -m neosager <stage> [...]. Every stage reads config.yaml only."""

from __future__ import annotations

import argparse
import json
import sys

from .config import DEFAULT_CONFIG, load_config


def _parse_years(spec: str) -> list[int]:
    """'1990-2024' or '1995,2010,2020' -> list of ints."""
    if "-" in spec:
        a, b = spec.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(y) for y in spec.split(",")]


def cmd_ingest(args: argparse.Namespace) -> int:
    from .data.isd_download import estimate_download_gb, ingest_bulk

    cfg = load_config(args.config)
    stations = args.stations.split(",")
    years = _parse_years(args.years)
    pairs = [(s, y) for s in stations for y in years]
    print(f"ingest: {len(stations)} stations x {len(years)} years "
          f"= {len(pairs)} station-years")

    est_gb = estimate_download_gb(cfg, pairs)
    print(f"estimated download: {est_gb:.1f} GB")
    if est_gb > cfg.ncei.confirm_threshold_gb and not args.confirm_download:
        print(f"ABORT: estimate exceeds {cfg.ncei.confirm_threshold_gb} GB; "
              f"rerun with --confirm-download after user approval.")
        return 2

    counts = ingest_bulk(cfg, pairs, keep_raw=args.keep_raw)
    print(f"done: {json.dumps(counts)}")
    return 0 if counts.get("error", 0) == 0 else 1


def cmd_coverage(args: argparse.Namespace) -> int:
    """Print per-station field-coverage diagnostics from the ledger."""
    from .data.ledger import Ledger

    cfg = load_config(args.config)
    ledger = Ledger(cfg.paths.resolved("ledger"))
    rows = [r for r in ledger._latest.values()
            if r["stage"] == "hourly_parquet" and r["status"] == "ok"]
    if args.stations:
        keep = set(args.stations.split(","))
        rows = [r for r in rows if r["station"] in keep]
    rows.sort(key=lambda r: (r["station"], r["year"]))
    print(f"{'station':>12} {'year':>5} {'press':>6} {'ma1':>6} {'wind':>6} "
          f"{'sky':>6} {'pcp_h':>6} {'hours':>6}")
    for r in rows:
        s = r.get("stats", {})
        print(f"{r['station']:>12} {r['year']:>5} "
              f"{s.get('coverage_pressure', 0):>6.2f} "
              f"{s.get('coverage_ma1', 0):>6.2f} "
              f"{s.get('coverage_wind', 0):>6.2f} "
              f"{s.get('coverage_sky', 0):>6.2f} "
              f"{s.get('precip_hours', 0):>6} "
              f"{s.get('hours_with_data', 0):>6}")
    return 0


def cmd_dataset(args: argparse.Namespace) -> int:
    from .data.stations import load_manifest
    from .dataset import build_all

    cfg = load_config(args.config)
    manifest = load_manifest(args.manifest)
    build_all(cfg, manifest)
    return 0


def cmd_baselines_report(args: argparse.Namespace) -> int:
    from .data.stations import load_manifest
    from .eval.run_baselines import run

    cfg = load_config(args.config)
    manifest = load_manifest(args.manifest)
    out = run(cfg, manifest, args.name)
    print(f"report written: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="neosager")
    p.add_argument("--config", default=str(DEFAULT_CONFIG))
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("ingest", help="download+parse station-years to parquet")
    pi.add_argument("--stations", required=True, help="comma-separated ids")
    pi.add_argument("--years", required=True, help="e.g. 1990-2024 or 1995,2010")
    pi.add_argument("--keep-raw", action="store_true")
    pi.add_argument("--confirm-download", action="store_true",
                    help="required when estimate exceeds the confirm threshold")
    pi.set_defaults(func=cmd_ingest)

    pc = sub.add_parser("coverage", help="print field-coverage diagnostics")
    pc.add_argument("--stations", default="")
    pc.set_defaults(func=cmd_coverage)

    pd_ = sub.add_parser("dataset", help="build feature+label matrices")
    pd_.add_argument("--manifest", required=True, help="stations yaml")
    pd_.set_defaults(func=cmd_dataset)

    pb = sub.add_parser("baselines-report", help="score baselines, write report")
    pb.add_argument("--manifest", required=True)
    pb.add_argument("--name", default="milestone1_report")
    pb.set_defaults(func=cmd_baselines_report)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
