from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat

from ..tags import TAG
from ..theme import COLUMN_COLOR, PROJECT_COLOR, TAG_COLOR


class Highlighter(QSyntaxHighlighter):
    """Colors the "# project" and "## column" lines, and the tags on card titles."""

    def __init__(self, document, dark):
        super().__init__(document)
        self.project = self.make_format(PROJECT_COLOR[dark])
        self.column = self.make_format(COLUMN_COLOR[dark])
        self.tag = QTextCharFormat()
        self.tag.setForeground(QColor(TAG_COLOR[dark]))

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
        elif text and not text[0].isspace():  # shortcut: indented card titles aren't highlighted, track the column base indent if it matters
            for m in TAG.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), self.tag)
