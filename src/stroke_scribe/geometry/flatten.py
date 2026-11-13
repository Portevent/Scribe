"""
Approximate path segments with points, e.g. to compute bounding boxes.
Every function takes absolute coordinates.
"""
import math

from stroke_scribe.geometry.point import Point


def cubic(p0: Point, p1: Point, p2: Point, p3: Point, steps: int) -> list[Point]:
    """Points of a cubic Bézier curve, p0 excluded"""
    points = []
    for i in range(1, steps + 1):
        t = i / steps
        u = 1 - t
        points.append(Point(
            u ** 3 * p0.x + 3 * u * u * t * p1.x + 3 * u * t * t * p2.x + t ** 3 * p3.x,
            u ** 3 * p0.y + 3 * u * u * t * p1.y + 3 * u * t * t * p2.y + t ** 3 * p3.y,
        ))
    return points


def quadratic(p0: Point, p1: Point, p2: Point, steps: int) -> list[Point]:
    """Points of a quadratic Bézier curve, p0 excluded"""
    points = []
    for i in range(1, steps + 1):
        t = i / steps
        u = 1 - t
        points.append(Point(
            u * u * p0.x + 2 * u * t * p1.x + t * t * p2.x,
            u * u * p0.y + 2 * u * t * p1.y + t * t * p2.y,
        ))
    return points


def arc(start: Point, rx: float, ry: float, angle: float, large_arc: bool, sweep: bool, end: Point,
        steps: int) -> list[Point]:
    """
    Points of an elliptical arc, start excluded.
    Endpoint to centre parameterisation from https://www.w3.org/TR/SVG11/implnote.html#ArcImplementationNotes
    """
    rx, ry = abs(rx), abs(ry)
    if rx == 0 or ry == 0 or start == end:
        return [end]

    phi = math.radians(angle)
    cos_phi, sin_phi = math.cos(phi), math.sin(phi)
    dx, dy = (start.x - end.x) / 2, (start.y - end.y) / 2
    x1 = cos_phi * dx + sin_phi * dy
    y1 = -sin_phi * dx + cos_phi * dy

    # Radii too small to reach the end point are scaled up
    radii_ratio = x1 ** 2 / rx ** 2 + y1 ** 2 / ry ** 2
    if radii_ratio > 1:
        rx, ry = rx * math.sqrt(radii_ratio), ry * math.sqrt(radii_ratio)

    numerator = rx ** 2 * ry ** 2 - rx ** 2 * y1 ** 2 - ry ** 2 * x1 ** 2
    denominator = rx ** 2 * y1 ** 2 + ry ** 2 * x1 ** 2
    coefficient = math.sqrt(max(0.0, numerator / denominator))
    if large_arc == sweep:
        coefficient = -coefficient
    cx1 = coefficient * rx * y1 / ry
    cy1 = -coefficient * ry * x1 / rx
    cx = cos_phi * cx1 - sin_phi * cy1 + (start.x + end.x) / 2
    cy = sin_phi * cx1 + cos_phi * cy1 + (start.y + end.y) / 2

    theta = _angle(1, 0, (x1 - cx1) / rx, (y1 - cy1) / ry)
    delta = _angle((x1 - cx1) / rx, (y1 - cy1) / ry, (-x1 - cx1) / rx, (-y1 - cy1) / ry)
    if not sweep and delta > 0:
        delta -= 2 * math.pi
    elif sweep and delta < 0:
        delta += 2 * math.pi

    points = []
    for i in range(1, steps + 1):
        t = theta + delta * i / steps
        points.append(Point(
            cx + rx * cos_phi * math.cos(t) - ry * sin_phi * math.sin(t),
            cy + rx * sin_phi * math.cos(t) + ry * cos_phi * math.sin(t),
        ))
    points[-1] = end  # Avoid rounding drift on the end point
    return points


def _angle(ux: float, uy: float, vx: float, vy: float) -> float:
    """Signed angle from vector u to vector v"""
    return math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
