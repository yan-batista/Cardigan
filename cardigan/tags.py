"""Tags: [NAME] or [NAME:COLOR] in card titles, plus the app-wide registry. No Qt in here."""
import json
import os
import re
from pathlib import Path

NAMED = {"RED": "#e5484d", "ORANGE": "#f76b15", "YELLOW": "#e5b800", "GREEN": "#30a46c",
         "BLUE": "#3e63dd", "PURPLE": "#8e4ec6", "PINK": "#d6409f", "GRAY": "#8b8d98"}
STANDARD = NAMED["GRAY"]
HEX = r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})"
# "[x]" is a checkbox and "[text](url)" a link, so neither is a tag
TAG = re.compile(rf"\[(?![xX][\]:])([\w-]+)(?::([A-Za-z]+|{HEX}))?\](?!\()")
PATH = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "cardigan" / "tags.json"


def load():
    """The registry: [{"name", "alias", "color"}]. A missing or broken file is an empty registry."""
    try:
        return [t for t in json.loads(PATH.read_text()) if isinstance(t, dict) and t.get("name")]
    except (OSError, ValueError, TypeError):
        return []


def save(registry):
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(registry, indent=2))


def valid_color(color):
    return color.upper() in NAMED or re.fullmatch(HEX, color) is not None


def color_hex(color):
    return NAMED.get(color.upper()) or (color if re.fullmatch(HEX, color) else STANDARD)


def text_color(bg):
    h = bg[1:]
    r, g, b = (int(c * 2, 16) for c in h) if len(h) == 3 else (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#000" if 0.299 * r + 0.587 * g + 0.114 * b > 150 else "#fff"


def resolve(title, registry):
    """Returns (title without its tags, [(label, background color)]), one chip per distinct tag."""
    lookup = {}
    for t in registry:
        lookup.setdefault(t["name"].lower(), t)
        if t.get("alias"):
            lookup.setdefault(t["alias"].lower(), t)
    chips = {}

    def take(m):
        name, inline = m.groups()
        known = lookup.get(name.lower())
        label = known["name"] if known else name
        color = known.get("color") if known else inline  # the registry color wins over an inline one
        chips.setdefault(label.lower(), (label.capitalize(), color_hex(color or "")))
        return ""

    return " ".join(TAG.sub(take, title).split()), list(chips.values())
