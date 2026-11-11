from dataclasses import dataclass

from geometry.point import Point
from geometry.role import ROLES, Role


@dataclass(frozen=True)
class Segment:
    """A single SVG path command with its arguments"""
    command: str
    args: tuple[float, ...] = ()

    def __post_init__(self):
        if self.command.lower() not in ROLES or len(self.command) != 1:
            raise ValueError(f"Unknown path command {self.command!r}")
        args = tuple(float(arg) for arg in self.args)
        if len(args) != len(self.roles):
            raise ValueError(f"Command {self.command!r} expects {len(self.roles)} arguments, got {len(args)}")
        object.__setattr__(self, "args", args)

    @property
    def roles(self) -> tuple[Role, ...]:
        return ROLES[self.command.lower()]

    @property
    def is_relative(self) -> bool:
        return self.command.islower()

    def end_point(self, current: Point, subpath_start: Point) -> Point:
        """
        Where the pen is after this segment
        :param current: Pen position before the segment
        :param subpath_start: Start of the current subpath (where a closepath goes back to)
        """
        if self.command in "zZ":
            return subpath_start
        x, y = (0.0, 0.0) if self.is_relative else current
        has_x = has_y = False
        for value, role in zip(self.args, self.roles):  # The last x / y of a command is its end point
            if role is Role.X:
                x, has_x = value, True
            elif role is Role.Y:
                y, has_y = value, True
        if self.is_relative:
            return Point(current.x + x, current.y + y)
        return Point(x if has_x else current.x, y if has_y else current.y)

    def to_svg(self, precision: int | None = 3) -> str:
        tokens: list[str] = []
        roles = self.roles
        i = 0
        while i < len(self.args):
            if roles[i] is Role.X and i + 1 < len(roles) and roles[i + 1] is Role.Y:
                tokens.append(f"{_format(self.args[i], precision)},{_format(self.args[i + 1], precision)}")
                i += 2
            else:
                value = self.args[i]
                tokens.append(str(int(value)) if roles[i] is Role.FLAG else _format(value, precision))
                i += 1
        return self.command + " ".join(tokens)


def _format(value: float, precision: int | None) -> str:
    text = repr(value) if precision is None else f"{value:.{precision}f}"
    if "." in text and "e" not in text and "E" not in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text
