from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon
from shapely import wkt
from shapely.geometry import Polygon as ShapelyPolygon

from . import bookie, init_outline, paths

try:
    from line_profiler import LineProfiler
except Exception:  # pragma: no cover - optional dependency
    LineProfiler = None


def _default_recentered_csv() -> Path:
    candidates = [
        paths.processed_sdd_dir() / "recentered_floor_geometries.csv",
        paths.source_sdd_dir() / "recentered_floor_geometries.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def render_floorplan(
    row_number: int,
    df,
    encountered_ids: list,
    generated_hashes: set,
    end_row_number: int,
    group_id: str,
    color_by: str,
    extent: float,
    fig_size_in: float,
    dpi_value: int,
    write_outline: bool,
) -> None:
    curr_row = df.iloc[row_number]

    site_id = curr_row["site_id"]
    unit_id = curr_row[group_id]

    if bookie.check_encountered_apartment_ids(row_number, unit_id, encountered_ids, end_row_number):
        return

    unit_df = df[(df["site_id"] == site_id) & (df[group_id] == unit_id)]
    unit_hash = bookie.get_unit_hash(unit_df)

    if unit_hash in generated_hashes:
        print("\nalready drawn similar unit and not doing it again...")
        return

    generated_hashes.add(unit_hash)

    unit_df = unit_df.copy()
    unit_df.loc[:, "recentered_geometry"] = unit_df["recentered_geometry"].apply(wkt.loads)

    fig, ax = plt.subplots(figsize=(fig_size_in, fig_size_in))
    ax.set_xlim(-extent, extent)
    ax.set_ylim(-extent, extent)

    colors_by_type = {
        "area": "white",
        "separator": "black",
        "opening": "white",
        "feature": "gray",
    }
    colors_by_subtype = {
        "BATHROOM": "#D3D3D3",
        "LIVING_ROOM": "#E8E8E8",
        "BALCONY": "#DCDCDC",
        "CORRIDOR": "#778899",
        "ROOM": "#F5F5F5",
        "BATHTUB": "#696969",
        "SHOWER": "#696969",
        "SINK": "#696969",
        "TOILET": "#696969",
        "KITCHEN": "#C0C0C0",
        "RAILING": "dimgray",
        "WINDOW": "gray",
        "DOOR": "#D3D3D3",
        "ENTRANCE_DOOR": "#D3D3D3",
        "DINING": "#E8E8E8",
        "SHAFT": "black",
        "WALL": "#000000",
        "STAIRCASE": "dimgray",
        "STAIRS": "black",
        "STOREROOM": "dimgray",
        "COLUMN": "#000000",
        "BASEMENT_COMPARTMENT": "#BC8F8F",
    }
    colors = colors_by_subtype if color_by == "entity_subtype" else colors_by_type

    area_polygons = []

    for _, row in unit_df.iterrows():
        geom = row["recentered_geometry"]
        if geom.is_valid and geom.geom_type == "Polygon":
            coords = np.array(geom.exterior.coords)
            if len(coords) >= 2:
                polygon = ShapelyPolygon(coords)
                if row["entity_type"] == "area":
                    if bookie.is_significantly_overlapping(polygon, area_polygons):
                        print("\nMAISONNETTE ALARM: significant overlap detected. Skipping plot.")
                        return
                    area_polygons.append(polygon)

    for i, row in unit_df.iterrows():
        geom = row["recentered_geometry"]
        color_key = row[color_by]
        color = colors.get(color_key, "green")

        if geom.is_valid and geom.geom_type == "Polygon":
            coords = np.array(geom.exterior.coords)
            if len(coords) >= 2:
                patch = Polygon(coords, closed=True, edgecolor="black", facecolor=color, alpha=1)
                ax.add_patch(patch)
            else:
                print(f"\nInvalid geometry for row {i}: {geom}")
        else:
            print(f"\nInvalid or non-polygon geometry for row {i}: {geom}")

    ax.set_aspect("equal")
    ax.axis("off")

    out_dir = paths.ensure_dir(paths.fp_complete_dir())
    filename = bookie.next_available_filename(out_dir, "FP")
    plt.savefig(filename, bbox_inches="tight", pad_inches=0, dpi=dpi_value)

    if write_outline:
        init_outline.get_contour()

    print("\napartment successfully exported")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render floorplan images from recentered geometries.")
    parser.add_argument(
        "--recentered-csv",
        type=Path,
        default=_default_recentered_csv(),
        help="CSV with recentered geometries.",
    )
    parser.add_argument("--group-id", default="apartment_id", help="Group identifier column.")
    parser.add_argument(
        "--color-by",
        choices=["entity_type", "entity_subtype"],
        default="entity_type",
        help="Column to map to colors.",
    )
    parser.add_argument("--start-row", type=int, default=0, help="Start row index.")
    parser.add_argument("--end-row", type=int, default=1000, help="End row index (inclusive).")
    parser.add_argument("--extent", type=float, default=12, help="Half-width/height of render window.")
    parser.add_argument("--fig-size", type=float, default=2.0, help="Figure size in inches.")
    parser.add_argument("--dpi", type=int, default=600, help="DPI for saved images.")
    parser.add_argument("--outline", action="store_true", help="Generate outline images after rendering.")
    parser.add_argument("--chunksize", type=int, default=100, help="CSV read chunk size.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    usecols = {"site_id", "apartment_id", "entity_type", "entity_subtype", "recentered_geometry", args.group_id}
    df = bookie.read_csv_with_progress(args.recentered_csv, chunksize=args.chunksize, usecols=usecols)

    if args.group_id not in df.columns:
        raise KeyError(f"group-id column '{args.group_id}' not found in CSV")

    num_rows = len(df)
    print(f"\nTotal number of rows in the database: {num_rows}")

    start_row = max(args.start_row, 0)
    end_row = min(args.end_row, num_rows - 1)

    generated_hashes = set()
    encountered_ids = []

    if LineProfiler:
        lp = LineProfiler()
        worker = lp(render_floorplan)
    else:
        lp = None
        worker = render_floorplan

    for row_number in range(start_row, end_row + 1):
        worker(
            row_number,
            df,
            encountered_ids,
            generated_hashes,
            end_row,
            args.group_id,
            args.color_by,
            args.extent,
            args.fig_size,
            args.dpi,
            args.outline,
        )

    if lp:
        lp.print_stats()

    print("goodbye")


if __name__ == "__main__":
    main()
