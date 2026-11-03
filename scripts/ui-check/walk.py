"""Повний прохід CRM (ПК 1440×900 і телефон 390×844) на базі з ~2 650 замовлень: кожна сторінка, головні дії, скриншоти,
автоматичні перевірки (помилки JS, відповіді 5xx/4xx, прокрутка вшир на телефоні, дрібні цілі дотику) і заміри швидкості."""
import json, re, sys, time
from playwright.sync_api import sync_playwright

B = "http://localhost:8078"
OUT = "/tmp/claude-0/walk"
import os
os.makedirs(OUT, exist_ok=True)
LOG = []


def say(*a):
    s = " ".join(str(x) for x in a)
    LOG.append(s)
    print(s, flush=True)


def np_mocks(pg):
    j = lambda r, d: r.fulfill(status=200, content_type="application/json", body=json.dumps(d, ensure_ascii=False))
    pg.route(re.compile(r".*/api/np/cities.*"), lambda r: j(r, {"ok": True, "items": [{"ref": "CK", "name": "Київ", "label": "Київ (місто, Київська обл.)"}]}))
    pg.route(re.compile(r".*/api/np/warehouses.*"), lambda r: j(r, {"ok": True, "items": [
        {"ref": f"W{i}", "name": f"Відділення №{i} (до 30 кг): вул. Хрещатик, {i}", "label": f"Відділення №{i} (до 30 кг): вул. Хрещатик, {i}", "max_weight": 30, "kind": "branch"} for i in range(1, 9)]}))

    def prev(route):
        resp = route.fetch(); d = resp.json()
        if d.get("supported") and "city_ref=" in route.request.url:
            d.update(price=85, eta=time.strftime("%Y-%m-%d", time.localtime(time.time() + 86400)))
        route.fulfill(response=resp, json=d)
    pg.route(re.compile(r".*/ttn/preview.*"), prev)


CHECK = """(mobile) => {
  const out = {};
  out.overflowX = document.documentElement.scrollWidth - window.innerWidth;
  if (mobile) {
    const small = [];
    for (const el of document.querySelectorAll('button, a[href], [role=button], input[type=checkbox], .xsel')) {
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height || r.bottom < 0 || r.top > innerHeight) continue;
      const st = getComputedStyle(el); if (st.visibility === 'hidden' || st.display === 'none') continue;
      if (Math.min(r.width, r.height) < 32) small.push((el.getAttribute('aria-label') || el.textContent || el.className || '').trim().slice(0, 30));
    }
    out.small = small.slice(0, 8); out.smallN = small.length;
  }
  const clipped = [];
  for (const el of document.querySelectorAll('button, .btn, h1, h2, h3, .tab, .chip')) {
    const r = el.getBoundingClientRect(); if (!r.width || r.bottom < 0 || r.top > innerHeight) continue;
    const st = getComputedStyle(el);
    if (st.textOverflow !== 'ellipsis' && el.scrollWidth > el.clientWidth + 2 && st.overflow !== 'visible') clipped.push((el.textContent || '').trim().slice(0, 30));
  }
  out.clipped = clipped.slice(0, 6);
  return out;
}"""


def run(p, name, vp, mobile):
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1243/chrome-linux64/chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport=vp, is_mobile=mobile, has_touch=mobile, device_scale_factor=1)
    ctx.add_init_script("window.__lt=[];new PerformanceObserver(l=>l.getEntries().forEach(e=>window.__lt.push(Math.round(e.duration)))).observe({entryTypes:['longtask']});")
    pg = ctx.new_page()
    errs, bad = [], []
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.on("console", lambda m: m.type == "error" and "401" not in m.text and errs.append("console: " + m.text[:140]))
    pg.on("response", lambda r: ("/api/" in r.url and r.status >= 400 and r.status != 401) and bad.append(f"{r.status} {r.request.method} {r.url.split('8078')[1][:80]}"))
    pg.on("dialog", lambda d: d.accept())
    np_mocks(pg)
    pg.goto(B + "/login"); pg.wait_for_timeout(700)
    pg.locator("input").nth(0).fill("admin"); pg.locator("input[type=password]").fill("admin12345"); pg.keyboard.press("Enter"); pg.wait_for_timeout(1500)
    pg.evaluate("localStorage.removeItem('crm-new-order-draft-2')")
    n = [0]

    def shot(tag, wait=900):
        pg.wait_for_timeout(wait)
        n[0] += 1
        f = f"{OUT}/{name}-{n[0]:02d}-{tag}.png"
        pg.screenshot(path=f)
        c = pg.evaluate(CHECK, mobile)
        issues = []
        if c["overflowX"] > 1: issues.append(f"прокрутка вшир {c['overflowX']}px")
        if mobile and c.get("smallN"): issues.append(f"дрібні цілі ({c['smallN']}): {c['small'][:4]}")
        if c["clipped"]: issues.append(f"обрізаний текст: {c['clipped'][:3]}")
        if errs: issues.append(f"JS: {errs[:2]}"); errs.clear()
        if bad: issues.append(f"API: {sorted(set(bad))[:3]}"); bad.clear()
        say(f"[{name}] {tag}: " + ("OK" if not issues else " | ".join(issues)))

    def go(path, tag, wait=1400):
        t = time.time(); pg.goto(B + path); pg.wait_for_load_state("networkidle"); dt = time.time() - t
        shot(tag, wait)
        say(f"    час відкриття {path}: {dt:.2f} с")

    def click(sel, tag=None, wait=900, nth=0, text=None):
        loc = pg.locator(sel, has_text=text) if text else pg.locator(sel)
        if loc.count() <= nth:
            say(f"[{name}] ⚠ не знайдено «{sel}{' / ' + text if text else ''}»"); return False
        loc.nth(nth).click(); pg.wait_for_timeout(300)
        if tag: shot(tag, wait)
        return True

    # ---- головна, замовлення, картка
    go("/", "головна")
    t = time.time(); pg.goto(B + "/orders"); pg.wait_for_selector(".m-card, .dt-row, [role=row]", timeout=15000); say(f"    список замовлень: перші рядки за {time.time() - t:.2f} с")
    shot("замовлення")
    if not mobile:
        pg.evaluate("window.__lt=[]")
        for _ in range(12):
            pg.mouse.wheel(0, 2500); pg.wait_for_timeout(120)
        say(f"    прокрутка списку: найдовша задача {max(pg.evaluate('window.__lt') or [0])} мс")
        pg.evaluate("document.querySelector('.dt-scroll, .dense, main')?.scrollTo?.(0,0)")
    row = ".m-card" if mobile else "[role=row]:not(.dt-head)"
    t = time.time()
    if click(row, nth=2):
        pg.wait_for_selector(".oc-grid, .oc-hero", timeout=10000); say(f"    картка відкрилась за {time.time() - t:.2f} с"); shot("картка", 1200)
        if mobile:
            pg.mouse.wheel(0, 900); shot("картка-нижче")
        click(".oc-mtile" if mobile else ".oc-ttn-acts .btn", "ттн", 1500, text=None if mobile else "Створити ТТН")
        pg.keyboard.press("Escape"); pg.wait_for_timeout(400)
        pg.keyboard.press("Escape"); pg.wait_for_timeout(400)
    # ---- майстер нового замовлення
    pg.goto(B + "/orders/new"); pg.wait_for_timeout(1500); shot("майстер-1")
    pg.locator("#wz-phone").fill("671112233"); pg.wait_for_timeout(800)
    nm = pg.locator("#wz-name")
    if not nm.input_value(): nm.fill("Стрес Тест Покупець")
    click(".wz-chip"); click(".wz-next")
    pg.locator(".wz-goods .psearch input").fill("а"); pg.wait_for_timeout(300); shot("майстер-2")
    pg.keyboard.press("Enter"); click(".wz-next"); click(".wz-pt"); shot("майстер-3"); click(".wz-next"); shot("майстер-4"); click(".wz-next"); shot("майстер-5")
    before = pg.evaluate("fetch('/api/orders?limit=1').then(r=>r.json()).then(j=>j.items[0].id)")
    nb = pg.locator(".wz-next")
    nb.dblclick(); pg.wait_for_timeout(2500)
    after = pg.evaluate("fetch('/api/orders?limit=3').then(r=>r.json()).then(j=>j.items.filter(x=>x.customer_name.includes('Стрес Тест')||x.phone.endsWith('671112233')).map(x=>x.id))")
    say(f"    подвійний клік «Створити»: створено замовлень {len([i for i in after if i > before])}")
    shot("після-створення", 1500)
    pg.keyboard.press("Escape"); pg.wait_for_timeout(500); pg.keyboard.press("Escape")
    # ---- ліди
    go("/leads", "ліди")
    if click(".lead-cta .go" if mobile else "[role=row]:not(.dt-head)", "лід-вікно", 1200):
        pg.keyboard.press("Escape"); pg.wait_for_timeout(400)
    pg.goto(B + "/leads/new"); pg.wait_for_timeout(1200); shot("новий-лід"); pg.keyboard.press("Escape")
    go("/board", "дошка")
    go("/customers", "покупці")
    click(".cu-mcard" if mobile else "[role=row]:not(.dt-head)", "покупець", 1200); pg.keyboard.press("Escape")
    go("/products", "товари")
    click(".pr-mcard, .m-card" if mobile else "[role=row]:not(.dt-head)", "товар", 1200); pg.keyboard.press("Escape")
    go("/warehouse", "склад")
    go("/purchases", "закупівлі")
    go("/invoices", "накладні")
    click(".doc-arrow", "меню-документа", 500); pg.keyboard.press("Escape"); pg.mouse.click(5, 5)
    go("/stats", "статистика", 2000)
    go("/payments", "оплати")
    go("/reports", "звіти")
    for sec in ["general", "statuses", "dirs", "entities", "delivery", "checkbox", "market", "webhook", "sms", "telegram", "docs", "customers", "users"]:
        go(f"/settings/{sec}", f"налаштування-{sec}", 1200)
    pg.goto(B + "/settings/dirs"); pg.wait_for_timeout(1500)
    click(".pm-table .xsel", "список-вибору", 500, nth=1); pg.keyboard.press("Escape")
    go("/system", "система")
    go("/audit", "журнал")
    go("/profile", "профіль")
    if not mobile:
        pg.goto(B + "/orders"); pg.wait_for_timeout(1200); pg.keyboard.press("Control+k"); shot("палітра-команд", 600); pg.keyboard.press("Escape")
        t = time.time(); r = pg.evaluate("fetch('/api/orders/export.csv').then(r=>r.text()).then(t=>t.length)"); say(f"    експорт CSV усіх замовлень: {time.time() - t:.2f} с, {r // 1024} КБ")
    b.close()


with sync_playwright() as p:
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    if which in ("both", "pc"):
        run(p, "pc", {"width": 1440, "height": 900}, False)
    if which in ("both", "mob"):
        run(p, "mob", {"width": 390, "height": 844}, True)
open(f"{OUT}/log.txt", "w").write("\n".join(LOG))
