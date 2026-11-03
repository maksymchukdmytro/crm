import sys
from playwright.sync_api import sync_playwright
B=sys.argv[1] if len(sys.argv)>1 else "http://localhost:8077"; O="/tmp/claude-0/views"
import os; os.makedirs(O,exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1243/chrome-linux64/chrome",args=["--no-sandbox"])
    for W,H in [(1280,800),(1600,900)]:
        pg=b.new_context(viewport={"width":W,"height":H}).new_page(); errs=[]
        pg.on("pageerror",lambda e: errs.append(str(e)[:200]))
        pg.on("console", lambda m: m.type=="error" and "401" not in m.text and errs.append("console: "+m.text[:160]))
        pg.goto(B+"/login"); pg.wait_for_timeout(500)
        pg.locator("input").nth(0).fill("admin"); pg.locator("input[type=password]").fill("admin12345"); pg.keyboard.press("Enter"); pg.wait_for_timeout(1200)
        for v in ["table","cards","inbox"]:
            pg.evaluate(f"localStorage.setItem('crm-orders-view','{v}')")
            pg.goto(B+"/orders"); pg.wait_for_timeout(2200)
            pg.screenshot(path=f"{O}/{W}-{v}.png")
            print(W, v, "overflowX", pg.evaluate("document.documentElement.scrollWidth-innerWidth"), "url", pg.url.split('8077')[-1].split('8078')[-1])
        # inbox: J to next, filter panel, unsorted tab
        pg.keyboard.press("j"); pg.wait_for_timeout(1200); print(W,"after J", pg.url[-20:])
        pg.locator(".lh-filter").click(); pg.wait_for_timeout(500); pg.screenshot(path=f"{O}/{W}-filters.png")
        pg.locator(".list-tabs button").first.click(); pg.wait_for_timeout(1800); pg.screenshot(path=f"{O}/{W}-inbox-unsorted.png"); print(W,"unsorted", pg.url[-30:])
        pg.evaluate("localStorage.setItem('crm-orders-view','cards')")
        pg.goto(B+"/orders?status="+pg.url.split("status=")[-1] if "status=" in pg.url else B+"/orders"); pg.wait_for_timeout(1800); pg.screenshot(path=f"{O}/{W}-cards-unsorted.png")
        pg.evaluate("localStorage.setItem('crm-orders-view','table')")
        print(W, "errors", errs[:5])
    b.close()
