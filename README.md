# Cardigan

A small text editor that turns your markdown to-do list into a kanban board.

I like writing my to-dos in a plain text editor, and I like seeing them on a Trello style board, but I don't like creating and moving cards. Cardigan lets you write the list as markdown and press **Ctrl+M** to see it as a board. The board is read-only: you change things by editing the text.

## The format

```markdown
# Project            <- a board
## Column            <- a column on that board
- Card               <- a card (a top-level line under a column)
    Card content     <- anything indented under a card is its content
```

- Cards can start with `-`, `*` or `+`, or be plain lines.
- Cards placed directly under a project, with no column, go in an unnamed column.
- Inline `` `code` ``, `**bold**` and links work in the board view.

A small example:

```markdown
# Ad Studio
## To do
- Copy prompt
- Model and explain database
## Ideas
- Dashboard
- Link classifier permission on config
    so users can add different websites

# Side project
- Update skill description
```

## Run it

Needs Python 3.10+ and [PySide6](https://pypi.org/project/PySide6/) (with Qt WebEngine).

```
pip install PySide6
python3 -m cardigan [file]
```

With no file, Cardigan reopens the last one you used. To get a `cardigan` command, run `pip install -e .` in this folder.

## Using it

The sidebar lists your projects with their card counts. In the editor, clicking a project jumps to its heading. In the board view, it shows only that project.

| Keys | Action |
| --- | --- |
| Ctrl+M | Switch between editor and board |
| Ctrl+B | Show or hide the sidebar |
| Ctrl+N / O / S, Ctrl+Shift+S | New, open, save, save as |
| Alt+Up / Down | Move the line (or selected lines) |
| Alt+Shift+Up / Down | Copy the line (or selected lines) up or down |
| Ctrl+Enter | New line below |
| Ctrl+Shift+Enter | New line above |
| Ctrl+X with no selection | Cut the whole line |

The editor also has line numbers, and colors the `#` and `##` lines (the colors are in `cardigan/theme.py`).

## Layout

```
cardigan/
├── parser.py       markdown text -> projects, columns, cards
├── renderer.py     parsed projects -> board HTML and CSS
├── theme.py        heading colors and style tweaks
├── sidebar.py      the project list
├── window.py       main window, menus, open and save
└── editor/         the text editor: line numbers, highlighting, line shortcuts
```

`parser.py` and `renderer.py` don't use Qt.
