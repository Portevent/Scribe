import random
from typing import TYPE_CHECKING

from geometry import Path, Role, Segment

if TYPE_CHECKING:
    from font import Character

TEXT_TEMPLATE = __file__.replace("textGenerator.py", "text_template.svg")


def add_error(path: Path, error: float, rng: random.Random | None = None) -> Path:
    """
    Randomly vary every coordinate of the path by up to +/- error/2 (relative)
    """
    if not error:
        return path
    rng = rng or random
    return path.map_coordinates(lambda value, role: value * (1 + (rng.random() - 0.5) * error))


class TextGenerator:
    """
    TextGenerator is a class that handle converting Characters to a text.
    It can adapt text to a A4 page and return to a new line whenever the text reach the end of the line
    """
    _segments: list[Segment]  # The path segments forming the SVG page
    _text: str  # String of all characters in the page (contains \n when it visually return to a new line)
    _autoReturnLine: bool  # Wether or not to return to a new line when reaching the margin
    _margin: float  # Margin of the page (all sides)
    _lineHeight: float  # Space between two lines

    # Used to buffer a word before writing it. So the TextGenerator knows the final size of the word, and return
    # to a new line if needed
    _blockBuffer: list[Segment]
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
        self._text = ""
        self._autoReturnLine = auto_return_line
        self._margin = margin
        self._lineHeight = line_height
        self._blockBuffer = []

        self._segments = [Segment("m", (margin, margin))]
        self.pointerX = margin
        self.pointerY = margin
        self.error = error

    def addLetter(self, letter: 'Character', error: float = None):
        """
        Append a letter in the text
        :param letter: Character to add
        """
        self._addCharacter(letter.path, letter.char, letter.advance_x, letter.advance_y, error=error)

    def addSpace(self, spaceSize: float = 20):
        """
        Add a space
        :param spaceSize: Size of the space (Default 20)
        """
        self._addCharacter(Path([Segment("m", (spaceSize, 0))]), " ", spaceSize, 0, True)

    def addNewLine(self):
        """
        Add a new line
        """
        moveX: float = self._margin - self.pointerX - self._blockPointerX
        moveY: float = self._lineHeight
        self._addCharacter(Path([Segment("m", (moveX, moveY))]), "\n", moveX, moveY, True)

    def _addCharacter(self, path: Path, string: str, deltaX: float, deltaY: float,
                      endOfBlock: bool = False, error: float = None):
        """
        Add a character
        :param path: Relative path of the character
        :param string: The str representation
        :param deltaX: The path ending X
        :param deltaY: The path ending Y
        :param endOfBlock: Whether it closes the block or not (is a space, bot, comma, etc)
        """
        if error is None:
            error = self.error
        self._blockBuffer += add_error(path, error)
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

        self._segments += self._blockBuffer
        self.pointerX += self._blockPointerX
        self.pointerY += self._blockPointerY

        self._blockBuffer, self._blockPointerX, self._blockPointerY = [], 0, 0

    def _checkForNewLine(self, blockSize: float = 20):
        if (self.pointerX + self._margin + blockSize) >= 2100:
            self.addNewLine()

    def getPath(self) -> Path:
        """
        The path of the whole page (block buffer included)
        """
        return Path(self._segments + self._blockBuffer)

    def exportToTemplate(self, filepath: str):
        """
        Export the image to a template SVG with the path inside
        :param filepath: Where to save the file
        """
        self._addBlock()  # In case the block buffer isn't empty

        with open(TEXT_TEMPLATE, "r") as template:
            content = template.read()
        with open(filepath, "w") as outFile:
            outFile.write(content.replace('d=""', f'd="M0,0\n{self.getPath().to_svg(separator=chr(10))}"'))

    def getText(self) -> str:
        """
        Get the text
        :return: What's written in the image
        """
        return self._text
