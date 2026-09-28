from __future__ import annotations
import html, json, shutil, subprocess
from pathlib import Path
from typing import Iterable


def design_status() -> dict:
    exe = shutil.which('12ui') or shutil.which('12ui.cmd')
    return {
        'primary': '12ui',
        'primary_installed': bool(exe),
        'primary_path': exe,
        'primary_note': 'The 12ui CLI can be retained locally, but hosted design generation may still require internet/service access.',
        'fallback': 'forge_local_design',
        'fallback_ready': True,
        'offline_capable': True,
    }


def render_local_page(title: str, subtitle: str, sections: Iterable[dict], output: str | Path) -> Path:
    """Dependency-free local UI fallback. Produces a responsive, readable single-file HTML page."""
    output=Path(output); output.parent.mkdir(parents=True,exist_ok=True)
    cards=[]
    for section in sections:
        h=html.escape(str(section.get('title','Section')))
        body=section.get('body','')
        if isinstance(body,(dict,list)):
            body='<pre>'+html.escape(json.dumps(body,indent=2))+'</pre>'
        else:
            body='<p>'+html.escape(str(body)).replace('\n','<br>')+'</p>'
        cards.append(f'<section class="card"><h2>{h}</h2>{body}</section>')
    doc=f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>
:root{{--bg:#07111f;--panel:#0f2033;--ink:#edf7ff;--muted:#a8bfd1;--accent:#65d8ff;--line:#24435c}}
*{{box-sizing:border-box}}body{{margin:0;background:linear-gradient(180deg,#06101c,#0a1725);color:var(--ink);font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:1050px;margin:auto;padding:48px 22px 80px}}header{{padding:28px 0 34px;border-bottom:1px solid var(--line);margin-bottom:28px}}
h1{{font-size:clamp(2rem,5vw,4.2rem);line-height:1.02;margin:.2em 0}}header p{{color:var(--muted);font-size:1.15rem;max-width:760px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px}}.card{{background:rgba(15,32,51,.92);border:1px solid var(--line);border-radius:18px;padding:22px;box-shadow:0 16px 40px #0004}}
.card h2{{margin-top:0;color:var(--accent)}}pre{{white-space:pre-wrap;word-break:break-word;background:#07111f;padding:14px;border-radius:12px;overflow:auto}}footer{{color:var(--muted);margin-top:28px;font-size:.9rem}}
</style></head><body><main><header><small>FORGE LOCAL DESIGN • OFFLINE</small><h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p></header><div class="grid">{''.join(cards)}</div><footer>Generated locally without a hosted design dependency.</footer></main></body></html>'''
    output.write_text(doc,encoding='utf-8')
    return output
