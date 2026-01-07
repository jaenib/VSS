#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="${1:-$ROOT_DIR/outputs/fp_png/fp_combine}"
PREFIX="${2:-FP_combine_}"

if [ ! -d "$SRC_DIR" ]; then
    echo "Source directory not found: $SRC_DIR"
    exit 1
fi

cd "$SRC_DIR"

shopt -s nullglob
for old_name in ${PREFIX}*.png; do
    num=$(echo "$old_name" | sed -e "s/${PREFIX}//" -e 's/\.png//')
    num=$(echo "$num" | sed 's/^0*//')

    if [ -z "$num" ]; then
        num=0
    fi

    new_name="$num.png"
    mv "$old_name" "$new_name"
done

echo "Renaming complete: Files have been renamed."
