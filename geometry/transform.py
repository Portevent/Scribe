import math
import re
from dataclasses import dataclass

from geometry.path import Path

_FUNCTION_RE = re.compile(r"\s*([a-zA-Z]+)\s*\(([^)]*)\)\s*,?")
_NUMBER_SPLIT_RE = re.compile(r"[\s,]+")


@dataclass(frozen=True)
class Transform:
    """
    A transform made of an axis aligned scale followed by a translation:
    x' = sx * x + tx, y' = sy * y + ty.
    Rotations and skews are not supported (they would require converting arcs and boxes).
    """
    sx: float = 1.0
    sy: float = 1.0
    tx: float = 0.0
    ty: float = 0.0

    @classmethod
    def parse(cls, attribute: str | None) -> 'Transform':
        """
        Parse an SVG transform attribute: translate, scale and matrix(a,0,0,d,e,f) are supported.
        :raise ValueError: on rotations, skews or malformed data
        """
        result = cls()
        if not attribute or not attribute.strip():
            return result
        position = 0
        text = attribute.strip()
        while position < len(text):
            match = _FUNCTION_RE.match(text, position)
            if match is None:
                raise ValueError(f"Malformed transform {attribute!r}")
            name, raw = match.group(1), match.group(2).strip()
            values = [float(value) for value in _NUMBER_SPLIT_RE.split(raw) if value] if raw else []
            result = result @ cls._from_function(name, values, attribute)
            position = match.end()
        return result

    @classmethod
    def _from_function(cls, name: str, values: list[float], attribute: str) -> 'Transform':
        if name == "translate" and len(values) in (1, 2):
            return cls(tx=values[0], ty=values[1] if len(values) == 2 else 0.0)
        if name == "scale" and len(values) in (1, 2):
            return cls(sx=values[0], sy=values[1] if len(values) == 2 else values[0])
        if name == "matrix" and len(values) == 6:
            a, b, c, d, e, f = values
            if not (math.isclose(b, 0, abs_tol=1e-12) and math.isclose(c, 0, abs_tol=1e-12)):
                raise ValueError(f"Rotated or skewed matrix is not supported: {attribute!r}")
            return cls(a, d, e, f)
        if name in ("rotate", "skewX", "skewY"):
            raise ValueError(f"{name} is not supported in transform {attribute!r}")
        raise ValueError(f"Malformed transform function {name}{tuple(values)} in {attribute!r}")

    def __matmul__(self, other: 'Transform') -> 'Transform':
        """self @ other: apply other first, then self (same order as nested SVG transforms)"""
        return Transform(self.sx * other.sx, self.sy * other.sy,
                         self.sx * other.tx + self.tx, self.sy * other.ty + self.ty)

    def apply(self, path: Path) -> Path:
        """Transform a path (converted to absolute commands first)"""
        return path.to_absolute().scale(self.sx, self.sy).translate(self.tx, self.ty)
