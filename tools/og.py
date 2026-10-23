#!/usr/bin/env python3
"""Render assets/og.png (1200x630 social preview) from a small inline page. Needs playwright + chromium."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
HTML = f"""<!doctype html><meta charset=utf-8><style>
@font-face{{font-family:Inter;font-weight:100 900;src:url(file://{ROOT}/assets/fonts/inter-latin-wght-normal.woff2) format('woff2')}}
*{{box-sizing:border-box}}body{{margin:0;width:1200px;height:630px;background:#0b1020;color:#f2f5ff;font-family:Inter,sans-serif;position:relative;overflow:hidden}}
.grid{{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px);background-size:56px 56px}}
.glow{{position:absolute;width:800px;height:800px;right:-220px;top:-260px;background:radial-gradient(circle,rgba(79,140,255,.28),transparent 65%)}}
.wrap{{position:absolute;left:84px;top:84px;right:84px;bottom:84px;display:flex;flex-direction:column;justify-content:space-between}}
.k{{color:#3ddc97;font-weight:600;letter-spacing:.16em;text-transform:uppercase;font-size:24px}}
h1{{margin:18px 0 0;font-size:92px;line-height:1.02;letter-spacing:-.035em;font-weight:800;max-width:900px}}h1 em{{font-style:normal;color:#3ddc97}}
.row{{display:flex;justify-content:space-between;align-items:flex-end}}.name{{font-size:34px;font-weight:700}}.sub{{color:#a9b4d0;font-size:26px;margin-top:6px}}
.dots{{display:flex;gap:14px;align-items:center}}.dots i{{width:22px;height:22px;border-radius:50%;display:block}}
</style><div class=grid></div><div class=glow></div><div class=wrap><div><div class=k>AI automation &middot; Data integration</div><h1>Automations that <em>don&rsquo;t fail quietly.</em></h1></div>
<div class=row><div><div class=name>Alfredo Ochoa</div><div class=sub>12 public demo projects &middot; open code and tests</div></div><div class=dots><i style="background:#4f8cff"></i><i style="background:#3ddc97"></i><i style="background:#ffb454"></i></div></div></div>"""
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--allow-file-access-from-files"]); pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.set_content(HTML); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(500)
    pg.screenshot(path=str(ROOT / "assets/og.png")); b.close()
print("wrote assets/og.png")
