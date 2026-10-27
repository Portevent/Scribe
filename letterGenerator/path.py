import re
from typing import List

# https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Attribute/d#path_commands
# Each path command take a letter for the command type, and some values separated by spaces or coma
# Negative number may omit separator because the minus symbol explicitly separate values
# Commands can be grouped by types : L 10 10 L 20 10 can be written as L 10 10 20 10
# We will call "chunk" a group of values for one command instance, so that one path command may have multiple chunks
# For consistency, we will choose to separate values among a chunk with comas, and separate chunk with spaces
# E.G.: L 10,10 20,10 so that it is more explicit it means (LineTo x=10 y=10) THEN (LineTo x=20 y=10)

EXPECTED_CHUNK_SIZE = { # Number of expected values making up a chunk for each command type
    'm': 2, # MoveTo: M, m
    'l': 2, # LineTo: L, l, H, h, V, v
    'h': 1,
    'v': 1,
    'c': 6, # Cubic Bézier curve: C, c, S, s
    's': 4,
    'q': 4, # Quadratic Bézier curve: Q, q, T, t
    't': 2,
    'a': 7, # Elliptical arc curve: A, a
    'z': 0 # ClosePath
}

CONTINUITY_WIDTH = 6.238
CONTINUITY_HEIGHT = 52.724

ARGUMENT_CHUNK = List[float]

class PathCommand:
    """
    Parse an SVG Path command to extract its type and every chunk of parameters
    """
    command_type: str = None
    arguments: list[ARGUMENT_CHUNK] = None

    def __init__(self, rawCommand: str | None = None, command_type: str | None = None, arguments: List[ARGUMENT_CHUNK] = None):
        """
        Generate a Path command, either from an already parsed type and arguments, or from the raw svg command
        :param rawCommand:
        :param command_type:
        :param arguments:
        """
        if command_type is not None and arguments is not None:
            self.command_type = command_type
            self.arguments = arguments

        if rawCommand is None or rawCommand == "":
            return

        self.command_type = rawCommand[0]
        if self.command_type == "z": # Close Path
            self.arguments = []
            return

        rawCommand = rawCommand[0:].replace(" ", "")
        rawCommand = re.sub("(\.[0-9]*)(\.[0-9]*)", "\g<1> \g<2>",rawCommand)
        rawCommand = re.sub("(\.[0-9]*)(\.[0-9]*)", "\g<1> \g<2>",rawCommand)
        argumentsList = [float(argument) for argument in re.findall("(-?[0-9]*[.[0-9]+]?)", rawCommand)]

        chunkSize: int = EXPECTED_CHUNK_SIZE[self.command_type.lower()]

        argumentsCount: int = len(argumentsList)

        if argumentsCount % chunkSize != 0:
            raise Exception(f"Path Command {rawCommand} has {argumentsCount} parameters, which doesn't correspond to "
                            f"multiple of {chunkSize}")

        self.arguments = [argumentsList[i:i+chunkSize] for i in range(0, argumentsCount, chunkSize)]

    def toLine(self) -> str:
        return self.command_type + " " \
               + ",\n".join([
                                ", ".join(map(str, chunk))
                                    .replace(" 0.0,", " 0,")
                                    .replace(" 1.0,", " 1,")
                                for chunk in self.arguments
                            ])

    def copy(self, pathCommand: 'PathCommand'):
        self.command_type = pathCommand.command_type
        self.arguments = pathCommand.arguments

    def toRelative(self, pointerX: float, pointerY: float) -> ['PathCommand', float, float]:
        relativePath: PathCommand = PathCommand("")
        relativePath.command_type = self.command_type.lower()
        relativePath.arguments = []

        for chunk in self.arguments:
            relativeChunk: list[float] = []
            match self.command_type:
                case "M":
                    relativeChunk = [chunk[0] - pointerX, chunk[1] - pointerY]
                    pointerX = chunk[0]
                    pointerY = chunk[1]
                case "m":
                    relativeChunk = chunk
                    pointerX += chunk[0]
                    pointerY += chunk[1]

                case "L":
                    relativeChunk = [chunk[0] - pointerX, chunk[1] - pointerY]
                    pointerX = chunk[0]
                    pointerY = chunk[1]
                case "l":
                    relativeChunk = chunk
                    pointerX += chunk[0]
                    pointerY += chunk[1]

                case "H":
                    relativeChunk = [chunk[0] - pointerX]
                    pointerX = chunk[0]
                case "h":
                    relativeChunk = chunk
                    pointerX += chunk[0]

                case "V":
                    relativeChunk = [chunk[0] - pointerY]
                    pointerY = chunk[0]
                case "v":
                    relativeChunk = chunk
                    pointerY += chunk[0]

                case "C":
                    relativeChunk = [
                        chunk[0] - pointerX, chunk[1] - pointerY,
                        chunk[2] - pointerX, chunk[3] - pointerY,
                        chunk[4] - pointerX, chunk[5] - pointerY
                    ]
                    pointerX = chunk[4]
                    pointerY = chunk[5]
                case "c":
                    relativeChunk = chunk
                    pointerX += chunk[4]
                    pointerY += chunk[5]

                case "S":
                    relativeChunk = [
                        chunk[0] - pointerX, chunk[1] - pointerY,
                        chunk[2] - pointerX, chunk[3] - pointerY
                    ]
                    pointerX = chunk[2]
                    pointerY = chunk[3]
                case "s":
                    relativeChunk = chunk
                    pointerX += chunk[2]
                    pointerY += chunk[3]

                case "Q":
                    relativeChunk = [
                        chunk[0] - pointerX, chunk[1] - pointerY,
                        chunk[2] - pointerX, chunk[3] - pointerY
                    ]
                    pointerX = chunk[2]
                    pointerY = chunk[3]
                case "q":
                    relativeChunk = chunk
                    pointerX += chunk[2]
                    pointerY += chunk[3]

                case "T":
                    relativeChunk = [chunk[0] - pointerX, chunk[1] - pointerY]
                    pointerX = chunk[0]
                    pointerY = chunk[1]
                case "t":
                    relativeChunk = chunk
                    pointerX += chunk[0]
                    pointerY += chunk[1]

                case "A":
                    relativeChunk = [
                        chunk[0], chunk[1], chunk[2], chunk[3], chunk[4],
                        chunk[5] - pointerX, chunk[6] - pointerY
                    ]
                    pointerX = chunk[5]
                    pointerY = chunk[6]
                case "a":
                    relativeChunk = chunk
                    pointerX += chunk[5]
                    pointerY += chunk[6]

                case "Z" | "z":
                    relativeChunk = chunk

            relativePath.arguments.append(relativeChunk)

        return relativePath, pointerX, pointerY

    def __str__(self):
        return f"<{self.toLine()}>"


class Path:
    """
    Parse an SVG Path Command, and output
    """
    pathCommands: list[PathCommand]

    def __init__(self, raw: str):
        raw = raw.replace("\n", "")
        commands = re.findall("([a-zA-Z][0-9.,\- ]+)", raw)
        self.pathCommands = [PathCommand(command) for command in commands]

    def toLine(self, withNewLine: bool = True) -> str:
        """
        Export the Path to a string to be included in a d=""
        :param withNewLine: Separate command with a new line each
        :return: A string representing the Path
        """
        return ("\n\n" if withNewLine else " ").join([pathCommand.toLine() for pathCommand in self.pathCommands])

    def toRelative(self) -> [float, float]:
        """
        Convert all pathCommands to relative pathCommands
        """
        pointerX: float = CONTINUITY_WIDTH
        pointerY: float = CONTINUITY_HEIGHT
        relativePathCommands: list[PathCommand] = []

        for pathCommand in self.pathCommands:
            relativePathCommand, pointerX, pointerY = pathCommand.toRelative(pointerX, pointerY)
            relativePathCommands.append(relativePathCommand)

        self.pathCommands = relativePathCommands
        print(f"Path converted to relative. Ends at {pointerX} {pointerY}")
        return pointerX-CONTINUITY_WIDTH, pointerY-CONTINUITY_HEIGHT

    def __str__(self):
        return "[\n    " + '\n    '.join(map(str, self.pathCommands)) + "\n]"
