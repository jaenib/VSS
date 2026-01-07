#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

GROUP_ID="${GROUP_ID:-floor_id}"
GROUP_SLUG="${GROUP_ID%_id}"
RECENTERED_CSV="${RECENTERED_CSV:-data/processed/sdd_recentered/recentered_${GROUP_SLUG}_geometries.csv}"
START_ROW="${START_ROW:-0}"
END_ROW="${END_ROW:-200}"
PLOT_SAMPLE="${PLOT_SAMPLE:-true}"
OUTLINE="${OUTLINE:-true}"
RUN_BOUNDS="${RUN_BOUNDS:-true}"
RUN_XRAY="${RUN_XRAY:-true}"

recenter_args=(--group-id "$GROUP_ID")
if [ "$PLOT_SAMPLE" = "true" ]; then
  recenter_args+=(--plot-sample)
fi

renderer_args=(--recentered-csv "$RECENTERED_CSV" --start-row "$START_ROW" --end-row "$END_ROW")
if [ "$OUTLINE" = "true" ]; then
  renderer_args+=(--outline)
fi

python -m vssv1.recenter "${recenter_args[@]}"
python -m vssv1.fp_renderer "${renderer_args[@]}"

if [ "$RUN_BOUNDS" = "true" ]; then
  python -m vssv1.boundaries --recentered-csv "$RECENTERED_CSV" --method percentile
fi

if [ "$RUN_XRAY" = "true" ]; then
  python -m vssv1.init_outline --xray --contour
fi
