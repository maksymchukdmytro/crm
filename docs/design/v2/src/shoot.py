# python3 shoot.py name[:WxH] ...  → png/<name>.png (2x)
import sys, os
from playwright.sync_api import sync_playwright
R = os.path.dirname(os.path.abspath(__file__))
with sync_playwright() as p:
    b = p.chromium.launch()
    for arg in sys.argv[1:]:
        name, _, size = arg.partition(":")
        w, h = (int(x) for x in (size or "1440x900").split("x"))
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(f"file://{R}/{name}.html")
        pg.wait_for_selector("body[data-ready]", timeout=5000)
        pg.wait_for_timeout(300)
        pg.screenshot(path=f"{R}/png/{name}.png")
        print(name, "ok" if not errs else errs)
    b.close()
