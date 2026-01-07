from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path
from typing import Iterable

import cv2
import pandas as pd
from tqdm import tqdm

try:
    from line_profiler import LineProfiler
except Exception:  # pragma: no cover - optional dependency
    LineProfiler = None


def next_available_filename(directory: Path | str, base_filename: str, suffix: str = ".png") -> Path:
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)

    i = 1
    while True:
        filename = dir_path / f"{base_filename}_{i:04d}{suffix}"
        if not filename.exists():
            return filename
        i += 1


def _extract_suffix_number(path: Path) -> int | None:
    stem = path.stem
    if "_" not in stem:
        return None
    suffix = stem.rsplit("_", 1)[-1]
    return int(suffix) if suffix.isdigit() else None


def get_latest_image(dir_path: Path | str) -> Path | None:
    dir_path = Path(dir_path)
    png_files = list(dir_path.glob("*.png"))
    if not png_files:
        print("\nno PNG files found in the directory.")
        return None

    numbered_files = [(path, _extract_suffix_number(path)) for path in png_files]
    numbered_files = [(path, num) for path, num in numbered_files if num is not None]
    if not numbered_files:
        print("\nno numbers found in file names.")
        return None

    latest_path = max(numbered_files, key=lambda item: item[1])[0]
    return latest_path


def show_image(image, delay: int = 3, wait_time: int = 1000) -> None:
    for i in range(delay, 0, -1):
        print(f"\npng will close in {i} seconds")
        cv2.imshow(str(i), image)
        cv2.waitKey(wait_time)
        cv2.destroyAllWindows()


def show_plt(filename: Path | str, delay: int = 3) -> None:
    filename = str(filename)
    for i in range(delay, 0, -1):
        print(f"\nfloorplan will close in {i} seconds")
        os.system(f"open {filename}")
        time.sleep(1)


def read_csv_with_progress(filepath: Path | str, chunksize: int = 100, usecols: Iterable[str] | None = None) -> pd.DataFrame:
    if usecols is None:
        usecols = [
            "site_id",
            "apartment_id",
            "entity_type",
            "entity_subtype",
            "geometry",
            "recentered_geometry",
        ]

    chunks = []
    for chunk in tqdm(pd.read_csv(filepath, chunksize=chunksize, usecols=list(usecols))):
        chunks.append(chunk)

    return pd.concat(chunks, axis=0)


def read_avg_csv_with_progress(filepath: Path | str, chunksize: int = 100) -> pd.DataFrame:
    return read_csv_with_progress(
        filepath,
        chunksize=chunksize,
        usecols=["site_id", "apartment_id", "entity_type", "entity_subtype", "geometry"],
    )


def do_profile(follow=None):
    if follow is None:
        follow = []

    def inner(func):
        def profiled_func(*args, **kwargs):
            if LineProfiler is None:
                raise RuntimeError("line_profiler is not installed. Install it to use profiling.")
            profiler = LineProfiler()
            profiler.add_function(func)
            for f in follow:
                profiler.add_function(f)
            profiler.enable_by_count()
            try:
                return func(*args, **kwargs)
            finally:
                profiler.print_stats()

        return profiled_func

    return inner


def check_encountered_apartment_ids(
    row_number: int,
    apartment_id,
    encountered_apartment_ids: list,
    end_row_number: int,
) -> bool:
    if apartment_id in encountered_apartment_ids or pd.isna(apartment_id):
        return True

    encountered_apartment_ids.append(apartment_id)
    print(f"\nfound apartment No. {len(encountered_apartment_ids)} @ row {row_number} of {end_row_number}")
    return False


def get_unit_hash(unit_df: pd.DataFrame) -> str:
    sorted_df = unit_df.sort_values(by=["recentered_geometry", "entity_subtype"])
    combined_string = "".join([str(geom) for geom in sorted_df["recentered_geometry"]]) + "".join(
        [str(val) for val in sorted_df["entity_subtype"]]
    )

    return hashlib.md5(combined_string.encode()).hexdigest()


def is_significantly_overlapping(polygon, polygons) -> bool:
    for existing_polygon in polygons:
        if polygon.intersects(existing_polygon):
            intersection = polygon.intersection(existing_polygon).area
            if intersection / min(polygon.area, existing_polygon.area) > 0.5:
                return True
    return False
