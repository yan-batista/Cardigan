from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QMessageBox, QPushButton,
                               QTableWidget, QTableWidgetItem, QVBoxLayout)

from .tags import TAG, color_hex, valid_color


class TagsDialog(QDialog):
    """Edits the tag registry: one row per tag with name, alias and color."""

    def __init__(self, registry, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage tags")
        self.resize(480, 360)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Name", "Alias", "Color"])
        self.table.horizontalHeader().setStretchLastSection(True)
        for t in registry:
            self.add_row(t["name"], t.get("alias", ""), t.get("color", "GRAY"))
        self.table.itemChanged.connect(self.paint)

        add = QPushButton("Add")
        add.clicked.connect(lambda: self.add_row("", "", "GRAY"))
        delete = QPushButton("Delete")
        delete.clicked.connect(lambda: self.table.removeRow(self.table.currentRow()))
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        row = QHBoxLayout()
        row.addWidget(add)
        row.addWidget(delete)
        row.addStretch()
        layout = QVBoxLayout(self)
        layout.addWidget(self.table)
        layout.addLayout(row)
        layout.addWidget(QLabel("Colors: red, orange, yellow, green, blue, purple, pink, gray or #rrggbb.\n"
                                "Renaming or deleting a tag doesn't change your files."))
        layout.addWidget(buttons)

    def add_row(self, name, alias, color):
        r = self.table.rowCount()
        self.table.insertRow(r)
        for c, text in enumerate((name, alias, color)):
            self.table.setItem(r, c, QTableWidgetItem(text))

    def paint(self, item):
        if item.column() == 2:
            self.table.blockSignals(True)  # setBackground fires itemChanged again
            item.setBackground(QColor(color_hex(item.text().strip())))
            self.table.blockSignals(False)

    def cell(self, r, c):
        return self.table.item(r, c).text().strip()

    def registry(self):
        rows = [(self.cell(r, 0), self.cell(r, 1), self.cell(r, 2)) for r in range(self.table.rowCount())]
        return [{"name": n, "alias": a, "color": c} for n, a, c in rows if n or a]

    def accept(self):
        seen = set()
        for t in self.registry():
            problem = None
            if not TAG.fullmatch(f"[{t['name']}]"):
                problem = f"'{t['name']}' isn't a valid tag name (letters, digits, - and _)."
            elif t["alias"] and not TAG.fullmatch(f"[{t['alias']}]"):
                problem = f"'{t['alias']}' isn't a valid alias."
            elif not valid_color(t["color"]):
                problem = f"'{t['color']}' isn't a color for {t['name']}."
            names = {t["name"].lower(), t["alias"].lower()} - {""}
            if not problem and (names & seen or len(names) < len([x for x in (t["name"], t["alias"]) if x])):
                problem = f"{t['name']}: a name or alias is already used."
            if problem:
                QMessageBox.warning(self, "Manage tags", problem)
                return
            seen |= names
        super().accept()
