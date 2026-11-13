"""
SVG path geometry.

A Path is an immutable sequence of Segments, one SVG command each
(e.g. "c 1,2 3,4 5,6 7,8 9,10 11,12" is stored as two "c" segments).
Reference: https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Attribute/d#path_commands
"""
import re
from typing import Callable, Iterable, Iterator

from stroke_scribe.geometry import flatten
from stroke_scribe.geometry.bounding_box import BoundingBox
from stroke_scribe.geometry.point import Point
from stroke_scribe.geometry.role import ROLES, Role
from stroke_scribe.geometry.segment import Segment

_COMMAND_LETTERS = "MmZzLlHhVvCcSsQqTtAa"
_COMMAND_RE = re.compile(rf"([{_COMMAND_LETTERS}])([^{_COMMAND_LETTERS}]*)")
_NUMBER_RE = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_SEPARATOR_RE = re.compile(r"[\s,]*")


class Path:
    """An immutable sequence of path segments"""

    def __init__(self, segments: Iterable[Segment] = ()):
        self._segments: tuple[Segment, ...] = tuple(segments)

    @classmethod
    def parse(cls, d: str) -> 'Path':
        """
        Parse the content of an SVG d="" attribute
        :raise ValueError: on malformed data
        """
        stripped = d.strip()
        if stripped and stripped[0] not in _COMMAND_LETTERS:
            raise ValueError(f"Path data must start with a command: {d[:20]!r}")

        segments: list[Segment] = []
        for match in _COMMAND_RE.finditer(stripped):
            command, raw_args = match.group(1), match.group(2)
            roles = ROLES[command.lower()]
            values = _tokenize(raw_args, roles, match.start(2))

            if not roles:
                if values:
                    raise ValueError(f"Command {command!r} takes no argument (at {match.start()})")
                segments.append(Segment(command))
                continue
            if not values or len(values) % len(roles):
                raise ValueError(f"Command {command!r} at {match.start()} has {len(values)} arguments, "
                                 f"expecting a multiple of {len(roles)}")
            for i in range(0, len(values), len(roles)):
                chunk_command = command
                if i and command in "Mm":  # Extra pairs after a moveto are implicit linetos
                    chunk_command = "L" if command == "M" else "l"
                segments.append(Segment(chunk_command, tuple(values[i:i + len(roles)])))
        return cls(segments)

    @property
    def segments(self) -> tuple[Segment, ...]:
        return self._segments

    def _walk(self, start: Point) -> Iterator[tuple[Segment, Point, Point]]:
        """Yield each segment with the pen position before and after it"""
        current = subpath_start = start
        for segment in self._segments:
            end = segment.end_point(current, subpath_start)
            yield segment, current, end
            if segment.command in "Mm":
                subpath_start = end
            current = end

    def end_point(self, start: Point = Point(0, 0)) -> Point:
        """
        Where the pen ends after drawing the path
        :param start: Pen position before the path (used by relative commands)
        """
        end = start
        for _, _, end in self._walk(start):
            pass
        return Point(*end)

    def to_relative(self, start: Point = Point(0, 0)) -> tuple['Path', Point]:
        """
        Convert every segment to a relative command
        :param start: Pen position before the path
        :return: The relative path and the absolute end point
        """
        segments: list[Segment] = []
        end = start
        for segment, current, end in self._walk(start):
            if segment.is_relative:
                segments.append(segment)
                continue
            args = tuple(
                value - current.x if role is Role.X else value - current.y if role is Role.Y else value
                for value, role in zip(segment.args, segment.roles)
            )
            segments.append(Segment(segment.command.lower(), args))
        return Path(segments), Point(*end)

    def to_absolute(self, start: Point = Point(0, 0)) -> 'Path':
        """
        Convert every segment to an absolute command
        :param start: Pen position before the path
        """
        segments: list[Segment] = []
        for segment, current, _ in self._walk(start):
            if not segment.is_relative:
                segments.append(segment)
                continue
            args = tuple(
                value + current.x if role is Role.X else value + current.y if role is Role.Y else value
                for value, role in zip(segment.args, segment.roles)
            )
            segments.append(Segment(segment.command.upper(), args))
        return Path(segments)

    def map_coordinates(self, fn: Callable[[float, Role], float]) -> 'Path':
        """
        Apply fn to every x / y coordinate (radii, angles and flags are left untouched)
        :param fn: Called with the value and its role (Role.X or Role.Y)
        """
        return Path(
            Segment(segment.command, tuple(
                fn(value, role) if role in (Role.X, Role.Y) else value
                for value, role in zip(segment.args, segment.roles)
            ))
            for segment in self._segments
        )

    def translate(self, dx: float, dy: float) -> 'Path':
        """
        Move absolute coordinates. Relative commands are position independent and are left untouched.
        """
        return Path(
            segment if segment.is_relative else Segment(segment.command, tuple(
                value + dx if role is Role.X else value + dy if role is Role.Y else value
                for value, role in zip(segment.args, segment.roles)
            ))
            for segment in self._segments
        )

    def scale(self, sx: float, sy: float | None = None) -> 'Path':
        """
        Scale the path relative to the origin (uniformly if sy is omitted).
        A mirroring scale (sx * sy < 0) also flips arc sweep flags and angles.
        Arc radii follow the axes, so a rotated arc under a non-uniform scale is only approximated.
        """
        sy = sx if sy is None else sy
        mirrored = sx * sy < 0
        factors = {Role.X: sx, Role.RX: abs(sx), Role.Y: sy, Role.RY: abs(sy)}

        def scale_segment(segment: Segment) -> Segment:
            args = [value * factors.get(role, 1) for value, role in zip(segment.args, segment.roles)]
            if mirrored and segment.command in "Aa":
                args[2] = -args[2]  # Rotation angle
                args[4] = 1 - args[4]  # Sweep flag
            return Segment(segment.command, tuple(args))

        return Path(scale_segment(segment) for segment in self._segments)

    def polylines(self, start: Point = Point(0, 0), steps: int = 16) -> list[list[Point]]:
        """
        Approximate the drawn parts of the path with points, one polyline per subpath.
        Moves are not drawn: a subpath made only of a move gives no polyline.
        :param start: Pen position before the path
        :param steps: Number of points per curve
        """
        polylines: list[list[Point]] = []
        current_line: list[Point] = []
        previous_control: Point | None = None  # Last control point, for S / T reflections
        previous_command = ""

        for segment, current, end in self.to_absolute(start)._walk(start):
            command, args = segment.command, segment.args
            if command == "M":
                if len(current_line) > 1:
                    polylines.append(current_line)
                current_line = [end]
            else:
                if not current_line:
                    current_line = [current]
                if command in "LHVZ":
                    current_line.append(end)
                elif command in "CS":
                    if command == "C":
                        control_1, control_2 = Point(args[0], args[1]), Point(args[2], args[3])
                    else:
                        control_1 = _reflect(previous_control, current) if previous_command in "CS" else current
                        control_2 = Point(args[0], args[1])
                    current_line += flatten.cubic(current, control_1, control_2, end, steps)
                    previous_control = control_2
                elif command in "QT":
                    if command == "Q":
                        control = Point(args[0], args[1])
                    else:
                        control = _reflect(previous_control, current) if previous_command in "QT" else current
                    current_line += flatten.quadratic(current, control, end, steps)
                    previous_control = control
                elif command == "A":
                    current_line += flatten.arc(current, args[0], args[1], args[2], bool(args[3]), bool(args[4]),
                                                end, steps)
                if command == "Z":  # A new subpath starts at the same point
                    polylines.append(current_line)
                    current_line = [end]
            previous_command = command

        if len(current_line) > 1:
            polylines.append(current_line)
        return polylines

    def bounding_box(self, start: Point = Point(0, 0), steps: int = 16) -> BoundingBox | None:
        """
        Bounding box of the drawn parts of the path (moves excluded), None if nothing is drawn
        :param start: Pen position before the path
        :param steps: Number of points per curve used for the approximation
        """
        return BoundingBox.from_points(point for line in self.polylines(start, steps) for point in line)

    def to_svg(self, precision: int | None = 3, separator: str = " ") -> str:
        """
        Export to a string usable in a d="" attribute
        :param precision: Number of decimals (None: full precision)
        :param separator: Put between segments
        """
        return separator.join(segment.to_svg(precision) for segment in self._segments)

    def __iter__(self) -> Iterator[Segment]:
        return iter(self._segments)

    def __len__(self) -> int:
        return len(self._segments)

    def __bool__(self) -> bool:
        return bool(self._segments)

    def __add__(self, other: 'Path') -> 'Path':
        return Path(self._segments + tuple(other))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Path) and self._segments == other._segments

    def __hash__(self) -> int:
        return hash(self._segments)

    def __repr__(self) -> str:
        return f"Path({self.to_svg(None)!r})"


def _tokenize(raw: str, roles: tuple[Role, ...], offset: int) -> list[float]:
    """Read the arguments of a command. Arc flags are single 0/1 chars that may be glued together."""
    values: list[float] = []
    pos = _SEPARATOR_RE.match(raw, 0).end()
    while pos < len(raw):
        role = roles[len(values) % len(roles)] if roles else None
        if role is Role.FLAG:
            if raw[pos] not in "01":
                raise ValueError(f"Expected an arc flag (0 or 1) at {offset + pos}, got {raw[pos]!r}")
            values.append(float(raw[pos]))
            pos += 1
        else:
            number = _NUMBER_RE.match(raw, pos)
            if number is None:
                raise ValueError(f"Unexpected {raw[pos]!r} in path data at {offset + pos}")
            values.append(float(number.group()))
            pos = number.end()
        pos = _SEPARATOR_RE.match(raw, pos).end()
    return values


def _reflect(point: Point | None, center: Point) -> Point:
    """Reflection of point around center (center itself if there is no point)"""
    if point is None:
        return center
    return Point(2 * center.x - point.x, 2 * center.y - point.y)
