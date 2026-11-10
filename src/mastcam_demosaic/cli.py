"""Command line interface for mastcam-demosaic."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .demosaic import PATTERNS, demosaic_file


def default_output_path(src: Path) -> Path:
    """Insert ".demosaic" before the extension: ``a.jpg`` -> ``a.demosaic.jpg``."""
    return src.with_name(f"{src.stem}.demosaic{src.suffix}")


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mastcam-demosaic",
        description="De-mosaic (colorize) a raw Bayer-pattern MastCam image.",
    )
    parser.add_argument("input", type=Path, help="path to the raw Bayer image")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="where to save the result (default: INPUT with '.demosaic' "
        "inserted before the extension)",
    )
    parser.add_argument(
        "-p",
        "--pattern",
        default="RGGB",
        type=str.upper,
        choices=PATTERNS,
        help="Bayer layout of the top-left 2x2 pixels (default: %(default)s, "
        "as used by MastCam)",
    )
    colors = parser.add_mutually_exclusive_group()
    colors.add_argument(
        "--natural",
        dest="color",
        action="store_const",
        const="natural",
        help="calibrate to estimated natural color: the scene as it would "
        "look to a person standing on Mars",
    )
    colors.add_argument(
        "--white-balanced",
        dest="color",
        action="store_const",
        const="white-balanced",
        help="calibrate and white balance: the terrain as it would look "
        "under Earth-like lighting",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=95,
        help="JPEG quality for the output, 1-95 (default: %(default)s)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    src: Path = args.input
    dst: Path = args.output or default_output_path(src)

    if not src.is_file():
        print(f"mastcam-demosaic: error: no such file: {src}", file=sys.stderr)
        return 1

    try:
        demosaic_file(
            src, dst, pattern=args.pattern, quality=args.quality, color=args.color or "raw"
        )
    except (OSError, ValueError) as exc:
        print(f"mastcam-demosaic: error: {exc}", file=sys.stderr)
        return 1

    print(f"Saved {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
