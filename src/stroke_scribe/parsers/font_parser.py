from abc import ABC, abstractmethod
from os import PathLike
from typing import IO

from stroke_scribe.font import Font

FontSource = str | PathLike | IO


class FontParser(ABC):
    """Build a Font from a source (file, folder, project...)"""

    @abstractmethod
    def parse(self, source: FontSource) -> Font:
        """
        Read the source and return the font it describes
        :raise ValueError: if the source is malformed
        """
