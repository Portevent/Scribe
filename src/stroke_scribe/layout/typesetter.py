import random
import re
import statistics

from stroke_scribe.font import Character, Font, MissingCharacterError
from stroke_scribe.geometry import Path, Point
from stroke_scribe.layout.layout_settings import LayoutSettings
from stroke_scribe.layout.placed_glyph import PlacedGlyph
from stroke_scribe.layout.text_layout import TextLayout

LINE_SPACING = 1.2  # Default line height = LINE_SPACING x (highest ascent + deepest descent)
SPACE_RATIO = 0.5  # Default space width = SPACE_RATIO x median glyph advance
TAB_SIZE = 4  # A tab is that many spaces
_TOKEN_RE = re.compile(r" +|[^ ]+")


class Typesetter:
    """Place the characters of a text, line after line, according to the settings"""

    def __init__(self, settings: LayoutSettings = LayoutSettings()):
        self.settings = settings

    def layout(self, font: Font, text: str) -> TextLayout:
        """
        :raise MissingCharacterError: if a character is missing and settings.on_missing is "raise"
        """
        return _Run(font, self.settings).typeset(text)


class _Run:
    """State of one layout: pen position, placed glyphs..."""

    def __init__(self, font: Font, settings: LayoutSettings):
        self.font = font
        self.settings = settings
        self.rng = random.Random(settings.seed)
        self.content_width = settings.width - 2 * settings.margin

        self.scale = _scale(font, settings)
        ascent, descent, median_advance = _metrics(font)
        self.ascent = ascent * self.scale
        self.descent = descent * self.scale
        self.line_height = settings.line_height if settings.line_height is not None \
            else LINE_SPACING * (self.ascent + self.descent)
        if settings.space_width is not None:
            self.space_width = settings.space_width
        elif " " in font:
            self.space_width = font.get(" ").advance_x * self.scale
        else:
            self.space_width = SPACE_RATIO * median_advance * self.scale

        self.glyphs: list[PlacedGlyph] = []
        self.missing: set[str] = set()
        self.line = 0  # Index of the current line
        self.x = 0.0  # Pen position from the left of the content area
        self.max_x = 0.0

    def typeset(self, text: str) -> TextLayout:
        for index, line in enumerate(text.replace("\r\n", "\n").split("\n")):
            if index:
                self.new_line()
            self.typeset_line(line.replace("\t", " " * TAB_SIZE))

        margin = self.settings.margin
        return TextLayout(
            glyphs=tuple(self.glyphs),
            width=max(self.settings.width, self.max_x + 2 * margin),
            height=self.baseline() + self.descent + margin,
            lines=self.line + 1,
            missing=frozenset(self.missing),
            scale=self.scale,
        )

    def typeset_line(self, line: str):
        pending_space = 0.0  # Spaces are only drawn if a word follows them on the same line
        wrapped = False  # The current line was started by an automatic wrap
        for token in _TOKEN_RE.findall(line):
            if token[0] == " ":
                if not (wrapped and self.x == 0):  # No leading space after a wrap (indentation is kept)
                    pending_space += len(token) * self.space_width
                continue

            characters = [character for character in map(self.character, token) if character is not None]
            gaps = [0.0] + [self.gap(previous, following) for previous, following in zip(characters, characters[1:])]
            word_width = sum(self.advance(character) for character in characters) + sum(gaps)
            if self.should_wrap(pending_space + word_width):
                self.new_line()
                wrapped, pending_space = True, 0.0
            self.x += pending_space
            pending_space = 0.0

            for character, gap in zip(characters, gaps):
                if self.should_wrap(gap + self.advance(character)):  # Only a word longer than a line gets here
                    self.new_line()
                    wrapped = True
                else:
                    self.x += gap
                self.place(character)

    def gap(self, previous: Character, following: Character) -> float:
        """Letter spacing between two glyphs of a word (none inside joined handwriting)"""
        if previous.connects_out and following.connects_in:
            return 0.0
        return self.settings.letter_spacing

    def should_wrap(self, width: float) -> bool:
        return self.settings.auto_wrap and self.x > 0 and self.x + width > self.content_width + 1e-9

    def character(self, char: str) -> Character | None:
        try:
            return self.font.get(char, self.rng)
        except MissingCharacterError:
            if self.settings.on_missing == "raise":
                raise
            self.missing.add(char)
            return None

    def advance(self, character: Character) -> float:
        return character.advance_x * self.scale

    def place(self, character: Character):
        path = character.path.scale(self.scale)
        if self.settings.jitter:
            jitter = self.settings.jitter
            path = path.map_coordinates(lambda value, role: value * (1 + (self.rng.random() - 0.5) * jitter))
        origin = Point(self.settings.margin + self.x, self.baseline())
        self.glyphs.append(PlacedGlyph(character, origin, path))
        self.x += self.advance(character)
        self.max_x = max(self.max_x, self.x)

    def new_line(self):
        self.line += 1
        self.x = 0.0

    def baseline(self) -> float:
        return self.settings.margin + self.ascent + self.line * self.line_height


def _scale(font: Font, settings: LayoutSettings) -> float:
    """Glyph scale: given directly, or derived from the wanted x-height"""
    if settings.x_height is None:
        return settings.scale
    font_x_height = font.x_height
    if not font_x_height:
        raise ValueError(f"Font {font.name!r} has no lowercase letter to measure its x-height")
    return settings.x_height / font_x_height


def _metrics(font: Font) -> tuple[float, float, float]:
    """Highest ascent, deepest descent and median advance of the font's glyphs (font units)"""
    characters = [character for char in font.chars for character in font.variants(char)]
    boxes = [character.bounds for character in characters if character.bounds is not None]
    ascent = max((-box.min_y for box in boxes), default=0.0)
    descent = max((box.max_y for box in boxes), default=0.0)
    advances = [character.advance_x for character in characters if character.advance_x > 0]
    return max(ascent, 0.0), max(descent, 0.0), statistics.median(advances) if advances else 0.0
