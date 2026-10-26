from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPalette
from PySide6.QtWidgets import (QLabel, QListWidget, QListWidgetItem, QStyle, QStyledItemDelegate,
                               QVBoxLayout, QWidget)

from .theme import mix


class ProjectDelegate(QStyledItemDelegate):
    """Draws a project row as a name with its card count on the right."""

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 34)

    def paint(self, painter, option, index):
        pal = option.palette
        text, window, accent = pal.text().color(), pal.window().color(), pal.highlight().color()
        selected = bool(option.state & QStyle.State_Selected)
        hovered = bool(option.state & QStyle.State_MouseOver)
        rect = option.rect.adjusted(8, 2, -8, -2)
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        if selected or hovered:
            fill = QColor(accent if selected else text)
            fill.setAlphaF(0.20 if selected else 0.07)
            painter.setBrush(fill)
            painter.drawRoundedRect(rect, 6, 6)
        if selected:
            painter.setBrush(accent)
            painter.drawRoundedRect(QRect(rect.left(), rect.top() + 7, 3, rect.height() - 14), 1.5, 1.5)
        count = str(index.data(Qt.UserRole))
        count_width = option.fontMetrics.horizontalAdvance(count)
        name_rect = rect.adjusted(14, 0, -(count_width + 22), 0)
        painter.setPen(text)
        painter.drawText(name_rect, Qt.AlignVCenter | Qt.AlignLeft,
                         option.fontMetrics.elidedText(index.data(Qt.DisplayRole), Qt.ElideRight, name_rect.width()))
        painter.setPen(mix(text, window, 0.45))
        painter.drawText(rect.adjusted(0, 0, -10, 0), Qt.AlignVCenter | Qt.AlignRight, count)
        painter.restore()


class Sidebar(QWidget):
    """Panel listing the projects. The first row is "All projects"."""

    project_selected = Signal(int)  # index into the projects, -1 for all of them

    def __init__(self):
        super().__init__()
        self.setMinimumWidth(170)
        self.setMaximumWidth(360)
        self.setAutoFillBackground(True)
        pal = self.palette()

        header = QLabel("PROJECTS")
        font = header.font()
        font.setPointSizeF(font.pointSizeF() * 0.8)
        font.setBold(True)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 1.2)
        header.setFont(font)
        header_pal = header.palette()
        header_pal.setColor(QPalette.WindowText, mix(pal.text().color(), pal.window().color(), 0.45))
        header.setPalette(header_pal)
        header.setContentsMargins(18, 16, 18, 8)

        self.list = QListWidget()
        self.list.setFrameShape(QListWidget.NoFrame)
        self.list.setMouseTracking(True)
        self.list.setItemDelegate(ProjectDelegate(self.list))
        self.list.viewport().setBackgroundRole(QPalette.Window)
        self.list.currentRowChanged.connect(self.on_row_changed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(0)
        layout.addWidget(header)
        layout.addWidget(self.list)

    def on_row_changed(self, row):
        if row >= 0:
            self.project_selected.emit(row - 1)

    def set_projects(self, projects, selected):
        """Refills the list without emitting project_selected."""
        counts = [sum(len(cards) for _, cards in columns) for _, columns, _ in projects]
        rows = [("All projects", sum(counts))]
        rows += [(name or "(untitled)", count) for (name, _, _), count in zip(projects, counts)]
        self.list.blockSignals(True)
        self.list.clear()
        for name, count in rows:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, count)
            self.list.addItem(item)
        self.list.setCurrentRow(selected + 1)
        self.list.blockSignals(False)
