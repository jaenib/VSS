#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="${1:-$ROOT_DIR/outputs/fp_png/fp_complete}"
TRAIN_DIR="${2:-$ROOT_DIR/data/splits/train}"
TEST_DIR="${3:-$ROOT_DIR/data/splits/test}"

mkdir -p "$TRAIN_DIR" "$TEST_DIR"

if [ "${EMPTY_DEST:-true}" = "true" ]; then
    rm -f "$TRAIN_DIR"/*.png "$TEST_DIR"/*.png
fi

shopt -s nullglob
files=("$SRC_DIR"/*.png)

if [ "${#files[@]}" -eq 0 ]; then
    echo "No PNG files found in $SRC_DIR"
    exit 0
fi

num_files=${#files[@]}
half_num_files=$((num_files / 2))

for i in "${!files[@]}"; do
    filename=$(basename "${files[$i]}")
    if [ "$i" -lt "$half_num_files" ]; then
        cp "${files[$i]}" "$TRAIN_DIR/$filename"
    else
        cp "${files[$i]}" "$TEST_DIR/$filename"
    fi
done

echo "Processing complete: Images have been copied to train and test directories."
