from os import PathLike
from xml.sax.saxutils import quoteattr

from stroke_scribe.geometry import Path, Segment
from stroke_scribe.layout import TextLayout


class SvgRenderer:
    """Write a laid out text as an SVG document in millimetres"""

    def __init__(self, stroke: str = "#000", stroke_width: float = 0.3, precision: int = 3):
        """
        :param stroke: Stroke colour
        :param stroke_width: Stroke width in millimetres
        :param precision: Decimals of the coordinates (3 = micrometres)
        """
        self.stroke = stroke
        self.stroke_width = stroke_width
        self.precision = precision

    def path_data(self, layout: TextLayout) -> str:
        """Content of the d attribute: every glyph drawn from its origin, one glyph per line"""
        return "\n".join(
            (Path([Segment("M", glyph.origin)]) + glyph.path).to_svg(self.precision)
            for glyph in layout.glyphs
        )

    def render(self, layout: TextLayout) -> str:
        width, height = _number(layout.width), _number(layout.height)
        style = f"fill:none;stroke:{self.stroke};stroke-width:{_number(self.stroke_width)};" \
                f"stroke-linecap:round;stroke-linejoin:round"
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm" '
            f'viewBox="0 0 {width} {height}">\n'
            f'  <path style={quoteattr(style)} d="{self.path_data(layout)}"/>\n'
            '</svg>\n'
        )

    def write(self, layout: TextLayout, file: str | PathLike):
        with open(file, "w", encoding="utf-8") as output:
            output.write(self.render(layout))


def _number(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")
