"""Append-only JSONL ledger recording every station-year's ingestion outcome
and every filtering decision (dropped-row counts by reason).

Done-ness contract: a station-year is complete iff its parquet file exists AND
the ledger's latest entry for (station, year, stage) has status "ok".
Status "absent" (NCEI 404) is terminal and never retried.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class Ledger:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._latest: dict[tuple[str, int, str], dict[str, Any]] = {}
        if self.path.exists():
            with open(self.path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    self._latest[self._key(rec)] = rec

    @staticmethod
    def _key(rec: dict[str, Any]) -> tuple[str, int, str]:
        return (rec["station"], int(rec["year"]), rec["stage"])

    def record(self, station: str, year: int, stage: str, status: str,
               **extra: Any) -> None:
        rec = {
            "station": station,
            "year": int(year),
            "stage": stage,
            "status": status,
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            **extra,
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self._latest[self._key(rec)] = rec

    def status(self, station: str, year: int, stage: str) -> str | None:
        rec = self._latest.get((station, int(year), stage))
        return rec["status"] if rec else None

    def entry(self, station: str, year: int, stage: str) -> dict[str, Any] | None:
        return self._latest.get((station, int(year), stage))
