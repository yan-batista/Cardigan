from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QPlainTextEdit

from .gutter import Gutter
from .highlighter import Highlighter
from .shortcuts import handle_key


class Editor(QPlainTextEdit):
    """Plain text editor with line numbers, heading colors and VS Code style line shortcuts."""

    find_requested = Signal()

    def __init__(self):
        super().__init__()
        font = QFont("monospace")
        font.setStyleHint(QFont.Monospace)
        font.setPointSize(11)
        self.setFont(font)
        self.setTabStopDistance(32)
        self.highlighter = Highlighter(self.document(), self.palette().base().color().lightness() < 128)
        self.gutter = Gutter(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.gutter.reposition()

    def keyPressEvent(self, event):
        if not handle_key(self, event):
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:  # the default is to zoom
            event.ignore()
        else:
            super().wheelEvent(event)
