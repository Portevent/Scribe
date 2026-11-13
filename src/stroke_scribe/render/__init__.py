from os import PathLike

from stroke_scribe.font import Font
from stroke_scribe.layout import LayoutSettings, TextLayout, Typesetter
from .svg_renderer import SvgRenderer

__all__ = ["SvgRenderer", "render_text", "write_text"]


def render_text(font: Font, text: str, settings: LayoutSettings = LayoutSettings(),
                renderer: SvgRenderer | None = None) -> tuple[str, TextLayout]:
    """
    Lay out the text with the font and render it as an SVG document
    :return: The SVG document, and the layout (e.g. to report missing characters)
    """
    layout = Typesetter(settings).layout(font, text)
    return (renderer or SvgRenderer()).render(layout), layout


def write_text(font: Font, text: str, output: str | PathLike, settings: LayoutSettings = LayoutSettings(),
               renderer: SvgRenderer | None = None) -> TextLayout:
    """
    Lay out the text with the font and write it to output
    :return: The layout, e.g. to report missing characters
    """
    document, layout = render_text(font, text, settings, renderer)
    with open(output, "w", encoding="utf-8") as file:
        file.write(document)
    return layout
