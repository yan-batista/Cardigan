from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QPainter, QPolygon
from PySide6.QtWidgets import QWidget

from ..theme import mix


class Gutter(QWidget):
    """The line number strip on the left of the editor."""

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.hover = -1  # block number under the mouse
        self.setMouseTracking(True)
        editor.blockCountChanged.connect(self.update_width)
        editor.updateRequest.connect(self.follow_editor)
        editor.cursorPositionChanged.connect(self.update)
        self.update_width()

    def desired_width(self):
        digits = max(2, len(str(self.editor.blockCount())))
        return 34 + self.editor.fontMetrics().horizontalAdvance("9") * digits

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

    @staticmethod
    def level(block):
        text = block.text()
        return 1 if text.startswith("# ") else 2 if text.startswith("## ") else 0

    def folded(self, block):
        return self.level(block) > 0 and block.next().isValid() and not block.next().isVisible()

    def toggle_fold(self, block):
        level, hide = self.level(block), not self.folded(block)
        block = block.next()
        body = []
        while block.isValid() and not 0 < self.level(block) <= level:
            body.append(block)
            block = block.next()
        while body and not body[-1].text().strip():  # trailing blank lines belong to no fold
            body.pop()
        for block in body:
            block.setVisible(not hide)
        doc = self.editor.document()
        doc.markContentsDirty(0, doc.characterCount())
        self.editor.viewport().update()
        self.update()
        cursor = self.editor.textCursor()  # keep the cursor out of the hidden lines
        if hide and not cursor.block().isVisible():
            while not cursor.block().isVisible():
                cursor.movePosition(cursor.MoveOperation.PreviousBlock)
            self.editor.setTextCursor(cursor)

    def block_at(self, y):
        return self.editor.cursorForPosition(QPoint(0, y)).block()

    def mouseMoveEvent(self, event):
        number = self.block_at(event.position().toPoint().y()).blockNumber()
        if number != self.hover:
            self.hover = number
            self.update()

    def leaveEvent(self, event):
        self.hover = -1
        self.update()

    def mousePressEvent(self, event):
        block = self.block_at(event.position().toPoint().y())
        if event.button() == Qt.LeftButton and self.level(block) and block.next().isValid():
            self.toggle_fold(block)

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
                painter.drawText(0, top, self.width() - 24, editor.fontMetrics().height(),
                                 Qt.AlignRight, str(number + 1))
                if self.level(block) and (number == self.hover or self.folded(block)):
                    self.draw_arrow(painter, top, bright if number == self.hover else dim, self.folded(block))
            block = block.next()
            top = bottom
            bottom = top + round(editor.blockBoundingRect(block).height())
            number += 1

    def draw_arrow(self, painter, top, color, folded):
        """A chevron pointing right when folded, down when open."""
        cx, cy = self.width() - 12, top + self.editor.fontMetrics().height() // 2
        points = [(-2, -4), (2, 0), (-2, 4)] if folded else [(-4, -2), (0, 2), (4, -2)]
        painter.save()
        painter.setPen(color)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPolyline(QPolygon([QPoint(cx + x, cy + y) for x, y in points]))
        painter.restore()
