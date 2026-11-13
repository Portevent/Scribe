from dataclasses import dataclass
from functools import cached_property

from stroke_scribe.geometry import BoundingBox, Path, Point, Segment

# Default point where the pen enters a glyph, in legacy asset coordinates.
# Connected glyphs start and end on its baseline.
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
    def from_path(cls, char: str, path: Path, variant: str | None = None,
                  origin: Point = ANCHOR, exit_point: Point | None = None) -> 'Character':
        """
        Build a character from an absolute path, as drawn in an asset.
        :param char: The represented character
        :param path: Absolute path of the glyph
        :param variant: Optional variant name
        :param origin: Where the pen is before drawing the glyph (on the baseline)
        :param exit_point: Where the pen must be after the glyph. If None, it stays where the path ends,
                           brought back to the baseline (origin's height).
        """
        relative, end = path.to_relative(origin)
        segments = list(relative)

        connects_in = False
        if segments and segments[0].command == "m" and segments[0].args == (0, 0):
            connects_in = True
            segments.pop(0)

        if exit_point is None:
            exit_point = Point(end.x, origin.y)
            connects_out = abs(end.y - origin.y) <= BASELINE_TOLERANCE
            if connects_out:
                exit_point = end  # Keep the exact residual, like the legacy implementation
        else:
            connects_out = abs(end.x - exit_point.x) <= BASELINE_TOLERANCE \
                and abs(end.y - exit_point.y) <= BASELINE_TOLERANCE

        if not connects_out:
            # Move the pen to the exit point so the next character starts at the right place
            segments.append(Segment("m", tuple(exit_point - end)))
        advance_x, advance_y = exit_point - origin

        return cls(
            char=char,
            path=Path(segments),
            advance_x=advance_x,
            advance_y=advance_y,
            connects_in=connects_in,
            connects_out=connects_out,
            variant=variant,
        )

    @cached_property
    def bounds(self) -> BoundingBox | None:
        """
        Bounding box of the drawn glyph, relative to its origin (y grows downwards):
        -bounds.min_y is the ascent above the baseline, bounds.max_y the descent below it.
        """
        return self.path.bounding_box()

    def __str__(self) -> str:
        return self.char if self.variant is None else f"{self.char} ({self.variant})"
