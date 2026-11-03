"""Render a Markdown file into a self-contained HTML page next to it (marked.js, plus mermaid.js when needed, from cdnjs).

Usage: python3 md2html.py [path/to/file.md]   (default: oss-landscape-2026-11.md beside this script)
"""
import html
import pathlib
import sys

here = pathlib.Path(__file__).parent
src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else here / "oss-landscape-2026-11.md"
md = src.read_text()
assert "</script" not in md, "markdown would break out of the embedding <script>"
title = next((line[2:].strip() for line in md.splitlines() if line.startswith("# ")), src.stem)
mermaid = '<script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/12.2.0/mermaid.min.js"></script>' if "```mermaid" in md else ""

page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root{{color-scheme:light dark;--fg:#1f2328;--bg:#fff;--muted:#59636e;--line:#d1d9e0;--head:#f6f8fa;--link:#0969da}}
@media (prefers-color-scheme:dark){{:root{{--fg:#e6edf3;--bg:#0d1117;--muted:#9198a1;--line:#3d444d;--head:#151b23;--link:#4493f8}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:32px 20px 80px}}
h1{{font-size:1.9em;line-height:1.25}} h2{{margin-top:2.2em;padding-bottom:.3em;border-bottom:1px solid var(--line)}} h3{{margin-top:1.6em}}
a{{color:var(--link)}} code{{font:0.88em ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--head);padding:.1em .35em;border-radius:4px}}
pre{{background:var(--head);padding:12px 14px;border-radius:6px;overflow-x:auto}} pre code{{background:none;padding:0}}
pre.mermaid{{background:none;text-align:center}}
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
{mermaid}
<script>
try {{
  const out = document.getElementById('out');
  out.innerHTML = marked.parse(document.getElementById('src').textContent);
  out.querySelectorAll('table').forEach(t => {{ const w = document.createElement('div'); w.className = 'tw'; t.replaceWith(w); w.appendChild(t); }});
  out.querySelectorAll('a[href$=".md"]').forEach(a => {{ if (!/^[a-z]+:/i.test(a.getAttribute('href'))) a.setAttribute('href', a.getAttribute('href').replace(/\\.md$/, '.html')); }});
  out.querySelectorAll('code.language-mermaid').forEach(c => {{ const d = document.createElement('pre'); d.className = 'mermaid'; d.textContent = c.textContent; c.parentElement.replaceWith(d); }});
  if (window.mermaid) {{ mermaid.initialize({{startOnLoad: false, theme: matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'default'}}); mermaid.run(); }}
}} catch (e) {{ /* fallback <pre> stays visible */ }}
</script>
</body></html>"""

dst = src.with_suffix(".html")
dst.write_text(page)
print(f"wrote {dst} ({len(page)} bytes)")
