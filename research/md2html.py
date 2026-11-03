"""Render oss-landscape-2026-11.md into a self-contained HTML page (marked.js from cdnjs).

Usage: python3 md2html.py   (run from this folder)
"""
import html
import pathlib

here = pathlib.Path(__file__).parent
md = (here / "oss-landscape-2026-11.md").read_text()
assert "</script" not in md, "markdown would break out of the embedding <script>"

page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Open-Source Landscape for a Unified Organizational Knowledge Base</title>
<style>
:root{{color-scheme:light dark;--fg:#1f2328;--bg:#fff;--muted:#59636e;--line:#d1d9e0;--head:#f6f8fa;--link:#0969da}}
@media (prefers-color-scheme:dark){{:root{{--fg:#e6edf3;--bg:#0d1117;--muted:#9198a1;--line:#3d444d;--head:#151b23;--link:#4493f8}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:32px 20px 80px}}
h1{{font-size:1.9em;line-height:1.25}} h2{{margin-top:2.2em;padding-bottom:.3em;border-bottom:1px solid var(--line)}} h3{{margin-top:1.6em}}
a{{color:var(--link)}} code{{font:0.88em ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--head);padding:.1em .35em;border-radius:4px}}
.tw{{overflow-x:auto;margin:1em 0;border:1px solid var(--line);border-radius:6px}}
table{{border-collapse:collapse;width:100%;font-size:13.5px}}
th,td{{border-bottom:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}}
th{{background:var(--head);position:sticky;top:0}} tr:last-child td{{border-bottom:0}}
blockquote{{margin:0;padding:0 1em;color:var(--muted);border-left:3px solid var(--line)}}
hr{{border:0;border-top:1px solid var(--line);margin:2em 0}}
pre#fallback{{white-space:pre-wrap}}
</style></head>
<body><main id="out"><pre id="fallback">{html.escape(md)}</pre></main>
<script type="text/markdown" id="src">{md}</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js"></script>
<script>
try {{
  const out = document.getElementById('out');
  out.innerHTML = marked.parse(document.getElementById('src').textContent);
  out.querySelectorAll('table').forEach(t => {{ const w = document.createElement('div'); w.className = 'tw'; t.replaceWith(w); w.appendChild(t); }});
}} catch (e) {{ /* fallback <pre> stays visible */ }}
</script>
</body></html>"""

(here / "oss-landscape-2026-11.html").write_text(page)
print(f"wrote {len(page)} bytes")
