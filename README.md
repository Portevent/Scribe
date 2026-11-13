# Scribe

Scribe writes a text with a **stroke font** and produces an **SVG drawing**, made of strokes (no fill).
The result is meant to be drawn by a pen plotter or a cutting machine, or used as is (default metric is millimeters).

A stroke font is a set of SVG path per letter.

```
python3 main.py assets/font.svg "Hello world" -o hello.svg --x-height 2
```

## Features

- Two font formats:
  - **Inkscape font**: one SVG document where every glyph is a path (or group) labelled with its
    character. Draw the letters on lines, set each object's label (*Object properties > Label*),
    and Scribe finds the rows, baselines and spacing by itself.
  - **Folder of SVG files** (legacy cursive font): one file per glyph, named after the character
    (`a.svg`, `h.svg`). Cursive letters join each other.
- Random **variants** per letter, optional **jitter** on every coordinate, reproducible with a
  seed.
- Layout in millimetres: page width, margins, automatic word wrapping, explicit line breaks,
  letter spacing, line height, space width.
- Size by **x-height** (height of small letters such as `x`), or by a raw scale factor.
- Missing characters are skipped and reported, or rejected with `--strict`.
- No dependency: only the Python standard library (Python 3.10 or newer).

## Usage

### Command line

```
python3 main.py FONT (TEXT | --text-file FILE) [-o OUTPUT.svg] [options]
```

`FONT` is an Inkscape SVG file or a folder of SVG glyphs.

| Option | Default | Description |
|---|---|---|
| `-o`, `--output` | console | SVG file to write. Without it (or with `-`), the SVG is printed to the console. |
| `--text-file FILE` | — | Read the text from a UTF-8 file instead of the command line. |
| `--width MM` | 210 | Page width. |
| `--margin MM` | 10 | Margin on every side. |
| `--no-wrap` | off | Only break lines where the text has line breaks. |
| `--x-height MM` | — | Height of small letters (`x`, `n`, `u`…). Sets the scale. |
| `--scale K` | 1 | Glyph size multiplier (exclusive with `--x-height`). |
| `--letter-spacing MM` | 0 | Extra space between letters, can be negative. |
| `--line-height MM` | from the font | Distance between two lines. |
| `--space MM` | from the font | Width of a space. |
| `--jitter R` | 0 | Random variation, e.g. `0.05` for ± 2.5 %. |
| `--seed N` | random | Same seed → same variants and jitter. |
| `--strict` | off | Fail if a character is missing from the font. |
| `--stroke-width MM` | 0.3 | Stroke width in the SVG. |

Examples:

```
# Small letters 2 mm tall, on a 100 mm wide label
python3 main.py assets/font.svg "Hello world" -o hello.svg --x-height 2 --width 100 --margin 5

# A longer text read from a file
python3 main.py assets/font.svg --text-file resume.txt -o letter.svg --x-height 3

# No -o: the SVG is printed to the console, ready to be piped
python3 main.py assets/font.svg "Hello world" --x-height 2 > hello.svg
```

The command reports the size of the drawing, the scale used and the resulting x-height, and the
characters the font couldn't provide. When the SVG is printed to the console, this report goes to
the error output (stderr) so that the console output stays a valid SVG document.

### Inspecting a font

```
python3 inspect_font.py references/raw/mtg.svg
```

Prints every glyph found in an Inkscape font with its metrics (advance, width, ascent, descent,
whether it joins its neighbours), then a summary: x-height, letters with variants, missing letters
and parser warnings (badly labelled objects, empty glyphs…). Run it after editing a font.

### From Python

```python
from layout import LayoutSettings
from parsers import InkscapeParser
from render import SvgRenderer, render_text, write_text

font = InkscapeParser().parse("assets/font.svg")
settings = LayoutSettings(width=100, margin=5, x_height=2, seed=1)

# Write a file
layout = write_text(font, "Hello world", "hello.svg", settings, SvgRenderer(stroke_width=0.2))
print(layout.lines, layout.missing)

# Or get the SVG document as a string
svg, layout = render_text(font, "Hello world", settings)
```
