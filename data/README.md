# Data layout

This repo expects the Swiss Dwellings dataset and derived files to live under `data/` by default.

Suggested layout:

```
data/
  source/
    sdd/
      swiss-dwellings-v3.0.0/
        geometries.csv
        recentered_floor_geometries.csv   # optional, if you already have it
  processed/
    sdd_recentered/
      recentered_floor_geometries.csv    # created by vssv1.recenter
```

You can keep the dataset elsewhere and point to it with:

```
export VSS_DATA_ROOT=/path/to/data
```
