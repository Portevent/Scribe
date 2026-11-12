"""
Parse an Inkscape font file and print what the parser understood, glyph by glyph.

Usage: python3 inspect_font.py [file.svg] [--spacing MM] [--scale K]
"""
import argparse
import string
import warnings

from font import Character, Font
from parsers import InkscapeParser

DEFAULT_FILE = "references/raw/mtg.svg"
EXPECTED = string.ascii_lowercase + string.ascii_uppercase


def continuity(character: Character) -> str:
    if character.connects_in and character.connects_out:
        return "continuous"
    if character.connects_in:
        return "joins previous only"
    if character.connects_out:
        return "joins next only"
    return "discontinuous"


def print_characters(font: Font):
    variant_width = max([len("variant")] + [len(str(c.variant)) for char in font.chars for c in font.variants(char)]) + 2
    header = f"{'char':<5}{'variant':<{variant_width}}{'continuity':<21}{'advance':>8}{'width':>8}{'ascent':>8}{'descent':>8}"
    print(header)
    print("-" * len(header))
    for char in sorted(font.chars):
        for character in font.variants(char):
            bounds = character.bounds
            print(f"{char!r:<5}{str(character.variant):<{variant_width}}{continuity(character):<21}"
                  f"{character.advance_x:>8.2f}{bounds.width:>8.2f}{-bounds.min_y:>8.2f}{bounds.max_y:>8.2f}")


def print_summary(font: Font, problems: list[str]):
    characters = [character for char in font.chars for character in font.variants(char)]
    counts: dict[str, int] = {}
    for character in characters:
        counts[continuity(character)] = counts.get(continuity(character), 0) + 1

    print(f"\nFont {font.name!r}: {len(font)} characters, {len(characters)} glyphs (variants included)")
    for kind, count in sorted(counts.items()):
        print(f"  {kind}: {count}")

    with_variants = sorted(char for char in font.chars if len(font.variants(char)) > 1)
    print(f"Characters with variants: {' '.join(with_variants) or '-'}")
    missing = [char for char in EXPECTED if char not in font]
    print(f"Missing letters: {' '.join(missing) or '-'}")
    extra = sorted(char for char in font.chars if char not in EXPECTED)
    print(f"Other characters: {' '.join(map(repr, extra)) or '-'}")

    print(f"Parser warnings: {len(problems) or '-'}")
    for problem in problems:
        print(f"  {problem}")


def main():
    arguments = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    arguments.add_argument("file", nargs="?", default=DEFAULT_FILE, help=f"Inkscape SVG file (default {DEFAULT_FILE})")
    arguments.add_argument("--spacing", type=float, default=0.0, help="letter spacing in millimetres")
    arguments.add_argument("--scale", type=float, default=1.0, help="output scale (1 = millimetres)")
    options = arguments.parse_args()

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        font = InkscapeParser(letter_spacing=options.spacing, scale=options.scale).parse(options.file)

    print_characters(font)
    print_summary(font, [str(warning.message) for warning in caught])


if __name__ == "__main__":
    main()
