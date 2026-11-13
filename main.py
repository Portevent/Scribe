"""
Write a text with a handwritten font into an SVG file.

Examples:
  python3 main.py references/raw/mtg.svg "Hello world" -o hello.svg --width 100
  python3 main.py references/raw/SVG --text-file text.txt -o letter.svg --jitter 0.05
"""
import argparse
import sys
from pathlib import Path as FilePath

from font import Font
from layout import LayoutSettings
from parsers import InkscapeParser, SvgFolderParser
from render import SvgRenderer, write_text


def load_font(source: str) -> Font:
    """A folder is a set of SVG glyph files, a file is an Inkscape font"""
    if FilePath(source).is_dir():
        return SvgFolderParser().parse(source)
    return InkscapeParser().parse(source)


def main():
    arguments = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0],
                                        epilog="\n".join(__doc__.strip().splitlines()[1:]),
                                        formatter_class=argparse.RawDescriptionHelpFormatter)
    arguments.add_argument("font", help="Inkscape SVG font file, or folder of SVG glyphs")
    text_source = arguments.add_mutually_exclusive_group(required=True)
    text_source.add_argument("text", nargs="?", help="text to write")
    text_source.add_argument("--text-file", help="read the text from this file (UTF-8)")
    arguments.add_argument("-o", "--output", required=True, help="SVG file to write")

    defaults = LayoutSettings()
    settings = arguments.add_argument_group("layout (lengths in millimetres)")
    settings.add_argument("--width", type=float, default=defaults.width, help=f"default {defaults.width}")
    settings.add_argument("--margin", type=float, default=defaults.margin, help=f"default {defaults.margin}")
    settings.add_argument("--no-wrap", action="store_true", help="only go to a new line on line breaks of the text")
    settings.add_argument("--letter-spacing", type=float, default=defaults.letter_spacing,
                          help="extra space between letters (can be negative)")
    size = settings.add_mutually_exclusive_group()
    size.add_argument("--x-height", type=float, help="height of small letters like 'x' (sets the scale)")
    size.add_argument("--scale", type=float, default=defaults.scale, help="glyph size multiplier")
    settings.add_argument("--line-height", type=float, help="distance between lines (default: from the font)")
    settings.add_argument("--space", type=float, help="width of a space (default: from the font)")
    settings.add_argument("--jitter", type=float, default=defaults.jitter, help="random variation, e.g. 0.05")
    settings.add_argument("--seed", type=int, help="make variants and jitter reproducible")
    settings.add_argument("--strict", action="store_true", help="fail on characters missing from the font")
    settings.add_argument("--stroke-width", type=float, default=0.3, help="default 0.3")
    options = arguments.parse_args()

    text = FilePath(options.text_file).read_text(encoding="utf-8") if options.text_file else options.text
    try:
        layout_settings = LayoutSettings(
            width=options.width, margin=options.margin, auto_wrap=not options.no_wrap, scale=options.scale, x_height=options.x_height,
            letter_spacing=options.letter_spacing,
            line_height=options.line_height, space_width=options.space, jitter=options.jitter, seed=options.seed,
            on_missing="raise" if options.strict else "skip",
        )
        font = load_font(options.font)
        layout = write_text(font, text, options.output, layout_settings, SvgRenderer(stroke_width=options.stroke_width))
    except (ValueError, KeyError, OSError) as error:
        sys.exit(f"Error: {error}")

    print(f"Wrote {options.output}: {layout.width:.1f} x {layout.height:.1f} mm, {layout.lines} line(s), "
          f"{len(layout.glyphs)} glyphs from font {font.name!r}")
    if font.x_height:
        print(f"Scale {layout.scale:.3g}: small letters are {font.x_height * layout.scale:.2f} mm tall")
    if layout.missing:
        print(f"Missing characters (skipped): {' '.join(sorted(layout.missing))}")


if __name__ == "__main__":
    main()
