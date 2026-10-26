from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget

from ..theme import mix


class Gutter(QWidget):
    """The line number strip on the left of the editor."""

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        editor.blockCountChanged.connect(self.update_width)
        editor.updateRequest.connect(self.follow_editor)
        editor.cursorPositionChanged.connect(self.update)
        self.update_width()

    def desired_width(self):
        digits = max(2, len(str(self.editor.blockCount())))
        return 20 + self.editor.fontMetrics().horizontalAdvance("9") * digits

    def sizeHint(self):
        return QSize(self.desired_width(), 0)

    def update_width(self):
        self.editor.setViewportMargins(self.desired_width(), 0, 0, 0)

    def follow_editor(self, rect, dy):
        if dy:
            self.scroll(0, dy)
        else:
            self.update(0, rect.y(), self.width(), rect.height())
        if rect.contains(self.editor.viewport().rect()):
            self.update_width()

    def reposition(self):
        area = self.editor.contentsRect()
        self.setGeometry(QRect(area.left(), area.top(), self.desired_width(), area.height()))

    def paintEvent(self, event):
        editor = self.editor
        base, text = editor.palette().base().color(), editor.palette().text().color()
        painter = QPainter(self)
        painter.fillRect(event.rect(), mix(base, text, 0.05))
        dim, bright = mix(text, base, 0.55), text
        current = editor.textCursor().blockNumber()
        block = editor.firstVisibleBlock()
        number = block.blockNumber()
        top = round(editor.blockBoundingGeometry(block).translated(editor.contentOffset()).top())
        bottom = top + round(editor.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(bright if number == current else dim)
                painter.drawText(0, top, self.width() - 10, editor.fontMetrics().height(),
                                 Qt.AlignRight, str(number + 1))
            block = block.next()
            top = bottom
            bottom = top + round(editor.blockBoundingRect(block).height())
            number += 1
