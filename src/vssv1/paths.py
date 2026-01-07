from __future__ import annotations

import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _env_path(name: str, default: Path) -> Path:
    value = os.getenv(name)
    if value:
        return Path(value).expanduser().resolve()
    return default


def repo_root() -> Path:
    return _env_path("VSS_REPO_ROOT", REPO_ROOT)


def data_root() -> Path:
    return _env_path("VSS_DATA_ROOT", repo_root() / "data")


def output_root() -> Path:
    return _env_path("VSS_OUTPUT_ROOT", repo_root() / "outputs")


def source_sdd_dir() -> Path:
    return data_root() / "source" / "sdd" / "swiss-dwellings-v3.0.0"


def processed_sdd_dir() -> Path:
    return data_root() / "processed" / "sdd_recentered"


def fp_png_dir() -> Path:
    return output_root() / "fp_png"


def fp_complete_dir() -> Path:
    return fp_png_dir() / "fp_complete"


def fp_outline_dir() -> Path:
    return fp_png_dir() / "fp_outline"


def fp_xray_dir() -> Path:
    return fp_png_dir() / "fp_xray"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
