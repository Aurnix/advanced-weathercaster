"""Streamed, resumable NCEI downloads and the download->parse->delete-raw
ingest pipeline for station-years.

NCEI quirks (verified 2026-07-01): HEAD requests time out — size probing uses
a streamed GET closed after reading Content-Length. 404 means the station-year
does not exist and is recorded as terminal status "absent".
"""

from __future__ import annotations

import hashlib
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

from ..config import Config
from .isd_parse import parse_isd_csv
from .ledger import Ledger
from .regularize import to_hourly

STAGE = "hourly_parquet"


def _url(cfg: Config, station: str, year: int) -> str:
    return f"{cfg.ncei.base_url}/{year}/{station}.csv"


def download_station_year(cfg: Config, station: str, year: int,
                          session: requests.Session | None = None) -> tuple[str, Path | None]:
    """Returns (status, path). status in {'ok', 'absent', 'error'}."""
    sess = session or requests.Session()
    dest = cfg.paths.resolved("raw_dir") / str(year) / f"{station}.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return "ok", dest
    part = dest.with_suffix(".csv.part")
    timeouts = (cfg.ncei.connect_timeout_s, cfg.ncei.read_timeout_s)
    for attempt in range(cfg.ncei.retries + 1):
        try:
            with sess.get(_url(cfg, station, year), stream=True,
                          timeout=timeouts) as r:
                if r.status_code == 404:
                    return "absent", None
                r.raise_for_status()
                with open(part, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        f.write(chunk)
            part.replace(dest)
            return "ok", dest
        except (requests.RequestException, OSError):
            part.unlink(missing_ok=True)
            if attempt == cfg.ncei.retries:
                return "error", None
            time.sleep(2 ** attempt * 2)
    return "error", None


def probe_size_bytes(cfg: Config, station: str, year: int,
                     session: requests.Session | None = None) -> int | None:
    """Content-Length via streamed GET closed after headers. None if absent."""
    sess = session or requests.Session()
    try:
        with sess.get(_url(cfg, station, year), stream=True,
                      timeout=(cfg.ncei.connect_timeout_s,
                               cfg.ncei.read_timeout_s)) as r:
            if r.status_code != 200:
                return None
            cl = r.headers.get("Content-Length")
            return int(cl) if cl else None
    except requests.RequestException:
        return None


def estimate_download_gb(cfg: Config, pairs: list[tuple[str, int]],
                         sample_n: int = 10) -> float:
    """Extrapolate total size from an evenly spaced sample of station-years."""
    if not pairs:
        return 0.0
    step = max(1, len(pairs) // sample_n)
    sample = pairs[::step][:sample_n]
    sess = requests.Session()
    sizes = [probe_size_bytes(cfg, s, y, sess) for s, y in sample]
    sizes = [s for s in sizes if s]
    if not sizes:
        return 0.0
    mean = sum(sizes) / len(sizes)
    return mean * len(pairs) / 1e9


def ingest_station_year(cfg: Config, ledger: Ledger, station: str, year: int,
                        keep_raw: bool = False,
                        session: requests.Session | None = None) -> str:
    """download -> parse -> hourly parquet -> delete raw. Returns status."""
    pq = cfg.paths.resolved("parquet_dir") / station / f"{year}.parquet"
    prior = ledger.status(station, year, STAGE)
    if prior == "absent":
        return "absent"
    if prior == "ok" and pq.exists():
        return "skip"

    status, raw_path = download_station_year(cfg, station, year, session)
    if status != "ok":
        ledger.record(station, year, STAGE, status)
        return status

    try:
        reports, drops = parse_isd_csv(raw_path, cfg.ingest)
        hourly, stats = to_hourly(reports, year, cfg.ingest)
        pq.parent.mkdir(parents=True, exist_ok=True)
        hourly.to_parquet(pq)
        sha = hashlib.sha256(pq.read_bytes()).hexdigest()
        ledger.record(station, year, STAGE, "ok",
                      rows=int(len(hourly)), drops=drops, stats=stats,
                      sha256=sha)
        if not keep_raw:
            raw_path.unlink(missing_ok=True)
        return "ok"
    except Exception as e:  # record and continue the bulk run
        ledger.record(station, year, STAGE, "parse_error", error=repr(e))
        return "parse_error"


def ingest_bulk(cfg: Config, pairs: list[tuple[str, int]],
                keep_raw: bool = False, progress: bool = True) -> dict:
    """Thread-pooled ingest of many (station, year) pairs. Resumable."""
    ledger = Ledger(cfg.paths.resolved("ledger"))
    counts: dict[str, int] = {}
    with ThreadPoolExecutor(max_workers=cfg.ncei.max_workers) as ex:
        futs = {ex.submit(ingest_station_year, cfg, ledger, s, y,
                          keep_raw, requests.Session()): (s, y)
                for s, y in pairs}
        done = 0
        for fut in as_completed(futs):
            status = fut.result()
            counts[status] = counts.get(status, 0) + 1
            done += 1
            if progress and done % 25 == 0:
                print(f"  {done}/{len(pairs)} station-years "
                      f"({counts})", flush=True)
    return counts
