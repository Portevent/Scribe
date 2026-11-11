from pathlib import Path as FilePath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from font import Character

LETTER_TEMPLATE = FilePath(__file__).with_name("letter_template.svg")


def export_character_preview(character: 'Character', filepath: str):
    """
    Export a single character to an SVG file, for preview purposes
    :param character: Character to draw
    :param filepath: Where to save the file
    """
    template = LETTER_TEMPLATE.read_text()
    with open(filepath, "w") as outFile:
        outFile.write(template.replace('d=""', f'd="M0,0\n{character.path.to_svg(separator=chr(10))}"'))
