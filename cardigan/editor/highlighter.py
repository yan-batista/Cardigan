from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat

from ..theme import COLUMN_COLOR, PROJECT_COLOR


class Highlighter(QSyntaxHighlighter):
    """Colors the "# project" and "## column" lines."""

    def __init__(self, document, dark):
        super().__init__(document)
        self.project = self.make_format(PROJECT_COLOR[dark])
        self.column = self.make_format(COLUMN_COLOR[dark])

    @staticmethod
    def make_format(color):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        fmt.setFontWeight(QFont.Bold)
        return fmt

    def highlightBlock(self, text):
        if text.startswith("## "):
            self.setFormat(0, len(text), self.column)
        elif text.startswith("# "):
            self.setFormat(0, len(text), self.project)
