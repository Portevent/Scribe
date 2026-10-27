import random

from cleaner import FileCleaner, FormatterCleaner
from letterGenerator import LetterGenerator, TextGenerator
from letterGenerator.scribe import Scribe

referenceFolder: str = f'references/raw/SVG/'
cleanFolder: str = f'references/clean/SVG/'
genFolder: str = f'references/generated/'


from os import listdir
from os.path import isfile, join

# Fetching letters
files = [f.split('.svg')[0] for f in listdir(referenceFolder) if isfile(join(referenceFolder, f))]

# List of all letter Generators that can be used
scribe: Scribe = Scribe()

# Cleaning all letters
for file in files:
    letter = file[0]  # First char of filename
    fileCleaner: FileCleaner = FileCleaner(referenceFolder + file + ".svg",
                                           cleanFolder + file + ".svg", FormatterCleaner())
    fileCleaner.export()

    letterTest: LetterGenerator = LetterGenerator(letter)
    letterTest.readPathFromSvg(cleanFolder + file + ".svg")
    letterTest.exportToTemplate(genFolder + file + ".svg")
    scribe.add_letter(letter, letterTest)


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
                    textGenerator.addLetter(scribe.get_letter(char), error=0.05)
            except Exception as e:
                errors[char] = True

file_name: str = textGenerator.getText()[0:40].replace('\n', ' ')
textGenerator.exportToTemplate(f"references/generated/{file_name}.svg")

print(f"Exported to {file_name}")
print(errors.keys())