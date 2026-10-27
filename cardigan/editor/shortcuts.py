"""VS Code style line shortcuts for the editor.

    Alt+Up/Down              move the line(s)
    Alt+Shift+Up/Down        copy the line(s) up or down
    Ctrl+Enter               new line below
    Ctrl+Shift+Enter         new line above
    Ctrl+X without selection cut the whole line
    Ctrl+Y                   redo
    Alt+Left/Right           move the card (and its nested lines) to the previous/next column
    Ctrl+F                   ask the window to open the find bar
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
    elif key == Qt.Key_Y and mods == CTRL:
        editor.redo()
    elif key in (Qt.Key_Left, Qt.Key_Right) and mods == ALT:
        move_card(editor, right=key == Qt.Key_Right)
    elif key == Qt.Key_F and mods == CTRL:
        editor.find_requested.emit()
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
    return text_between(editor, start, end).selectedText().split("\u2029")


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


def indent_of(line):
    expanded = line.expandtabs(4)
    return len(expanded) - len(expanded.lstrip())


def move_card(editor, right):
    """Moves the top-level card at the cursor, with its nested lines, to the end of the adjacent column."""
    lines = editor.toPlainText().split("\n")
    n = editor.textCursor().blockNumber()
    is_heading = lambda line: line.startswith(("# ", "## "))

    def column_end(head):
        end = head + 1
        while end < len(lines) and not is_heading(lines[end]):
            end += 1
        return end

    def column_base(head, end):
        return next((indent_of(l) for l in lines[head + 1:end] if l.strip()), 0)

    head = n
    while head >= 0 and not is_heading(lines[head]):
        head -= 1
    if head < 0 or head == n or not lines[head].startswith("## ") or not lines[n].strip():
        return
    end = column_end(head)
    base = column_base(head, end)
    start = n
    while start > head + 1 and (not lines[start].strip() or indent_of(lines[start]) > base):
        start -= 1
    stop = start + 1
    while stop < end and (not lines[stop].strip() or indent_of(lines[stop]) > base):
        stop += 1
    while not lines[stop - 1].strip():
        stop -= 1

    if right:
        target = end
    else:
        target = head - 1
        while target >= 0 and not is_heading(lines[target]):
            target -= 1
    if not 0 <= target < len(lines) or not lines[target].startswith("## "):
        return
    target_end = column_end(target)
    target_base = column_base(target, target_end)
    insert = target_end
    while insert > target + 1 and not lines[insert - 1].strip():
        insert -= 1

    card = lines[start:stop]
    if target_base != base:
        card = [" " * target_base + l.expandtabs(4)[base:] if l.strip() else l for l in card]
    del lines[start:stop]
    if insert > start:
        insert -= stop - start
    lines[insert:insert] = card

    cursor = editor.textCursor()
    cursor.beginEditBlock()
    cursor.select(QTextCursor.Document)
    cursor.insertText("\n".join(lines))
    cursor.endEditBlock()
    editor.setTextCursor(cursor)
    cursor.setPosition(editor.document().findBlockByNumber(insert + n - start).position())
    editor.setTextCursor(cursor)
    editor.ensureCursorVisible()
