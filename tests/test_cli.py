"""Lightweight CLI tests that don't touch the heavy rembg model.

These cover argument parsing and output-path resolution — the parts that must
stay correct regardless of the ML engine. Real background-removal quality is a
user-zone / manual smoke check (see ideas/Idea_001/Card.md, Stage 4).
"""

from pathlib import Path

import pytest

from fonremover import __version__
from fonremover.cli import _default_output, build_parser


def test_default_output_is_sibling_png():
    assert _default_output(Path("a/b/photo.jpg")) == Path("a/b/photo_nobg.png")


def test_parser_reads_input_and_output():
    args = build_parser().parse_args(["in.jpg", "-o", "out.png"])
    assert args.input == Path("in.jpg")
    assert args.output == Path("out.png")
    assert args.model == "u2net"


def test_version_flag_reports_package_version(capsys):
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out
