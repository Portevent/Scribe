import random

from font.character import Character


class MissingCharacterError(KeyError):
    """Raised when a font has no glyph for a requested character."""


class Font:
    """
    A collection of characters, each one possibly having several variants.
    Loading characters from assets is the job of dedicated parsers.
    """

    def __init__(self, name: str = ""):
        self.name = name
        self._characters: dict[str, list[Character]] = {}

    def add(self, character: Character) -> None:
        """
        Register a character (as a new variant if the char is already known)
        """
        self._characters.setdefault(character.char, []).append(character)

    def get(self, char: str, rng: random.Random | None = None) -> Character:
        """
        Pick one variant of the requested character
        :param char: The character to get
        :param rng: Random generator used to pick the variant (module random by default)
        :raise MissingCharacterError: if the font has no glyph for char
        """
        variants = self.variants(char)
        return (rng or random).choice(variants)

    def variants(self, char: str) -> list[Character]:
        """
        All variants of the requested character
        :raise MissingCharacterError: if the font has no glyph for char
        """
        if char not in self._characters:
            raise MissingCharacterError(char)
        return list(self._characters[char])

    @property
    def chars(self) -> set[str]:
        return set(self._characters)

    def __contains__(self, char: str) -> bool:
        return char in self._characters

    def __len__(self) -> int:
        return len(self._characters)
