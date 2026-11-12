from dataclasses import dataclass
from typing import Iterable

from geometry.point import Point


@dataclass(frozen=True)
class BoundingBox:
    """Axis aligned rectangle (y grows downwards, as in SVG)"""
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @classmethod
    def from_points(cls, points: Iterable[Point]) -> 'BoundingBox | None':
        """Smallest box containing every point, None if there is no point"""
        points = list(points)
        if not points:
            return None
        xs = [point.x for point in points]
        ys = [point.y for point in points]
        return cls(min(xs), min(ys), max(xs), max(ys))

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y

    def union(self, other: 'BoundingBox') -> 'BoundingBox':
        return BoundingBox(min(self.min_x, other.min_x), min(self.min_y, other.min_y),
                           max(self.max_x, other.max_x), max(self.max_y, other.max_y))

    def vertical_overlap(self, other: 'BoundingBox') -> float:
        """Height of the horizontal band shared by both boxes (0 if they don't overlap vertically)"""
        return max(0.0, min(self.max_y, other.max_y) - max(self.min_y, other.min_y))
