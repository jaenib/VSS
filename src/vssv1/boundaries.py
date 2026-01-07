from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from shapely import wkt
from shapely.geometry import box

from . import bookie, paths

# Bounding box helper for recentered geometries.


def all_bounds(gdf: gpd.GeoDataFrame):
    union_of_all = gdf["recentered_geometry"].unary_union
    minx, miny, maxx, maxy = union_of_all.bounds

    print(f"Bounding Box: ({minx}, {miny}, {maxx}, {maxy})")
    return minx, miny, maxx, maxy


def percentile_bounds(gdf: gpd.GeoDataFrame, percentile: int = 5):
    all_x_coords = []
    all_y_coords = []

    for geom in gdf["recentered_geometry"]:
        if geom.type == "Polygon":
            x, y = geom.exterior.coords.xy
            all_x_coords.extend(x)
            all_y_coords.extend(y)
        elif geom.type == "MultiPolygon":
            for polygon in geom.geoms:
                x, y = polygon.exterior.coords.xy
                all_x_coords.extend(x)
                all_y_coords.extend(y)

    minx = np.percentile(all_x_coords, percentile)
    maxx = np.percentile(all_x_coords, 100 - percentile)
    miny = np.percentile(all_y_coords, percentile)
    maxy = np.percentile(all_y_coords, 100 - percentile)

    print(f"Bounding Box (using percentiles): ({minx}, {miny}, {maxx}, {maxy})")
    return minx, miny, maxx, maxy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute bounding box for recentered geometries.")
    parser.add_argument(
        "--recentered-csv",
        type=Path,
        default=paths.processed_sdd_dir() / "recentered_floor_geometries.csv",
        help="CSV with recentered geometries.",
    )
    parser.add_argument(
        "--method",
        choices=["all", "percentile"],
        default="percentile",
        help="Bounding box method to use.",
    )
    parser.add_argument(
        "--percentile",
        type=int,
        default=5,
        help="Percentile for the percentile bounding box.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    df = bookie.read_csv_with_progress(args.recentered_csv, usecols=["recentered_geometry"])
    df["recentered_geometry"] = df["recentered_geometry"].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry="recentered_geometry")

    if args.method == "all":
        minx, miny, maxx, maxy = all_bounds(gdf)
    else:
        minx, miny, maxx, maxy = percentile_bounds(gdf, percentile=args.percentile)

    bounding_box_polygon = gpd.GeoSeries(
        {"geometry": gpd.GeoDataFrame({"geometry": [box(minx, miny, maxx, maxy)]})["geometry"].unary_union}
    )

    ax = gdf.plot(edgecolor="black", facecolor="none")
    bounding_box_polygon.boundary.plot(ax=ax, color="red", linewidth=2)
    ax.set_adjustable("box")

    all_x_coords = []
    all_y_coords = []

    for geom in gdf["recentered_geometry"]:
        if geom.type == "Polygon":
            x, y = geom.exterior.coords.xy
            all_x_coords.extend(x)
            all_y_coords.extend(y)
        elif geom.type == "MultiPolygon":
            for polygon in geom.geoms:
                x, y = polygon.exterior.coords.xy
                all_x_coords.extend(x)
                all_y_coords.extend(y)

    ax_xhist = ax.twiny()
    ax_yhist = ax.twinx()

    ax_xhist.hist(all_x_coords, bins=200, orientation="vertical", alpha=0.4, color="blue")
    ax_yhist.hist(all_y_coords, bins=200, orientation="horizontal", alpha=0.4, color="green")

    ax_xhist.set_ylim(ax.get_ylim())
    ax_yhist.set_xlim(ax.get_xlim())

    plt.show()

    print("goodbye")


if __name__ == "__main__":
    main()
