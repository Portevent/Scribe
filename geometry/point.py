from typing import NamedTuple


class Point(NamedTuple):
    x: float
    y: float

    def __add__(self, other: 'Point') -> 'Point':
        return Point(self.x + other[0], self.y + other[1])

    def __sub__(self, other: 'Point') -> 'Point':
        return Point(self.x - other[0], self.y - other[1])
