from dataclasses import dataclass

from font import Character
from geometry import Path, Point


@dataclass(frozen=True)
class PlacedGlyph:
    """A character positioned in a text"""
    character: Character
    origin: Point  # Pen position before drawing the glyph, on the baseline
    path: Path  # Relative path to draw from origin (scaled and jittered)
