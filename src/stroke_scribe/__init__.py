"""Write text with a stroke font and produce SVG drawings for pen plotters."""
from importlib.resources import files

from stroke_scribe.font import Character, Font, MissingCharacterError
from stroke_scribe.layout import LayoutSettings, TextLayout, Typesetter
from stroke_scribe.parsers import InkscapeParser, SvgFolderParser
from stroke_scribe.render import SvgRenderer, render_text, write_text

__version__ = "1.0.0"

#: Path of the example Inkscape font shipped with the package
EXAMPLE_FONT = str(files("stroke_scribe") / "assets" / "font.svg")

__all__ = ["Character", "EXAMPLE_FONT", "Font", "InkscapeParser", "LayoutSettings", "MissingCharacterError",
           "SvgFolderParser", "SvgRenderer", "TextLayout", "Typesetter", "render_text", "write_text"]
