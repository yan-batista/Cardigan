from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCursor, QTextDocument
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLineEdit, QTextEdit, QToolButton, QWidget

MATCH = QColor("#f5d04a")
CURRENT = QColor("#ff9632")


class FindBar(QWidget):
    """Footer search for the editor: finds as you type, optionally highlights every match."""

    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.edit = QLineEdit(placeholderText="Find")
        self.case = QCheckBox("Match case")
        self.all = QCheckBox("Highlight all")
        self.all.setChecked(True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.addWidget(self.edit, 1)
        for text, fn in (("↑", lambda: self.step(backwards=True)), ("↓", self.step)):
            button = QToolButton(text=text)
            button.clicked.connect(fn)
            layout.addWidget(button)
        layout.addWidget(self.case)
        layout.addWidget(self.all)
        close = QToolButton(text="✕")
        close.clicked.connect(self.close_bar)
        layout.addWidget(close)

        self.edit.textChanged.connect(self.on_text)
        self.edit.returnPressed.connect(self.step)
        self.case.toggled.connect(self.on_text)
        self.all.toggled.connect(self.highlight)
        editor.textChanged.connect(self.highlight)
        self.hide()

    def flags(self):
        return QTextDocument.FindCaseSensitively if self.case.isChecked() else QTextDocument.FindFlag(0)

    def open(self):
        self.show()
        self.edit.setFocus()
        self.edit.selectAll()
        self.highlight()

    def close_bar(self):
        self.hide()
        self.highlight()
        self.editor.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close_bar()
        else:
            super().keyPressEvent(event)

    def on_text(self):
        cursor = self.editor.textCursor()
        cursor.setPosition(min(cursor.anchor(), cursor.position()))  # keep the current match while typing
        self.editor.setTextCursor(cursor)
        self.step()

    def step(self, backwards=False):
        text = self.edit.text()
        if text:
            flags = self.flags() | (QTextDocument.FindBackward if backwards else QTextDocument.FindFlag(0))
            if not self.editor.find(text, flags):  # wrap around
                self.editor.moveCursor(QTextCursor.End if backwards else QTextCursor.Start)
                self.editor.find(text, flags)
        self.highlight()

    def highlight(self):
        text = self.edit.text()
        selections = []
        if self.isVisible() and text:
            current = self.editor.textCursor()
            cursor = self.editor.document().find(text, 0, self.flags())
            while not cursor.isNull() and self.all.isChecked():
                selections.append(self.selection(cursor, MATCH))
                cursor = self.editor.document().find(text, cursor, self.flags())
            if current.hasSelection():
                selections.append(self.selection(current, CURRENT))
        self.editor.setExtraSelections(selections)

    @staticmethod
    def selection(cursor, color):
        sel = QTextEdit.ExtraSelection()
        sel.cursor = cursor
        sel.format.setBackground(color)
        sel.format.setForeground(Qt.black)
        return sel
