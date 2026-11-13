import re
import statistics
import warnings
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from os import PathLike, fspath
from pathlib import Path as FilePath

from stroke_scribe.font import Character, Font
from stroke_scribe.geometry import BoundingBox, Path, Point, Transform
from stroke_scribe.parsers.font_parser import FontParser, FontSource

SVG_NS = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
LABEL = f"{{{INKSCAPE_NS}}}label"
GROUP_MODE = f"{{{INKSCAPE_NS}}}groupmode"

# Elements that never contain glyphs
IGNORED_TAGS = {"defs", "namedview", "metadata", "text", "title", "desc", "style", "script",
                "clipPath", "mask", "symbol", "marker", "pattern", "linearGradient", "radialGradient"}
# Shapes Inkscape can convert with "Path > Object to Path"
UNSUPPORTED_SHAPES = {"rect", "circle", "ellipse", "line", "polyline", "polygon", "use", "image"}

UNIT_TO_MM = {"mm": 1.0, "cm": 10.0, "q": 0.25, "in": 25.4, "pt": 25.4 / 72, "pc": 25.4 / 6, "px": 25.4 / 96, "": 25.4 / 96}
_LENGTH_RE = re.compile(r"\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)\s*([a-zA-Z]*)\s*$")

ROW_OVERLAP_RATIO = 0.5  # Glyphs sharing more than this ratio of the smaller height are on the same row
BASELINE_TOLERANCE_RATIO = 0.05
DEFAULT_SPACING_RATIO = 0.1  # Default letter spacing, relative to the median glyph height of a row  # Bottoms closer than this ratio of the row height are on the same line


@dataclass
class _RawGlyph:
    """A labelled object found in the document, before its metrics are known"""
    char: str
    variant: str | None
    path: Path
    box: BoundingBox


class InkscapeParser(FontParser):
    """
    Read a font drawn in an Inkscape SVG file. Every glyph is an object labelled with its character
    (Object properties > Label, stored as inkscape:label).

    Assumptions:
    - A glyph is a labelled <path>, or a labelled group (not a layer) whose paths are merged.
      Several objects with the same label are variants of the character (variant name = element id).
      Labels must be a single character; other labels are skipped with a warning.
    - Layers, the root <svg>, <defs>, <text>... are not glyphs. Unlabelled objects outside glyphs are ignored.
    - Glyphs are laid out in rows. Glyphs whose vertical extents overlap by more than half of the smaller
      height are on the same row.
    - The baseline of a row is the most common bottom of its glyphs (round overshoots are tolerated,
      descenders are outvoted).
    - A glyph starts at (left of its bounding box, baseline) and advances by its width + letter_spacing.
      By default letter_spacing is DEFAULT_SPACING_RATIO x the median glyph height of the row.
    - Output coordinates are in millimetres (from the document width / viewBox), multiplied by scale.
    - Transforms are supported if they only scale and translate.
    """

    def __init__(self, letter_spacing: float | None = None, scale: float = 1.0, curve_steps: int = 16):
        """
        :param letter_spacing: Natural space after each glyph, in millimetres (None: proportional to the row height)
        :param scale: Multiplies output coordinates (e.g. 10 to work in tenths of millimetres)
        :param curve_steps: Precision of the curve approximation used for bounding boxes
        """
        self.letter_spacing = letter_spacing
        self.scale = scale
        self.curve_steps = curve_steps

    def parse(self, source: FontSource) -> Font:
        root = ElementTree.parse(source).getroot()
        if _local_name(root.tag) != "svg":
            raise ValueError(f"Not an SVG document (root element is {root.tag!r})")

        unit = _user_unit_in_mm(root) * self.scale
        glyphs: list[_RawGlyph] = []
        self._collect(root, Transform(unit, unit), glyphs)

        font = Font(FilePath(fspath(source)).stem if isinstance(source, (str, PathLike)) else "")
        for row in _rows(glyphs):
            baseline = _baseline(row)
            if self.letter_spacing is None:
                spacing = DEFAULT_SPACING_RATIO * statistics.median(glyph.box.height for glyph in row)
            else:
                spacing = self.letter_spacing * self.scale
            for glyph in row:
                origin = Point(glyph.box.min_x, baseline)
                exit_point = Point(glyph.box.max_x + spacing, baseline)
                font.add(Character.from_path(glyph.char, glyph.path, glyph.variant, origin, exit_point))
        return font

    def _collect(self, element: ElementTree.Element, transform: Transform, glyphs: list[_RawGlyph]):
        """Walk the document and collect every labelled glyph"""
        for child in element:
            tag = _local_name(child.tag)
            if tag in IGNORED_TAGS or not isinstance(child.tag, str):
                continue
            child_transform = transform @ _transform_of(child)
            label = child.get(LABEL)
            is_layer = tag == "g" and child.get(GROUP_MODE) == "layer"

            if label is not None and tag in ("path", "g") and not is_layer:
                char = label.strip()
                if len(char) != 1:
                    warnings.warn(f"Skipping {_describe(child)}: label {label!r} is not a single character")
                    continue
                path = self._glyph_path(child, child_transform)
                box = path.bounding_box(steps=self.curve_steps)
                if box is None:
                    warnings.warn(f"Skipping {_describe(child)}: nothing is drawn")
                    continue
                glyphs.append(_RawGlyph(char, child.get("id"), path, box))
            elif tag in ("g", "svg"):
                self._collect(child, child_transform, glyphs)

    def _glyph_path(self, element: ElementTree.Element, transform: Transform) -> Path:
        """Absolute path of a glyph element, in output coordinates"""
        tag = _local_name(element.tag)
        if tag == "path":
            try:
                return transform.apply(Path.parse(element.get("d", "")))
            except ValueError as error:
                raise ValueError(f"Invalid path data in {_describe(element)}: {error}") from error
        if tag in UNSUPPORTED_SHAPES:
            raise ValueError(f"{_describe(element)} is a <{tag}>: convert it with Path > Object to Path in Inkscape")

        path = Path()
        if tag in ("g", "svg"):
            for child in element:
                if isinstance(child.tag, str) and _local_name(child.tag) not in IGNORED_TAGS:
                    path = path + self._glyph_path(child, transform @ _transform_of(child))
        return path


def _local_name(tag) -> str:
    """Tag name without its namespace"""
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _describe(element: ElementTree.Element) -> str:
    return f"<{_local_name(element.tag)} id={element.get('id')!r}>"


def _transform_of(element: ElementTree.Element) -> Transform:
    try:
        return Transform.parse(element.get("transform"))
    except ValueError as error:
        raise ValueError(f"{_describe(element)}: {error}") from error


def _length_in_mm(value: str | None) -> float | None:
    if value is None:
        return None
    match = _LENGTH_RE.match(value)
    if match is None or match.group(2).lower() not in UNIT_TO_MM:
        raise ValueError(f"Unsupported document length {value!r}")
    return float(match.group(1)) * UNIT_TO_MM[match.group(2).lower()]


def _user_unit_in_mm(root: ElementTree.Element) -> float:
    """Size of one user unit (the unit of path coordinates) in millimetres"""
    width = _length_in_mm(root.get("width"))
    view_box = root.get("viewBox")
    if width is None or view_box is None:
        return UNIT_TO_MM["px"]
    view_box_width = float(re.split(r"[\s,]+", view_box.strip())[2])
    return width / view_box_width


def _rows(glyphs: list[_RawGlyph]) -> list[list[_RawGlyph]]:
    """Group glyphs drawn on the same line"""
    rows: list[tuple[BoundingBox, list[_RawGlyph]]] = []
    for glyph in sorted(glyphs, key=lambda g: (g.box.min_y + g.box.max_y) / 2):
        for index, (row_box, members) in enumerate(rows):
            smaller_height = min(row_box.height, glyph.box.height)
            if row_box.vertical_overlap(glyph.box) > ROW_OVERLAP_RATIO * smaller_height:
                members.append(glyph)
                rows[index] = (row_box.union(glyph.box), members)
                break
        else:
            rows.append((glyph.box, [glyph]))
    return [members for _, members in rows]


def _baseline(row: list[_RawGlyph]) -> float:
    """Most common bottom of the glyphs of a row"""
    row_height = max(g.box.max_y for g in row) - min(g.box.min_y for g in row)
    tolerance = BASELINE_TOLERANCE_RATIO * row_height
    clusters: list[list[float]] = []
    for bottom in sorted(g.box.max_y for g in row):
        if clusters and bottom - clusters[-1][0] <= tolerance:
            clusters[-1].append(bottom)
        else:
            clusters.append([bottom])
    # Largest cluster wins; on a tie, the highest one (descenders go below the baseline)
    best = max(clusters, key=lambda cluster: (len(cluster), -cluster[0]))
    return statistics.median(best)
