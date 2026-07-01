"""Load and validate config.yaml. Single source of truth for all stages."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "config" / "config.yaml"


class PathsCfg(BaseModel):
    data_root: str
    raw_dir: str
    parquet_dir: str
    datasets_dir: str
    models_dir: str
    artifacts_dir: str
    ledger: str

    def resolved(self, name: str) -> Path:
        raw: str = getattr(self, name)
        return Path(raw.format(data_root=self.data_root))


class NceiCfg(BaseModel):
    base_url: str
    history_url: str
    max_workers: int = 5
    retries: int = 3
    connect_timeout_s: float = 10
    read_timeout_s: float = 60
    confirm_threshold_gb: float = 5.0


class YearsCfg(BaseModel):
    start: int
    end: int


class SplitsCfg(BaseModel):
    train_years: tuple[int, int]
    val_years: tuple[int, int]
    calib_years: tuple[int, int]
    test_years: tuple[int, int]
    station_test_frac: float
    seed: int
    thin_hours: int
    purge_lead_h: int


class IngestCfg(BaseModel):
    report_types_keep: list[str]
    qc_reject_flags: list[str]
    scalar_type_priority: list[str]


class LabelsCfg(BaseModel):
    leads_h: list[int]
    eval_extra_leads_h: list[int]
    window_min_coverage: float
    window_max_gap_h: int
    pressure_fall_hpa: float
    wind_beaufort_jump: int
    endpoint_tolerance_h: float


class FeaturesCfg(BaseModel):
    tendency_hours: list[int]
    tendency_endpoint_tol_min: int
    hf_window_h: int
    tide_correction: bool
    tide_s2_amp: float
    tide_s2_phase_h: float
    tide_s1_amp: float
    tide_s1_phase_h: float
    mask_manual_group_frac: float
    mask_cloud_only_frac: float


class StationsCfg(BaseModel):
    core_manifest: str
    full_manifest: str
    probe_years: list[int]
    probe_min_pressure_coverage: float
    probe_min_precip_hours: int
    probe_min_precip_hours_desert: int
    move_threshold_km: float


class Config(BaseModel):
    paths: PathsCfg
    ncei: NceiCfg
    years: YearsCfg
    splits: SplitsCfg
    ingest: IngestCfg
    labels: LabelsCfg
    features: FeaturesCfg
    stations: StationsCfg


def load_config(path: Path | str = DEFAULT_CONFIG) -> Config:
    with open(path, encoding="utf-8") as f:
        return Config.model_validate(yaml.safe_load(f))
