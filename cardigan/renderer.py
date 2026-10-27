"""Renders parsed projects as the HTML shown in the board view. No Qt in here."""
import html
import re

CSS = """
:root { color-scheme: light dark; --bg:#f4f5f7; --col:#e4e6ea; --card:#fff; --fg:#1d2430; --mute:#5b6572; }
@media (prefers-color-scheme: dark) { :root { --bg:#16191e; --col:#22262d; --card:#2d323b; --fg:#e6e9ee; --mute:#9aa4b2; } }
* { box-sizing: border-box; }
body { margin:0; padding:24px; background:var(--bg); color:var(--fg);
       font:14px/1.45 system-ui, sans-serif; }
h1 { font-size:20px; margin:28px 0 12px; } h1:first-child { margin-top:0; }
.board { display:flex; gap:12px; align-items:flex-start; overflow-x:auto; padding-bottom:8px; }
.col { background:var(--col); border-radius:8px; padding:10px; width:280px; flex:none; }
.col h2 { font-size:12px; text-transform:uppercase; letter-spacing:.06em; color:var(--mute);
          margin:2px 4px 10px; display:flex; justify-content:space-between; }
.card { background:var(--card); border-radius:6px; padding:8px 10px; margin-bottom:8px;
        box-shadow:0 1px 2px rgba(0,0,0,.18); }
.card .t { font-weight:600; }
.card .c { color:var(--mute); font-size:13px; margin-top:4px; }
.card .c div { margin-top:2px; }
.empty { color:var(--mute); font-size:12px; margin:0 4px 4px; }
"""


def inline(s):
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    return re.sub(r"(https?://[^\s<]+)", r'<a href="\1">\1</a>', s)


def render(projects):
    out = [f"<style>{CSS}</style>"]
    for name, columns, _ in projects:
        if name:
            out.append(f"<h1>{inline(name)}</h1>")
        out.append('<div class="board">')
        for col, cards in columns:
            out.append(f'<div class="col"><h2><span>{inline(col)}</span><span>{len(cards)}</span></h2>')
            if not cards:
                out.append('<div class="empty">empty</div>')
            for title, content in cards:
                out.append(f'<div class="card"><div class="t">{inline(title)}</div>')
                if content:
                    out.append('<div class="c">')
                    for _, body in content:
                        out.append(f"<div>{inline(body)}</div>")
                    out.append("</div>")
                out.append("</div>")
            out.append("</div>")
        out.append("</div>")
    if len(out) == 1:
        out.append('<p class="empty">Nothing to show. Start with "# Project" and "## Column".</p>')
    # Chromium zooms the page on Ctrl+wheel; cancel it
    script = "<script>addEventListener('wheel',e=>{if(e.ctrlKey)e.preventDefault()},{passive:false})</script>"
    return "<!doctype html><meta charset=utf-8>" + "".join(out) + script
