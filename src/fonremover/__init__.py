"""FonRemover — remove image backgrounds (transparent PNG) using rembg / U2-Net.

Public package surface: the :class:`BackgroundRemover` engine and the package
version. The CLI lives in :mod:`fonremover.cli`.

Introduced by ideas/Idea_001 (CLI background remover).
"""

from .core import BackgroundRemover

__version__ = "0.1.0"

__all__ = ["BackgroundRemover", "__version__"]
