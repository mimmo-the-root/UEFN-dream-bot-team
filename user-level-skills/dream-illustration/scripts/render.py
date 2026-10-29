"""Render out/*.svg to png/*.png with Playwright Chromium. Usage: python render.py [name-part ...]
Fonts: npm i @fontsource/caveat-brush @fontsource/patrick-hand in this folder (set DREAM_FONTS to override the path)."""
import glob, os, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.environ.get("DREAM_FONTS", os.path.join(HERE, "node_modules", "@fontsource"))
css = f"""
@font-face{{font-family:'Caveat Brush';src:url('file://{FONTS}/caveat-brush/files/caveat-brush-latin-400-normal.woff2') format('woff2');}}
@font-face{{font-family:'Patrick Hand';src:url('file://{FONTS}/patrick-hand/files/patrick-hand-latin-400-normal.woff2') format('woff2');}}
"""
os.makedirs("png", exist_ok=True)
only = sys.argv[1:]
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1360, "height": 768}, device_scale_factor=1)
    for f in sorted(glob.glob("out/*.svg")):
        name = os.path.basename(f)[:-4]
        if only and not any(o in name for o in only):
            continue
        svg = open(f, encoding="utf-8").read()
        tmp = os.path.join(HERE, "tmp.html")
        open(tmp, "w", encoding="utf-8").write(f"<html><head><style>{css} body{{margin:0}}</style></head><body>{svg}</body></html>")
        pg.goto("file://" + tmp)
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(500)
        pg.screenshot(path=f"png/{name}.png")
        print(name)
    b.close()
