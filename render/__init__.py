from os import PathLike

from font import Font
from layout import LayoutSettings, TextLayout, Typesetter
from .svg_renderer import SvgRenderer

__all__ = ["SvgRenderer", "write_text"]


def write_text(font: Font, text: str, output: str | PathLike, settings: LayoutSettings = LayoutSettings(),
               renderer: SvgRenderer | None = None) -> TextLayout:
    """
    Lay out the text with the font and write it to output
    :return: The layout, e.g. to report missing characters
    """
    layout = Typesetter(settings).layout(font, text)
    (renderer or SvgRenderer()).write(layout, output)
    return layout
