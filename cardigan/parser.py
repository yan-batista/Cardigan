"""Turns the markdown outline into projects, columns and cards. No Qt in here."""
import re

BULLET = re.compile(r"^[-*+]\s+")


def parse(text):
    """Returns [(project, [(column, [(card_title, [(depth, line)])])], line_number)]."""
    projects = []
    base = None  # indent of the cards in the current column
    for number, raw in enumerate(text.splitlines()):
        line = raw.rstrip()
        if line.startswith("## "):
            if not projects:
                projects.append(("", [], number))
            projects[-1][1].append((line[3:].strip(), []))
            base = None
        elif line.startswith("# "):
            projects.append((line[2:].strip(), [], number))
            base = None
        elif line.strip():
            if not projects:
                projects.append(("", [], number))
            if not projects[-1][1]:  # cards directly under a project get an unnamed column
                projects[-1][1].append(("", []))
            cards = projects[-1][1][-1][1]
            expanded = line.expandtabs(4)
            indent = len(expanded) - len(expanded.lstrip())
            if base is None:
                base = indent
            body = BULLET.sub("", expanded.strip())
            if indent <= base or not cards:
                cards.append((body, []))
            else:
                cards[-1][1].append((indent - base, body))
    return projects
