# VSSv1

![VSSv1 preview](assets/hero.png)

VSSv1 is the first milestone in a pipeline for generating architecture floorplans from the Swiss Dwellings dataset. This repo packages the VSSv1 code in a portable, reproducible layout with configurable data/output paths and clear installation steps.

## What this repo does

- Recenter Swiss Dwellings geometries around the origin.
- Render floorplan PNGs from recentered geometries.
- Generate outline/xray variants of rendered floorplans.
- Provide notebooks and scripts for dataset preparation and splitting.

## Repo layout

```
.
├─ src/vssv1/              # Core pipeline modules
├─ notebooks/              # Jupyter notebooks for experiments
├─ scripts/                # Bash helpers (dataset splitting, renaming)
├─ tools/                  # Optional utilities
├─ assets/                 # Project imagery for docs
├─ data/                   # Expected dataset layout (ignored by git)
├─ outputs/                # Rendered images (ignored by git)
├─ requirements.txt
├─ requirements-tools.txt
└─ pyproject.toml
```

## Installation

1) Create and activate a virtual environment.

```
python -m venv .venv
source .venv/bin/activate
```

2) Install dependencies.

```
pip install -e .
```

If you prefer a plain requirements file:

```
pip install -r requirements.txt
```

Optional tools:

```
pip install -r requirements-tools.txt
```

## Dataset setup

By default, the code expects the Swiss Dwellings dataset under `data/`:

```
data/
  source/
    sdd/
      swiss-dwellings-v3.0.0/
        geometries.csv
```

If your dataset lives elsewhere, point to it with:

```
export VSS_DATA_ROOT=/path/to/data
```

## Prepare data

Run the full preparation pipeline (recenter → render → bounds → xray/contour) with one command:

```
./scripts/prepare_data.sh
```

Defaults match the earlier manual steps:

- `GROUP_ID=floor_id`
- `START_ROW=0`
- `END_ROW=200`

You can override any of these:

```
GROUP_ID=floor_id START_ROW=0 END_ROW=200 ./scripts/prepare_data.sh
```

Disable optional steps if needed (useful for headless runs):

```
PLOT_SAMPLE=false OUTLINE=false RUN_BOUNDS=false RUN_XRAY=false ./scripts/prepare_data.sh
```

Rendered images are written to:

```
outputs/fp_png/fp_complete/
outputs/fp_png/fp_outline/
outputs/fp_png/fp_xray/
```

## Configuration

Environment variables:

- `VSS_DATA_ROOT`: where source/processed data lives (default: `./data`).
- `VSS_OUTPUT_ROOT`: where output images are written (default: `./outputs`).
- `VSS_REPO_ROOT`: override repo root if running from elsewhere.

## Notebooks

- `notebooks/01_dwellings_compiler.ipynb`: main exploratory pipeline for recentering + rendering.
- `notebooks/bigDatahandler.ipynb`: image post-processing and dataset splitting helpers.

Run notebooks from the repo root so `Path.cwd()` resolves correctly, or set the environment variables above.

## Notes

- `geopandas` may require system dependencies (GDAL/GEOS). If pip installation fails, consider using Conda.
- The dataset is large; expect multi‑GB storage and long runtimes for full runs.

## License

MIT License. See `LICENSE`.
