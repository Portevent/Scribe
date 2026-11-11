from dataclasses import dataclass

from geometry import Path, Point, Segment

# Point where the pen enters a glyph, in asset coordinates. Connected glyphs start and end on its baseline.
ANCHOR = Point(6.238, 52.724)

# Tolerance used to decide whether a glyph starts at the anchor / ends on the baseline
BASELINE_TOLERANCE = 0.001


@dataclass(frozen=True)
class Character:
    """
    A single glyph of a handwritten font.

    The path is stored in relative commands, starting from the glyph anchor (the point where the
    pen enters the letter, see ANCHOR), so that a character can be appended anywhere in a text.
    """
    char: str  # The represented character: "a", "A", "é", ","...
    path: Path  # Relative path commands, connector move already stripped
    advance_x: float  # Horizontal pen move after drawing the character
    advance_y: float  # Vertical pen move after drawing the character (~0: back on the baseline)
    connects_in: bool  # The glyph starts at the anchor and joins the previous character
    connects_out: bool  # The glyph ends on the baseline so the next character can join
    variant: str | None = None  # Optional name distinguishing alternatives of the same char

    @classmethod
    def from_path(cls, char: str, path: Path, variant: str | None = None) -> 'Character':
        """
        Build a character from an absolute path, as drawn in an asset.
        :param char: The represented character
        :param path: Absolute path of the glyph
        :param variant: Optional variant name
        """
        relative, end = path.to_relative(ANCHOR)
        advance_x, advance_y = end - ANCHOR
        segments = list(relative)

        connects_in = False
        if segments and segments[0].command == "m" and segments[0].args == (0, 0):
            connects_in = True
            segments.pop(0)

        connects_out = abs(advance_y) <= BASELINE_TOLERANCE
        if not connects_out:
            # Bring the pen back to the baseline so the next character starts at the right height
            segments.append(Segment("m", (0, -advance_y)))
            advance_y = 0.0

        return cls(
            char=char,
            path=Path(segments),
            advance_x=advance_x,
            advance_y=advance_y,
            connects_in=connects_in,
            connects_out=connects_out,
            variant=variant,
        )

    def __str__(self) -> str:
        return self.char if self.variant is None else f"{self.char} ({self.variant})"
