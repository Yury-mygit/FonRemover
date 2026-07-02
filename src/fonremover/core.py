"""Core background-removal logic.

Thin wrapper over the rembg (U2-Net ONNX) engine: takes image bytes or file
paths and returns a PNG with the background made transparent. Keeping the
engine behind one class lets the CLI (and any future web layer) reuse a single
loaded model session instead of re-loading it per image.

Introduced by ideas/Idea_001 (CLI background remover).
"""

from __future__ import annotations

from pathlib import Path

# Image extensions rembg / Pillow can decode as input. Output is always PNG
# (only PNG preserves the alpha channel we produce).
SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}

DEFAULT_MODEL = "u2net"


class BackgroundRemover:
    """Removes image backgrounds using a single reused rembg model session.

    The model (~176 MB for ``u2net``) is downloaded by rembg on first use and
    cached under the user's home directory; subsequent runs are offline.
    """

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        # Import lazily so `--help` / `--version` work without the heavy
        # onnxruntime stack loaded (and without the model download).
        from rembg import new_session

        self.model = model
        self._session = new_session(model)

    def remove_bytes(self, data: bytes) -> bytes:
        """Return PNG bytes (with transparent background) for input image bytes."""
        from rembg import remove

        return remove(data, session=self._session)

    def process_file(self, src: Path, dst: Path) -> Path:
        """Remove the background of ``src`` and write the PNG result to ``dst``."""
        result = self.remove_bytes(src.read_bytes())
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(result)
        return dst
