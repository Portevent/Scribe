from dataclasses import dataclass, field

from layout.placed_glyph import PlacedGlyph


@dataclass(frozen=True)
class TextLayout:
    """Result of laying out a text: positioned glyphs and the size of the area (millimetres)"""
    glyphs: tuple[PlacedGlyph, ...]
    width: float
    height: float
    lines: int
    missing: frozenset[str] = field(default_factory=frozenset)  # Characters the font couldn't provide

    @property
    def text(self) -> str:
        """The characters actually drawn"""
        return "".join(glyph.character.char for glyph in self.glyphs)
