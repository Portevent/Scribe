
## Project layout

| Path | Content |
|---|---|
| `geometry/` | SVG path parsing and transformations, bounding boxes. |
| `font/` | `Character` (one glyph) and `Font` (characters and their variants). |
| `parsers/` | Font loaders: `InkscapeParser`, `SvgFolderParser`. |
| `layout/` | `LayoutSettings`, `Typesetter` (line breaking and placement), `TextLayout`. |
| `render/` | `SvgRenderer` and `write_text`. |
| `main.py`, `inspect_font.py` | Command-line tools. |
| `tests/` | Unit tests. |
| `docs/TECHNICAL.md` | How the library works internally. |

Run the tests with:

```
python3 -W error -m unittest discover -s tests -t .
```

The font assets (`references/`) and the tests are currently not versioned (see `.gitignore`).

## Status and work in progress

Working: both font formats, layout, sizing, variants, jitter, SVG output.

To be reworked or not done yet:

- **Cursive joins**: the legacy cursive font's flags for "this letter joins the next one" are
  computed with an exact tolerance and are wrong for several letters (`b`, `c`, `d`, `g`, `o`,
  `v`, `w`…). With `--letter-spacing` different from 0, some cursive words get cut apart. Join
  detection needs a tolerance and support for exits above the baseline.
- **Inspector**: a print letter whose stroke happens to end at the exit point (`u` in `mtg.svg`)
  is reported as joining the next letter.
- **Layout**: no kerning, no centred / right-aligned / justified text, no pagination.
- `cleaner/` is a leftover of the first version and will be removed.
