from __future__ import annotations

import argparse
import datetime
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import DBSCAN
from tqdm import tqdm

try:
    import osxmetadata
except Exception:  # pragma: no cover - optional dependency
    osxmetadata = None


def get_file_creation_times(directory_path: Path):
    creation_times = []
    file_paths = []
    all_files = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            all_files.append(Path(root) / file)

    for file_path in tqdm(all_files, desc="Reading file creation timestamps"):
        try:
            if osxmetadata:
                metadata = osxmetadata.OSXMetaData(str(file_path))
                creation_time = metadata.kMDItemFSCreationDate
            else:
                creation_time = None

            if creation_time is None:
                creation_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
            creation_times.append(creation_time)
            file_paths.append(file_path)
        except Exception as exc:
            print(f"Error processing file {file_path}: {exc}")
    return creation_times, file_paths


def cluster_creation_times(creation_times, eps):
    print("Determining clusters of timestamps as working sessions")
    creation_timestamps = np.array([time.timestamp() for time in creation_times]).reshape(-1, 1)

    clustering = DBSCAN(eps, min_samples=2).fit(creation_timestamps)

    clusters = {}
    for label in set(clustering.labels_):
        if label != -1:
            cluster_times = [creation_times[i] for i in range(len(creation_times)) if clustering.labels_[i] == label]
            clusters[label] = cluster_times
    return clusters, clustering.labels_


def get_dominant_folder(cluster_files):
    folder_counts = {}
    for file_path in cluster_files:
        folder = file_path.parent
        folder_counts[folder] = folder_counts.get(folder, 0) + 1
    return max(folder_counts, key=folder_counts.get)


def estimate_worked_hours(clusters, file_paths, labels):
    total_worked_hours = 0
    cluster_durations = {}
    cluster_start_times = []
    cluster_durations_hours = []

    for cluster_label, cluster_times in clusters.items():
        start_time = min(cluster_times)
        end_time = max(cluster_times)
        worked_hours = (end_time - start_time).total_seconds() / 3600

        cluster_files = [file_paths[i] for i in range(len(file_paths)) if labels[i] == cluster_label]
        dominant_folder = get_dominant_folder(cluster_files)

        cluster_name = f"Cluster starting {start_time.strftime('%Y-%m-%d %H:%M')} in {dominant_folder.name}"
        cluster_durations[cluster_name] = worked_hours
        total_worked_hours += worked_hours

        cluster_start_times.append(start_time)
        cluster_durations_hours.append(worked_hours)

    return total_worked_hours, cluster_durations, cluster_start_times, cluster_durations_hours


def plot_clusters(cluster_start_times, cluster_durations_hours):
    df = pd.DataFrame({
        "cluster_start_time": cluster_start_times,
        "worked_hours": cluster_durations_hours,
    })

    plt.figure(figsize=(12, 6))
    sns.scatterplot(
        data=df,
        x="cluster_start_time",
        y="worked_hours",
        hue="worked_hours",
        palette="viridis",
        legend=False,
    )
    plt.title("Worked Hours in Each Cluster Over Time")
    plt.xlabel("Cluster Start Time")
    plt.ylabel("Worked Hours")
    plt.show()


def main(directory_path: Path, eps: int, plot: bool) -> None:
    creation_times, file_paths = get_file_creation_times(directory_path)
    clusters, labels = cluster_creation_times(creation_times, eps)

    print("Clusters found:")
    for cluster_label, cluster_times in clusters.items():
        cluster_files = [file_paths[i] for i in range(len(file_paths)) if labels[i] == cluster_label]
        dominant_folder = get_dominant_folder(cluster_files)
        print(
            f"Cluster starting {min(cluster_times).strftime('%Y-%m-%d %H:%M')} in "
            f"{dominant_folder.name}: {len(cluster_times)} files"
        )

    worked_hours, cluster_durations, cluster_start_times, cluster_durations_hours = estimate_worked_hours(
        clusters, file_paths, labels
    )

    print("\nEstimated worked hours per cluster:")
    for cluster_name, duration in cluster_durations.items():
        print(f"{cluster_name}: {duration:.2f} hours")

    print(f"\nTotal estimated worked hours: {worked_hours:.2f}")

    if plot:
        plot_clusters(cluster_start_times, cluster_durations_hours)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Estimate worked hours from file creation timestamps.")
    parser.add_argument(
        "--directory",
        type=Path,
        default=Path.cwd(),
        help="Directory to analyze.",
    )
    parser.add_argument(
        "--timeframe",
        type=float,
        default=1,
        help="Max time between timestamps for clustering (hours).",
    )
    parser.add_argument("--plot", action="store_true", help="Plot clusters over time.")
    return parser.parse_args()


def entrypoint() -> None:
    args = parse_args()
    eps = int(args.timeframe * 3600)
    print(f"Looking for sessions with a max timegap of {args.timeframe} hours in {args.directory}")
    main(args.directory, eps, args.plot)


if __name__ == "__main__":
    entrypoint()
