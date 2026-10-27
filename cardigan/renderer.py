"""Renders parsed projects as the HTML shown in the board view. No Qt in here."""
import html
import re

from .tags import resolve, text_color

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
.card .t { font-weight:600; } .t:empty { display:none; }
.tags { display:flex; flex-wrap:wrap; gap:4px; margin-top:4px; } .tags:empty, .m-tags:empty { display:none; }
.tag { font-size:11px; font-weight:600; border-radius:3px; padding:1px 8px; }
.m-tags { display:flex; flex-wrap:wrap; gap:4px; margin-top:8px; }
.card .c { color:var(--mute); font-size:13px; margin-top:4px; }
.card .c div { margin-top:2px; }
.card .c { display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.card { cursor:pointer; }
dialog { background:var(--bg); color:var(--fg); border:0; border-radius:12px; padding:0;
         width:min(720px, 92vw); max-height:86vh; overflow:auto; box-shadow:0 12px 48px rgba(0,0,0,.45); }
dialog::backdrop { background:rgba(0,0,0,.6); }
.m-head { padding:20px 56px 12px 24px; }
.m-title { font-size:20px; font-weight:600; line-height:1.3; }
.m-list { color:var(--mute); font-size:13px; margin-top:4px; }
.m-close { position:absolute; top:12px; right:12px; width:32px; height:32px; border:0; border-radius:6px;
           background:none; color:var(--mute); font-size:20px; cursor:pointer; }
.m-close:hover { background:var(--col); color:var(--fg); }
.m-body { padding:4px 24px 24px; }
.m-body h3 { font-size:14px; margin:16px 0 8px; }
.m-body .c { display:block; overflow:visible; margin:0; font-size:14px; color:var(--fg); background:var(--card);
             border-radius:8px; padding:10px 12px; }
.m-body .c div { margin-top:4px; } .m-body .c div:first-child { margin-top:0; }
.m-body .none { color:var(--mute); font-style:italic; }
.empty { color:var(--mute); font-size:12px; margin:0 4px 4px; }
"""


def inline(s):
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    return re.sub(r"(https?://[^\s<]+)", r'<a href="\1">\1</a>', s)


def render(projects, registry=()):
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
                title, chips = resolve(title, registry)
                tags = "".join(f'<span class="tag" style="background:{bg};color:{text_color(bg)}">{label}</span>'
                               for label, bg in chips)
                out.append(f'<div class="card" data-col="{html.escape(col, quote=True)}"><div class="t">{inline(title)}</div>'
                           f'<div class="tags">{tags}</div>')
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
    script = '''<dialog id=m><button class=m-close aria-label=Close>&times;</button>
<div class=m-head><div class=m-title></div><div class=m-tags></div><div class=m-list></div></div>
<div class=m-body><h3>Description</h3><div class=m-desc></div></div></dialog><script>
addEventListener('wheel',e=>{if(e.ctrlKey)e.preventDefault()},{passive:false});
const m=document.getElementById('m'),q=s=>m.querySelector(s);
document.addEventListener('click',e=>{
  const c=e.target.closest('.card');if(!c||e.target.closest('a'))return;
  q('.m-title').innerHTML=c.querySelector('.t').innerHTML;
  q('.m-tags').innerHTML=c.querySelector('.tags').innerHTML;
  q('.m-list').textContent=c.dataset.col?'in list '+c.dataset.col:'';
  const d=c.querySelector('.c');
  q('.m-desc').innerHTML=d?d.outerHTML:'<div class=none>No description</div>';
  m.showModal();m.scrollTop=0});
q('.m-close').onclick=()=>m.close();
m.addEventListener('click',e=>{if(e.target===m)m.close()});
</script>'''
    return "<!doctype html><meta charset=utf-8>" + "".join(out) + script
