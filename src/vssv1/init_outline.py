from __future__ import annotations

import argparse

import cv2
import numpy as np

from . import bookie, hochbauzeichner, paths


def _read_latest_floorplan():
    latest_image_path = bookie.get_latest_image(paths.fp_complete_dir())
    if latest_image_path is None:
        raise FileNotFoundError("No rendered floorplan images found in outputs/fp_png/fp_complete")
    image = cv2.imread(str(latest_image_path))
    if image is None:
        raise RuntimeError(f"Unable to read image: {latest_image_path}")
    return image


def get_xray() -> None:
    image = _read_latest_floorplan()
    xray_image = hochbauzeichner.get_outline(image)

    out_path = bookie.next_available_filename(paths.ensure_dir(paths.fp_xray_dir()), "OL_xray")
    cv2.imwrite(str(out_path), xray_image)

    print("\nxray has been drawn and saved...")


def get_contour() -> None:
    image = _read_latest_floorplan()

    edges = hochbauzeichner.get_outline(image)
    kernel = np.ones((5, 5), np.uint8)
    closing = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _hierarchy = cv2.findContours(closing, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    contour_image = np.zeros_like(image)
    cv2.drawContours(contour_image, contours, -1, (255, 0, 0), 3)

    out_path = bookie.next_available_filename(paths.ensure_dir(paths.fp_outline_dir()), "OL_outline")
    cv2.imwrite(str(out_path), contour_image)

    print("outline has been drawn and saved...")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate outline and xray images from rendered floorplans.")
    parser.add_argument("--xray", action="store_true", help="Generate xray output.")
    parser.add_argument("--contour", action="store_true", help="Generate contour output.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    run_xray = args.xray or not args.contour
    run_contour = args.contour or not args.xray

    if run_xray:
        get_xray()
    if run_contour:
        get_contour()


if __name__ == "__main__":
    main()
