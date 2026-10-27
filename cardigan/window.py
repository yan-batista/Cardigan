from pathlib import Path

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtGui import QAction, QKeySequence, QTextCursor
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QSplitter, QStackedWidget, QVBoxLayout, QWidget

from .editor import Editor
from .editor.findbar import FindBar
from .parser import parse
from .renderer import render
from .sidebar import Sidebar
from . import tags
from .tagsdialog import TagsDialog


class Window(QMainWindow):
    def __init__(self, path):
        super().__init__()
        self.settings = QSettings("cardigan", "cardigan")
        self.path = None
        self.projects = []
        self.registry = tags.load()
        self.selected = -1  # index into self.projects, -1 shows all of them

        self.editor = Editor()
        self.view = QWebEngineView()
        self.stack = QStackedWidget()
        self.stack.addWidget(self.editor)
        self.stack.addWidget(self.view)
        self.findbar = FindBar(self.editor)
        self.editor.find_requested.connect(self.findbar.open)
        main = QWidget()
        column = QVBoxLayout(main)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        column.addWidget(self.stack)
        column.addWidget(self.findbar)
        self.sidebar = Sidebar()

        splitter = QSplitter()
        splitter.addWidget(self.sidebar)
        splitter.addWidget(main)
        splitter.setSizes([220, 880])
        splitter.setStretchFactor(1, 1)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(1)
        self.setCentralWidget(splitter)
        self.resize(1100, 750)

        self.refresh_timer = QTimer(self, singleShot=True, interval=250)
        self.refresh_timer.timeout.connect(self.refresh_sidebar)
        self.editor.textChanged.connect(self.refresh_timer.start)
        self.editor.document().modificationChanged.connect(self.update_title)
        self.sidebar.project_selected.connect(self.select)
        self.build_menus()

        last = self.settings.value("lastFile", "")
        target = path or (Path(last) if last else None)
        if not (target and target.exists() and self.load(target)):
            self.refresh_sidebar()
            self.update_title()

    def build_menus(self):
        def add(menu, text, keys, fn, checkable=False):
            act = QAction(text, self, checkable=checkable)
            if keys:
                act.setShortcut(QKeySequence(keys))
            # PySide drops the checked flag when `triggered` goes to a built-in slot, so use `toggled`
            (act.toggled if checkable else act.triggered).connect(fn)
            menu.addAction(act)
            return act

        file_menu = self.menuBar().addMenu("File")
        add(file_menu, "&New", "Ctrl+N", self.new)
        add(file_menu, "&Open...", "Ctrl+O", self.open)
        self.recent_menu = file_menu.addMenu("Open &Recent")
        self.recent_menu.aboutToShow.connect(self.fill_recent)
        file_menu.addSeparator()
        add(file_menu, "&Save", "Ctrl+S", self.save)
        add(file_menu, "Save &As...", "Ctrl+Shift+S", self.save_as)
        file_menu.addSeparator()
        add(file_menu, "&Quit", "Ctrl+Q", self.close)

        view_menu = self.menuBar().addMenu("View")
        add(view_menu, "&Board / Editor", "Ctrl+M", self.toggle)
        side = add(view_menu, "&Sidebar", "Ctrl+B", self.sidebar.setVisible, checkable=True)
        side.setChecked(True)

        add(self.menuBar().addMenu("Tags"), "&Manage tags...", "", self.manage_tags)

    def manage_tags(self):
        dialog = TagsDialog(self.registry, self)
        if dialog.exec():
            self.registry = dialog.registry()
            try:
                tags.save(self.registry)
            except OSError as err:
                QMessageBox.warning(self, "Save failed", f"{tags.PATH}\n\n{err}")
            if self.in_board():
                self.show_board()

    def fill_recent(self):
        self.recent_menu.clear()
        recent = [r for r in self.settings.value("recent", "").split("\n") if r]
        for name in recent:
            act = self.recent_menu.addAction(name)
            act.triggered.connect(lambda _=False, p=Path(name): self.open_path(p))
        self.recent_menu.setEnabled(bool(recent))

    def in_board(self):
        return self.stack.currentWidget() is self.view

    def update_title(self):
        star = "*" if self.editor.document().isModified() else ""
        self.setWindowTitle(f"{self.path.name if self.path else 'untitled'}{star} - Cardigan")

    def refresh_sidebar(self):
        self.projects = parse(self.editor.toPlainText())
        if self.selected >= len(self.projects):
            self.selected = -1
        self.sidebar.set_projects(self.projects, self.selected)

    def select(self, index):
        self.selected = index
        if self.in_board():
            self.show_board()
        elif index >= 0:
            block = self.editor.document().findBlockByNumber(self.projects[index][2])
            self.editor.setTextCursor(QTextCursor(block))
            self.editor.centerCursor()
            self.editor.setFocus()

    def show_board(self):
        shown = self.projects if self.selected < 0 else [self.projects[self.selected]]
        self.view.setHtml(render(shown, self.registry))

    def toggle(self):
        if self.in_board():
            self.stack.setCurrentWidget(self.editor)
            self.editor.setFocus()
        else:
            self.refresh_sidebar()
            self.show_board()
            self.stack.setCurrentWidget(self.view)
            self.view.setFocus()
        self.update_title()

    def confirm_discard(self):
        if not self.editor.document().isModified():
            return True
        answer = QMessageBox.question(
            self, "Unsaved changes", f"Save changes to {self.path.name if self.path else 'untitled'}?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        if answer == QMessageBox.Save:
            return self.save()
        return answer == QMessageBox.Discard

    def load(self, path):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as err:
            QMessageBox.warning(self, "Open failed", f"{path}\n\n{err}")
            return False
        self.path = path
        self.editor.setPlainText(text)
        self.editor.document().setModified(False)
        self.selected = -1
        self.refresh_sidebar()
        if self.in_board():
            self.show_board()
        self.remember(path)
        self.update_title()
        return True

    def remember(self, path):
        recent = [r for r in self.settings.value("recent", "").split("\n") if r and r != str(path)]
        self.settings.setValue("lastFile", str(path))
        self.settings.setValue("recent", "\n".join([str(path)] + recent[:7]))

    def new(self):
        if not self.confirm_discard():
            return
        self.path = None
        self.editor.clear()
        self.editor.document().setModified(False)
        self.selected = -1
        self.refresh_sidebar()
        self.update_title()

    def open(self):
        start = str(self.path.parent) if self.path else str(Path.home())
        name, _ = QFileDialog.getOpenFileName(self, "Open", start)
        if name:
            self.open_path(Path(name))

    def open_path(self, path):
        if self.confirm_discard():
            self.load(path)

    def save(self):
        return self.write(self.path) if self.path else self.save_as()

    def save_as(self):
        start = str(self.path) if self.path else str(Path.home())
        name, _ = QFileDialog.getSaveFileName(self, "Save As", start)
        return self.write(Path(name)) if name else False

    def write(self, path):
        try:
            path.write_text(self.editor.toPlainText(), encoding="utf-8")
        except OSError as err:
            QMessageBox.warning(self, "Save failed", f"{path}\n\n{err}")
            return False
        self.path = path
        self.editor.document().setModified(False)
        self.remember(path)
        self.update_title()
        return True

    def closeEvent(self, event):
        event.accept() if self.confirm_discard() else event.ignore()
