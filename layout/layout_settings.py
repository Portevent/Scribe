from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class LayoutSettings:
    """How a text is laid out. Every length is in millimetres."""
    width: float = 210.0  # Width of the output
    margin: float = 10.0  # Margin on every side
    auto_wrap: bool = True  # Go to a new line when a word doesn't fit in the width
    scale: float = 1.0  # Glyph size multiplier
    line_height: float | None = None  # Distance between baselines (None: computed from the font)
    space_width: float | None = None  # Width of a space (None: the font's " " glyph, or computed from the font)
    jitter: float = 0.0  # Random relative variation of every coordinate (0.05 = up to +/- 2.5 %)
    seed: int | None = None  # Seed for variants and jitter (None: different output on every run)
    on_missing: Literal["skip", "raise"] = "skip"  # What to do with characters the font doesn't have

    def __post_init__(self):
        if self.width - 2 * self.margin <= 0:
            raise ValueError(f"No room left for text: width {self.width} with margin {self.margin}")
        if self.scale <= 0:
            raise ValueError(f"Scale must be positive, got {self.scale}")
        if self.on_missing not in ("skip", "raise"):
            raise ValueError(f"on_missing must be 'skip' or 'raise', got {self.on_missing!r}")
