import random

from letterGenerator import LetterGenerator
from letterGenerator.path import Path, PathCommand


def add_error_value(value: float, error: float) -> float:
    if value == 1:
        return value
    if value == 0:
        return value
    return value * (1 + (random.random() - 0.5) * error)


def add_error(pathCommand: PathCommand, error: float) -> PathCommand:
    return PathCommand(command=pathCommand.command_type, arguments=
    [
        [add_error_value(value, error) for value in argument]
        for argument in pathCommand.arguments
    ])


class TextGenerator:
    """
    TextGenerator is a class that handle converting LetterGenerator to a text.
    It can adapt text to a A4 page and return to a new line whenever the text reach the end of the line
    """
    _path: Path  # The list of Path command forming the SVG page
    _text: str  # String of all characters in the page (contains \n when it visually return to a new line)
    _autoReturnLine: bool  # Wether or not to return to a new line when reaching the margin
    _margin: float  # Margin of the page (all sides)
    _lineHeight: float  # Space between two lines

    # Used to buffer a word before writing it. So the TextGenerator knows the final size of the word, and return
    # to a new line if needed
    _blockBuffer: list[PathCommand]
    _blockPointerX: float = 0
    _blockPointerY: float = 0

    pointerX: float = 0
    pointerY: float = 0

    def __init__(self, auto_return_line: bool = True, margin: float = 80, line_height: float = 70, error: float = 0.05):
        """
        Configuration of the TextGenerator
        :param auto_return_line: If false, won't return to a new line when reaching the end of the page
        :param margin: Margin of the page (default 80)
        :param line_height: Height of a line (default 70)
        :param error: Variantion in values of path command
        """
        self._path = Path("")
        self._text = ""
        self._autoReturnLine = auto_return_line
        self._margin = margin
        self._lineHeight = line_height
        self._blockBuffer = []

        self._path.pathCommands.append(PathCommand(f"m {margin}, {margin}"))
        self.pointerX = margin
        self.pointerY = margin
        self.error = error

    def addLetter(self, letter: LetterGenerator, error: float = None):
        """
        Append a letter in the text
        :param letter: Letter to add
        """
        self._addCharacter(letter.getPath().pathCommands, letter.getLetter(), letter.pathEndX, letter.pathEndY, error=error)

    def addSpace(self, spaceSize: float = 20):
        """
        Add a space
        :param spaceSize: Size of the space (Default 20)
        """
        self._addCharacter([PathCommand(f"m {spaceSize}, 0")], " ", spaceSize, 0, True)

    def addNewLine(self):
        """
        Add a new line
        """
        moveX: float = self._margin - self.pointerX - self._blockPointerX
        moveY: float = self._lineHeight
        self._addCharacter([PathCommand(command='m', arguments=[[moveX, moveY]])], "\n", moveX, moveY, True)

    def _addCharacter(self, pathCommands: list[PathCommand], string: str, deltaX: float, deltaY: float,
                      endOfBlock: bool = False, error: float = None):
        """
        Add a character
        :param pathCommands: List of the path command of the character
        :param string: The str representation
        :param deltaX: The path ending X
        :param deltaY: The path ending Y
        :param endOfBlock: Whether it closes the block or not (is a space, bot, comma, etc)
        """
        if error is None:
            error = self.error
        self._blockBuffer += [
            add_error(pathCommand, error) for pathCommand in pathCommands
        ]
        self._text += string
        self._blockPointerX += deltaX
        self._blockPointerY += deltaY

        if endOfBlock:
            self._addBlock()

    def _addBlock(self):
        """
        Append the block at the current line or the next one if _autoReturnLine and we reached the end
        """
        if self._autoReturnLine:
            self._checkForNewLine(self._blockPointerX)

        # Edit block Buffer to alter it
        self._path.pathCommands += self._blockBuffer
        self.pointerX += self._blockPointerX
        self.pointerY += self._blockPointerY

        self._blockBuffer, self._blockPointerX, self._blockPointerY = [], 0, 0

    def _checkForNewLine(self, blockSize: float = 20):
        if (self.pointerX + self._margin + blockSize) >= 2100:
            self.addNewLine()

    def exportToTemplate(self, filepath: str):
        """
        Export the image to a template SVG with the path inside
        :param filepath: Where to save the file
        """
        self._addBlock()  # In case the block buffer isn't empty

        with open(filepath, "w") as outFile:
            with open(__file__.replace("textGenerator.py", "text_template.svg"), "r") as template:
                outFile.write(template.read().replace('d=""', f'd="M0,0\n{self._path.toLine()}"'))

    def getText(self) -> str:
        """
        Get the text
        :return: What's written in the image
        """
        return self._text
