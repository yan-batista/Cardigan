from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QPainter, QPolygon
from PySide6.QtWidgets import QWidget

from ..theme import mix


class Gutter(QWidget):
    """The line number strip on the left of the editor."""

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.collapsed = set()  # ordinals of the folded headings
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

    def headings(self):
        block, found = self.editor.document().begin(), []
        while block.isValid():
            if self.level(block):
                found.append(block)
            block = block.next()
        return found

    def body(self, head):
        """The lines a fold of this heading hides: up to the next heading of the same or higher level, minus trailing blank lines."""
        level, body, block = self.level(head), [], head.next()
        while block.isValid() and not 0 < self.level(block) <= level:
            body.append(block)
            block = block.next()
        while body and not body[-1].text().strip():  # trailing blank lines belong to no fold
            body.pop()
        return body

    def ordinal(self, head):
        return sum(1 for h in self.headings() if h.position() < head.position())

    def folded(self, block):
        return self.level(block) > 0 and self.ordinal(block) in self.collapsed and bool(self.body(block))

    def toggle_fold(self, block):
        self.collapsed ^= {self.ordinal(block)}
        self.apply()
        cursor = self.editor.textCursor()  # keep the cursor out of the hidden lines
        while not cursor.block().isVisible():
            cursor.movePosition(cursor.MoveOperation.PreviousBlock)
        self.editor.setTextCursor(cursor)

    def reveal(self, block):
        """Unfolds just the headings that enclose this block."""
        if block.isVisible():
            return
        stack = []  # the headings above the block, nearest of each level
        for head in self.headings():
            if head.position() > block.position():
                break
            stack = [h for h in stack if self.level(h) < self.level(head)] + [head]
        for head in stack:
            self.collapsed.discard(self.ordinal(head))
        self.apply()

    def apply(self):
        """Shows every line, then hides the body of each collapsed heading."""
        doc = self.editor.document()
        block = doc.begin()
        while block.isValid():
            block.setVisible(True)
            block = block.next()
        for number, head in enumerate(self.headings()):
            if number in self.collapsed:
                for line in self.body(head):
                    line.setVisible(False)
        doc.markContentsDirty(0, doc.characterCount())
        self.editor.viewport().update()
        self.update()

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
