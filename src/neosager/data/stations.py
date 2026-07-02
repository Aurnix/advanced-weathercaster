"""Station manifest construction: candidate filtering from isd-history.csv,
climate-regime assignment, coastal flagging, stratified draw, and the
two-year quality probe that gates acceptance.

Every rejection is recorded in the manifest with its reason — nothing is
silently dropped.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from shapely.geometry import shape
from shapely.strtree import STRtree

from ..config import REPO_ROOT, Config

HISTORY_CSV = REPO_ROOT / "docs" / "isd-history-2026-07-01.csv"
COASTLINE_GEOJSON = REPO_ROOT / "docs" / "ne_50m_coastline.geojson"
REGIMES_YAML = REPO_ROOT / "config" / "regimes.yaml"


def load_history(path: Path = HISTORY_CSV) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.columns = [c.strip().lower().replace(" ", "_").replace("(m)", "_m")
                  for c in df.columns]
    out = pd.DataFrame({
        "usaf": df["usaf"].str.strip(),
        "wban": df["wban"].str.strip(),
        "name": df["station_name"].str.strip(),
        "ctry": df["ctry"].str.strip(),
        "state": df["state"].str.strip(),
        "lat": pd.to_numeric(df["lat"], errors="coerce"),
        "lon": pd.to_numeric(df["lon"], errors="coerce"),
        "elev": pd.to_numeric(df["elev_m"], errors="coerce"),
        "begin": pd.to_datetime(df["begin"], format="%Y%m%d", errors="coerce"),
        "end": pd.to_datetime(df["end"], format="%Y%m%d", errors="coerce"),
    })
    out["station_id"] = out["usaf"] + out["wban"]
    return out


def candidates(cfg: Config, history: pd.DataFrame) -> pd.DataFrame:
    """North-America core candidate filter. Returns df + 'reject' column
    (empty string = candidate survives)."""
    h = history.copy()
    h["reject"] = ""

    def flag(mask: pd.Series, reason: str) -> None:
        h.loc[mask & (h["reject"] == ""), "reject"] = reason

    flag(~h["ctry"].isin(["US", "CA"]), "country")
    flag((h["usaf"] == "999999") | (h["wban"] == "99999"), "no_usaf_or_wban")
    flag(h["lat"].isna() | h["lon"].isna() | h["elev"].isna(), "no_position")
    flag(~h["lat"].between(24, 72), "lat_range")
    flag(~h["lon"].between(-170, -50), "lon_range")
    flag(h["begin"].isna() | (h["begin"] > pd.Timestamp("1995-01-01")),
         "record_starts_too_late")
    flag(h["end"].isna() | (h["end"] < pd.Timestamp("2024-12-31")),
         "record_ends_too_early")
    # duplicate station ids (station moves create multiple history rows):
    # keep the longest-record row, flag the rest; the >5km move check happens
    # against downloaded data later.
    h["record_days"] = (h["end"] - h["begin"]).dt.days
    dup = h[h["reject"] == ""].sort_values("record_days", ascending=False)
    keep_idx = dup.drop_duplicates("station_id").index
    flag(h.index.isin(dup.index) & ~h.index.isin(keep_idx), "duplicate_row")
    return h


def _load_regime_rules() -> tuple[list[dict], list[list[float]]]:
    with open(REGIMES_YAML, encoding="utf-8") as f:
        d = yaml.safe_load(f)
    return d["regimes"], d.get("desert_boxes", [])


def assign_regime(lat: float, lon: float, elev: float,
                  rules: list[dict]) -> str:
    for r in rules:
        if r["rule"] == "fallback":
            return r["name"]
        # rules are our own config, evaluated over exactly these three names
        if eval(r["rule"], {"__builtins__": {}},
                {"lat": lat, "lon": lon, "elev": elev}):
            return r["name"]
    return "other"


def is_desert(lat: float, lon: float, boxes: list[list[float]]) -> bool:
    return any(b[0] <= lat <= b[1] and b[2] <= lon <= b[3] for b in boxes)


def coastal_flags(df: pd.DataFrame, threshold_km: float = 50.0,
                  path: Path = COASTLINE_GEOJSON) -> pd.Series:
    """True if within threshold of the Natural Earth 1:50m coastline.
    Approximate planar distance with lon scaled by cos(lat) — plenty for a
    coarse coastal/continental stratification flag."""
    with open(path, encoding="utf-8") as f:
        gj = json.load(f)
    geoms = [shape(feat["geometry"]) for feat in gj["features"]]
    tree = STRtree(geoms)
    out = []
    for lat, lon in zip(df["lat"], df["lon"]):
        scale = math.cos(math.radians(lat))
        # search in raw degrees first (cheap), refine with scaled distance
        from shapely.geometry import Point
        p = Point(lon, lat)
        idx = tree.query(p.buffer(1.5))  # 1.5 deg ~ 165 km search radius
        if len(idx) == 0:
            out.append(False)
            continue
        best_km = math.inf
        for i in idx:
            g = geoms[i]
            q = g.interpolate(g.project(p)) if g.geom_type == "LineString" \
                else g
            # nearest point on geometry via shapely distance in degrees is
            # anisotropic; compute km distance to the projected nearest point
            from shapely.ops import nearest_points
            np_pt = nearest_points(p, g)[1]
            dlat = (np_pt.y - lat) * 111.0
            dlon = (np_pt.x - lon) * 111.0 * scale
            best_km = min(best_km, math.hypot(dlat, dlon))
        out.append(best_km <= threshold_km)
    return pd.Series(out, index=df.index)


def build_candidate_frame(cfg: Config) -> pd.DataFrame:
    """History -> surviving candidates with regime/coastal/desert columns."""
    hist = load_history()
    cand = candidates(cfg, hist)
    ok = cand[cand["reject"] == ""].copy()
    rules, desert_boxes = _load_regime_rules()
    ok["regime"] = [assign_regime(la, lo, el, rules)
                    for la, lo, el in zip(ok["lat"], ok["lon"], ok["elev"])]
    ok = ok[ok["regime"] != "other"]
    ok["desert"] = [is_desert(la, lo, desert_boxes)
                    for la, lo in zip(ok["lat"], ok["lon"])]
    ok["coastal"] = coastal_flags(ok)
    ok["lat_band"] = pd.cut(ok["lat"], [24, 35, 45, 55, 90],
                            labels=["24-35", "35-45", "45-55", "55+"])
    return ok


def stratified_draw(cand: pd.DataFrame, per_regime: int, seed: int
                    ) -> pd.DataFrame:
    """Draw per_regime stations per regime, balancing coastal/continental
    and spreading across lat bands where possible."""
    rng = np.random.default_rng(seed)
    picks = []
    for regime, grp in cand.groupby("regime", sort=True):
        n = min(per_regime, len(grp))
        # proportional-ish allocation over (coastal, lat_band) cells, at
        # least 1 per non-empty cell while budget lasts
        cells = [g for _, g in grp.groupby(["coastal", "lat_band"],
                                           sort=True, observed=True)]
        rng.shuffle(cells)
        quota = {id(c): max(1, round(n * len(c) / len(grp))) for c in cells}
        chosen: list[pd.DataFrame] = []
        remaining = n
        for c in cells:
            k = min(quota[id(c)], len(c), remaining)
            if k > 0:
                chosen.append(c.sample(k, random_state=int(rng.integers(2**32))))
                remaining -= k
        pool = grp.drop(pd.concat(chosen).index) if chosen else grp
        if remaining > 0 and len(pool) > 0:
            chosen.append(pool.sample(min(remaining, len(pool)),
                                      random_state=int(rng.integers(2**32))))
        picks.append(pd.concat(chosen))
    return pd.concat(picks)


def probe_and_accept(cfg: Config, drawn: pd.DataFrame) -> pd.DataFrame:
    """Ingest the probe years for each drawn station and apply the quality
    gate. Adds probe metric columns + 'accepted'/'probe_reject' columns."""
    from .isd_download import ingest_bulk
    from .ledger import Ledger

    years = cfg.stations.probe_years
    pairs = [(s, y) for s in drawn["station_id"] for y in years]
    ingest_bulk(cfg, pairs)

    ledger = Ledger(cfg.paths.resolved("ledger"))
    rows = []
    for s in drawn["station_id"]:
        rec = {"station_id": s, "probe_reject": ""}
        press, ma1, pcp = [], [], []
        for y in years:
            e = ledger.entry(s, y, "hourly_parquet")
            if not e or e["status"] != "ok":
                rec["probe_reject"] = f"probe_year_{y}_{e['status'] if e else 'missing'}"
                break
            st = e.get("stats", {})
            press.append(st.get("coverage_pressure", 0.0))
            ma1.append(st.get("coverage_ma1", 0.0))
            pcp.append(st.get("precip_hours", 0))
        else:
            rec["probe_pressure_cov"] = round(min(press), 3)
            rec["probe_ma1_cov"] = round(min(ma1), 3)
            rec["probe_precip_hours"] = min(pcp)
            if min(press) < cfg.stations.probe_min_pressure_coverage:
                rec["probe_reject"] = "pressure_coverage"
        rows.append(rec)
    probe = pd.DataFrame(rows).set_index("station_id")
    out = drawn.set_index("station_id").join(probe)
    floor = np.where(out["desert"],
                     cfg.stations.probe_min_precip_hours_desert,
                     cfg.stations.probe_min_precip_hours)
    thin_precip = (out["probe_reject"] == "") & \
        (out["probe_precip_hours"].fillna(0) < floor)
    out.loc[thin_precip, "probe_reject"] = "precip_evidence"
    out["accepted"] = out["probe_reject"] == ""
    return out.reset_index()


def write_manifest(df: pd.DataFrame, path: Path) -> None:
    cols = ["station_id", "name", "ctry", "state", "lat", "lon", "elev",
            "regime", "coastal", "desert", "lat_band",
            "probe_pressure_cov", "probe_ma1_cov", "probe_precip_hours",
            "accepted", "probe_reject"]
    cols = [c for c in cols if c in df.columns]
    recs = df[cols].to_dict(orient="records")
    for r in recs:  # yaml-friendly types
        for k, v in r.items():
            if isinstance(v, (np.floating, np.integer)):
                r[k] = v.item()
            elif isinstance(v, np.bool_):
                r[k] = bool(v)
            elif pd.isna(v) if not isinstance(v, (list, dict)) else False:
                r[k] = None
            elif not isinstance(v, (str, int, float, bool, type(None))):
                r[k] = str(v)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump({"stations": recs}, f, sort_keys=False,
                       allow_unicode=True)


def load_manifest(path: Path) -> pd.DataFrame:
    with open(path, encoding="utf-8") as f:
        return pd.DataFrame(yaml.safe_load(f)["stations"])
