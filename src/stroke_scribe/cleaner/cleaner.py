class Cleaner:

    def clean(self, string: str) -> str:
        return "Not implemented"


class FormatterCleaner(Cleaner):

    def clean(self, string: str) -> str:
        # print(f"Cleaning out {string=}")
        out_string = string.replace("\n", "").replace("	", '').replace(">", ">\n").replace("</", "\n</").replace("\n\n", "\n")

        return out_string


class FileCleaner:
    """
    Simple Class that handle a task to operate :
    take given file, read it,
    clean it with given cleaner,
    write to given file
    """
    _file: str
    _exportFile: str
    _cleaner: Cleaner

    def __init__(self, filePath: str, filePathOut: str, cleaner: Cleaner):
        self._file = filePath
        self._exportFile = filePathOut
        self._cleaner = cleaner

    def export(self):
        print(f"Exporting {self._file} to {self._exportFile}")
        with open(self._file, "r") as inFile:
            with open(self._exportFile, "w") as outFile:
                outFile.write(self._cleaner.clean(inFile.read()))

