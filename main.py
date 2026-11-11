import re
from os import listdir
from os.path import isfile, join

from cleaner import FileCleaner, FormatterCleaner
from font import Character, Font, MissingCharacterError
from letterGenerator import TextGenerator, export_character_preview
from geometry import Path

referenceFolder: str = f'references/raw/SVG/'
cleanFolder: str = f'references/clean/SVG/'
genFolder: str = f'references/generated/'


def _load_legacy_svg(filepath: str) -> Path:
    """
    TEMPORARY: read every d="" of an SVG file as one absolute path.
    To be replaced by the upcoming font parsers (SVG folder, Inkscape project).
    """
    with open(filepath, "r") as file:
        return Path.parse(" ".join(re.findall(r' d="([^"]*)"', file.read())))


# Fetching letters
files = [f.split('.svg')[0] for f in listdir(referenceFolder) if isfile(join(referenceFolder, f))]

font: Font = Font("references")

# Cleaning all letters
for file in files:
    char = file[0]  # First char of filename, e.g. "a.svg", "A -.svg", "A - bis.svg"
    variant = file[1:].strip(" -") or None
    fileCleaner: FileCleaner = FileCleaner(referenceFolder + file + ".svg",
                                           cleanFolder + file + ".svg", FormatterCleaner())
    fileCleaner.export()

    character = Character.from_path(char, _load_legacy_svg(cleanFolder + file + ".svg"), variant)
    export_character_preview(character, genFolder + file + ".svg")
    font.add(character)


textGenerator: TextGenerator = TextGenerator(error=0, margin=300)

errors = {}

with open('text.txt', 'r', encoding="utf-8") as f:
    for line in f.readlines():
        for char in line:
            try:
                if char == " ":
                    textGenerator.addSpace()
                elif char == "\n":
                    textGenerator.addNewLine()
                else:
                    textGenerator.addLetter(font.get(char), error=0.05)
            except MissingCharacterError:
                errors[char] = True

file_name: str = textGenerator.getText()[0:40].replace('\n', ' ')
textGenerator.exportToTemplate(f"references/generated/{file_name}.svg")

print(f"Exported to {file_name}")
print(errors.keys())
