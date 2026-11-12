import re
from os import PathLike, fspath
from pathlib import Path as FilePath

from font import Character, Font
from font.character import ANCHOR
from geometry import Path, Point
from parsers.font_parser import FontParser

_PATH_DATA_RE = re.compile(r'\sd="([^"]*)"')


class SvgFolderParser(FontParser):
    """
    Read a font made of one SVG file per glyph (the legacy cursive assets).

    - The character is the first letter of the file name; the rest, stripped of spaces and dashes,
      is the variant name: "a.svg" -> a, "A -.svg" -> A, "h - bis.svg" -> h (variant "bis").
    - Every d="" of a file is part of the glyph. The pen enters at ANCHOR and leaves where the path ends.
    - Asset units are tenths of millimetres: scale=0.1 gives millimetres.
    """

    def __init__(self, scale: float = 0.1, anchor: Point = ANCHOR):
        self.scale = scale
        self.anchor = anchor

    def parse(self, source: str | PathLike) -> Font:
        folder = FilePath(fspath(source))
        if not folder.is_dir():
            raise ValueError(f"{folder} is not a folder")

        font = Font(folder.name)
        origin = Point(self.anchor.x * self.scale, self.anchor.y * self.scale)
        for file in sorted(folder.glob("*.svg")):
            content = file.read_text(encoding="utf-8", errors="replace")
            try:
                path = Path.parse(" ".join(_PATH_DATA_RE.findall(content)))
            except ValueError as error:
                raise ValueError(f"Invalid path data in {file}: {error}") from error
            char, variant = file.stem[0], file.stem[1:].strip(" -") or None
            font.add(Character.from_path(char, path.scale(self.scale), variant, origin))
        return font
