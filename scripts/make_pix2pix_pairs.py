#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}


def list_images(folder: Path) -> list[Path]:
    return sorted([p for p in folder.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create side-by-side pix2pix training pairs (input | target)."
    )
    parser.add_argument("--input-dir", required=True, help="Folder with input images.")
    parser.add_argument("--target-dir", required=True, help="Folder with target images.")
    parser.add_argument("--output-dir", required=True, help="Output folder for paired images.")
    parser.add_argument(
        "--size",
        type=int,
        default=512,
        help="Resize images to size x size before concatenation.",
    )
    parser.add_argument(
        "--match",
        choices=["name", "order"],
        default="name",
        help="Match pairs by filename or by sorted order.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on number of pairs to write.",
    )
    parser.add_argument(
        "--ext",
        default="png",
        help="Output image extension (default: png).",
    )
    return parser.parse_args()


def pair_by_name(inputs: list[Path], targets: list[Path]) -> list[tuple[Path, Path]]:
    target_map = {p.name: p for p in targets}
    pairs = [(inp, target_map[inp.name]) for inp in inputs if inp.name in target_map]
    if not pairs:
        raise ValueError("No matching filenames between input and target folders.")
    return pairs


def pair_by_order(inputs: list[Path], targets: list[Path]) -> list[tuple[Path, Path]]:
    if len(inputs) != len(targets):
        raise ValueError("Input and target folders must have the same number of images for order matching.")
    return list(zip(inputs, targets))


def main() -> None:
    args = parse_args()

    input_dir = Path(args.input_dir)
    target_dir = Path(args.target_dir)
    output_dir = Path(args.output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    input_images = list_images(input_dir)
    target_images = list_images(target_dir)

    if not input_images:
        raise FileNotFoundError(f"No images found in {input_dir}")
    if not target_images:
        raise FileNotFoundError(f"No images found in {target_dir}")

    if args.match == "name":
        pairs = pair_by_name(input_images, target_images)
    else:
        pairs = pair_by_order(input_images, target_images)

    if args.limit is not None:
        pairs = pairs[: args.limit]

    for index, (input_path, target_path) in enumerate(pairs, start=1):
        input_img = Image.open(input_path).convert("L")
        target_img = Image.open(target_path).convert("L")

        input_img = input_img.resize((args.size, args.size), Image.NEAREST)
        target_img = target_img.resize((args.size, args.size), Image.NEAREST)

        out_img = Image.new("L", (args.size * 2, args.size))
        out_img.paste(input_img, (0, 0))
        out_img.paste(target_img, (args.size, 0))

        out_name = f"{index:05d}.{args.ext}"
        out_img.save(output_dir / out_name)

    print(f"Wrote {len(pairs)} pairs to {output_dir}")


if __name__ == "__main__":
    main()
