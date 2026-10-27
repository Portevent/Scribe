import re

from letterGenerator.path import Path, PathCommand


class LetterGenerator:
    _letter: str  # a / A / b / B / etc
    _path: Path

    continousStart: bool = False
    continousEnd: bool = False

    pathEndX: float
    pathEndY: float

    def __init__(self, letter: str):
        self._letter = letter

    def readPathFromSvg(self, filepath: str):
        """
        Read path from a given svg file. Will read the svg file and look for a d="" which will be used
        :param filepath: Path of the SVG File
        """
        with open(filepath, "r") as file:
            self._path = Path(", ".join(re.findall(" d=\"([a-zA-Z0-9,.\- ]*)\"", file.read())))
            self.pathEndX, self.pathEndY = self._path.toRelative()
            self._analyseContinuity()

    def readPathFromSvgString(self, string: str):
        """
        Read path from a given svg text. Will read the string and look for a d="" which will be used
        :param string: The content of a SVG Image
        """
        self._path = Path(string.split(" d=\"")[1].split('"')[0])
        self.pathEndX, self.pathEndY = self._path.toRelative()
        self._analyseContinuity()

    def readPathFromString(self, string: str):
        """
        Will read a path from a given text
        :param string: E.G. M1,1 L2,2
        """
        self._path = Path(string)
        self.pathEndX, self.pathEndY = self._path.toRelative()
        self._analyseContinuity()

    def _analyseContinuity(self):
        """
        Check wether the path is a continuity of a previous letter, and if it can continue with another letter
        """
        if self._path.pathCommands[0].command_type == "m" and \
                self._path.pathCommands[0].arguments[0] == [0, 0]:
            self.continousStart = True
            self._path.pathCommands.pop(0)

        if abs(self.pathEndY) <= 0.001:
            self.continousEnd = True
        else:
            self._path.pathCommands.append(PathCommand("m 0, " + str(-self.pathEndY)))
            self.pathEndY = 0

    def exportToTemplate(self, filepath: str):
        with open(filepath, "w") as outFile:
            with open(__file__.replace("letterGenerator.py", "letter_template.svg"), "r") as template:
                outFile.write(template.read().replace('d=""', f'd="M0,0\n{self._path.toLine()}"'))

    def printPath(self):
        print(f"Path = {self._path}")

    def getPath(self):
        return self._path

    def getLetter(self):
        return self._letter
