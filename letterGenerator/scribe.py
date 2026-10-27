import random

from letterGenerator import LetterGenerator


class Scribe:
    """
    Memorize letterGenerator by letters, so they can be retrieves when asked a certain letter
    """

    def __init__(self):
        self.letters: dict = {}

    def add_letter(self, letter: str, letterGenerator: LetterGenerator):
        """
        Memorize new letter
        :param letter: letter
        :param letterGenerator: Generator
        """

        if letter not in self.letters:
            self.letters[letter] = []
        self.letters[letter].append(letterGenerator)

    def get_letter(self, letter: str) -> LetterGenerator:
        """
        Get a letter Generator
        :param letter: letter
        :return: Letter Generator
        """
        if letter not in self.letters:
            raise Exception(f'{letter} is not a known letter in Scribe')
        return self.letters[letter][random.randrange(0, len(self.letters[letter]))]
