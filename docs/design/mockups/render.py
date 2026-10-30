"""python3 render.py v1_bento [v2_glass ...] — HTML-дошка + PNG кожного кадру + PNG дошки."""
import importlib, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT))

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1243/chrome-linux64/chrome", args=["--no-sandbox", "--allow-file-access-from-files"])
    for mod in sys.argv[1:]:
        m = importlib.import_module(mod)
        html = OUT / f"{mod}.html"
        html.write_text(m.build(), encoding="utf-8")
        pg = b.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=1)
        errs = []
        pg.on("console", lambda msg: errs.append(msg.text) if msg.type == "error" else None)
        pg.goto(html.as_uri())
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(600)
        for fr in pg.query_selector_all(".frame"):
            fr.screenshot(path=str(OUT / f"{mod}-{fr.get_attribute('data-name')}.png"))
        pg.screenshot(path=str(OUT / f"{mod}-board.png"), full_page=True)
        print(mod, "ok", errs[:3])
        pg.close()
    b.close()
