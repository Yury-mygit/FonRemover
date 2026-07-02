"""Command-line interface for FonRemover.

    fonremover INPUT [-o OUTPUT] [--model MODEL]

INPUT is a single image file or a directory (batch mode — every supported
image in the directory is processed). Output is always a transparent PNG.

Introduced by ideas/Idea_001 (CLI background remover).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterator, Optional, Sequence

from . import __version__
from .core import DEFAULT_MODEL, SUPPORTED_SUFFIXES


def _default_output(src: Path) -> Path:
    """Sibling PNG next to the input: ``photo.jpg`` -> ``photo_nobg.png``."""
    return src.with_name(f"{src.stem}_nobg.png")


def _iter_images(directory: Path) -> Iterator[Path]:
    for path in sorted(directory.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            yield path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fonremover",
        description="Remove image backgrounds (transparent PNG) using rembg / U2-Net.",
    )
    parser.add_argument("input", type=Path, help="input image file or directory")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="output PNG file (single input) or output directory (batch)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"rembg model name (default: {DEFAULT_MODEL})",
    )
    parser.add_argument("--version", action="version", version=f"fonremover {__version__}")
    return parser


def _run_batch(remover, src: Path, output: Optional[Path]) -> int:
    out_dir = output or (src / "nobg")
    images = list(_iter_images(src))
    if not images:
        print(f"no supported images in {src}", file=sys.stderr)
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)
    for img in images:
        dst = remover.process_file(img, out_dir / f"{img.stem}.png")
        print(f"{img.name} -> {dst}")
    print(f"done: {len(images)} image(s)")
    return 0


def _run_single(remover, src: Path, output: Optional[Path]) -> int:
    dst = remover.process_file(src, output or _default_output(src))
    print(f"{src.name} -> {dst}")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    src: Path = args.input
    if not src.exists():
        print(f"error: input not found: {src}", file=sys.stderr)
        return 2

    # Construct the engine (loads the model) only after input validation.
    from .core import BackgroundRemover

    remover = BackgroundRemover(model=args.model)
    if src.is_dir():
        return _run_batch(remover, src, args.output)
    return _run_single(remover, src, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
