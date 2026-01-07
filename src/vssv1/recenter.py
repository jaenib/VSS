from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from shapely import wkt
from shapely.affinity import translate
from shapely.geometry import MultiPolygon, Polygon

from . import bookie, paths

# Recenter floorplan geometries so each unit is centered around the origin.


def _collect_points(geometry):
    if isinstance(geometry, Polygon):
        return list(geometry.exterior.coords)
    if isinstance(geometry, MultiPolygon):
        points = []
        for poly in geometry.geoms:
            points.extend(list(poly.exterior.coords))
        return points
    return []


def recenter_geometry_avg_factory(stats):
    def recenter_geometry_avg(group):
        all_points = [point for geometry in group["geometry"] for point in _collect_points(geometry)]
        if not all_points:
            return group

        avg_x = sum(point[0] for point in all_points) / len(all_points)
        avg_y = sum(point[1] for point in all_points) / len(all_points)

        x_translation = -avg_x
        y_translation = -avg_y

        group["recentered_geometry"] = group["geometry"].apply(
            lambda geom: translate(geom, x_translation, y_translation)
        )

        stats["count"] += 1
        stats["points"] += len(all_points)
        print(
            f"\nunit No {stats['count']} successfully relocated to origin. "
            f"Moved total {stats['points']} points"
        )

        return group

    return recenter_geometry_avg


def plot_sample(apartment_data):
    fig, ax = plt.subplots()

    for _, row in apartment_data.iterrows():
        if isinstance(row["recentered_geometry"], Polygon):
            x, y = row["recentered_geometry"].exterior.xy
            ax.fill(x, y, alpha=0.5)
            ax.plot(x, y, color="black")
        elif isinstance(row["recentered_geometry"], MultiPolygon):
            for polygon in row["recentered_geometry"].geoms:
                x, y = polygon.exterior.xy
                ax.fill(x, y, alpha=0.5)
                ax.plot(x, y, color="black")

    ax.set_aspect("equal", "box")
    plt.show()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recenter Swiss Dwellings geometries.")
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=paths.source_sdd_dir() / "geometries.csv",
        help="Path to geometries.csv from the Swiss Dwellings dataset.",
    )
    parser.add_argument(
        "--group-id",
        default="apartment_id",
        help="Column to group by for recentering (e.g., apartment_id, floor_id).",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="Output CSV path. Defaults to data/processed/sdd_recentered/.",
    )
    parser.add_argument(
        "--chunksize",
        type=int,
        default=100,
        help="CSV read chunk size.",
    )
    parser.add_argument(
        "--plot-sample",
        action="store_true",
        help="Plot the first recentered unit for quick validation.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    output_csv = args.output_csv
    if output_csv is None:
        output_csv = paths.processed_sdd_dir() / f"recentered_{args.group_id.replace('_id', '')}_geometries.csv"

    print("\nreading source csv...")
    usecols = {
        "site_id",
        "apartment_id",
        "entity_type",
        "entity_subtype",
        "geometry",
        args.group_id,
    }
    df = bookie.read_csv_with_progress(args.input_csv, chunksize=args.chunksize, usecols=usecols)
    print("\ninflating WKT into shapely shapes...")
    df["geometry"] = df["geometry"].apply(wkt.loads)

    stats = {"count": 0, "points": 0}
    recenter_fn = recenter_geometry_avg_factory(stats)

    print("\nrecentering geometries...")
    df = df.groupby(args.group_id).apply(recenter_fn).reset_index(drop=True)

    if args.plot_sample:
        print("\nplotting the first unit...")
        first_unit_id = df[args.group_id].iloc[0]
        first_unit = df[df[args.group_id] == first_unit_id]
        plot_sample(first_unit)

    output_csv = Path(output_csv)
    paths.ensure_dir(output_csv.parent)
    print(f"\nsaving recentered data to {output_csv}...")
    df.to_csv(output_csv, index=False)
    print("goodbye")


if __name__ == "__main__":
    main()
