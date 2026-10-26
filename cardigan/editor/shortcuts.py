"""VS Code style line shortcuts for the editor.

    Alt+Up/Down              move the line(s)
    Alt+Shift+Up/Down        copy the line(s) up or down
    Ctrl+Enter               new line below
    Ctrl+Shift+Enter         new line above
    Ctrl+X without selection cut the whole line
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QTextCursor

CTRL = Qt.ControlModifier
CTRL_SHIFT = Qt.ControlModifier | Qt.ShiftModifier
ALT = Qt.AltModifier
ALT_SHIFT = Qt.AltModifier | Qt.ShiftModifier


def handle_key(editor, event):
    """Runs the shortcut for this key press and returns True, or returns False if there is none."""
    mods = event.modifiers() & ~Qt.KeypadModifier
    key = event.key()
    if key in (Qt.Key_Up, Qt.Key_Down) and mods == ALT:
        move_lines(editor, up=key == Qt.Key_Up)
    elif key in (Qt.Key_Up, Qt.Key_Down) and mods == ALT_SHIFT:
        copy_lines(editor, up=key == Qt.Key_Up)
    elif key in (Qt.Key_Return, Qt.Key_Enter) and mods in (CTRL, CTRL_SHIFT):
        insert_line(editor, below=mods == CTRL)
    elif key == Qt.Key_X and mods == CTRL and not editor.textCursor().hasSelection():
        cut_line(editor)
    else:
        return False
    return True


def selected_blocks(editor):
    """First and last block touched by the selection (or the cursor line)."""
    cursor = editor.textCursor()
    start, end = sorted((cursor.anchor(), cursor.position()))
    doc = editor.document()
    first, last = doc.findBlock(start), doc.findBlock(end)
    if end > start and end == last.position():  # selection ends at the start of a line
        last = last.previous()
    return first, last


def text_between(editor, start, end):
    cursor = QTextCursor(editor.document())
    cursor.setPosition(start)
    cursor.setPosition(end, QTextCursor.KeepAnchor)
    return cursor


def lines_between(editor, start, end):
    return text_between(editor, start, end).selectedText().split(" ")


def replace_range(editor, start, end, text, anchor, position):
    """Replaces [start, end) as one undo step and restores the selection."""
    cursor = text_between(editor, start, end)
    cursor.beginEditBlock()
    cursor.insertText(text)
    cursor.endEditBlock()
    cursor = editor.textCursor()
    cursor.setPosition(anchor)
    cursor.setPosition(position, QTextCursor.KeepAnchor)
    editor.setTextCursor(cursor)


def move_lines(editor, up):
    first, last = selected_blocks(editor)
    other = first.previous() if up else last.next()
    if not other.isValid():
        return
    cursor = editor.textCursor()
    start = other.position() if up else first.position()
    tail = last if up else other
    end = tail.position() + len(tail.text())
    lines = lines_between(editor, start, end)
    lines = lines[1:] + lines[:1] if up else lines[-1:] + lines[:-1]
    shift = (-1 if up else 1) * (len(other.text()) + 1)
    replace_range(editor, start, end, "\n".join(lines), cursor.anchor() + shift, cursor.position() + shift)


def copy_lines(editor, up):
    first, last = selected_blocks(editor)
    cursor = editor.textCursor()
    start, end = first.position(), last.position() + len(last.text())
    text = "\n".join(lines_between(editor, start, end))
    if up:  # the selection stays on the upper copy
        replace_range(editor, start, start, text + "\n", cursor.anchor(), cursor.position())
    else:
        shift = len(text) + 1
        replace_range(editor, end, end, "\n" + text, cursor.anchor() + shift, cursor.position() + shift)


def insert_line(editor, below):
    block = editor.textCursor().block()
    indent = block.text()[:len(block.text()) - len(block.text().lstrip())]
    cursor = editor.textCursor()
    cursor.clearSelection()
    cursor.beginEditBlock()
    cursor.movePosition(QTextCursor.EndOfBlock if below else QTextCursor.StartOfBlock)
    cursor.insertText("\n")
    if not below:
        cursor.movePosition(QTextCursor.Left)
    cursor.insertText(indent)
    cursor.endEditBlock()
    editor.setTextCursor(cursor)


def cut_line(editor):
    block = editor.textCursor().block()
    start, end = block.position(), block.position() + len(block.text())
    if block.next().isValid():
        end += 1  # take the line break with the line
    elif block.previous().isValid():
        start -= 1
    QGuiApplication.clipboard().setText(block.text() + "\n")
    text_between(editor, start, end).removeSelectedText()
