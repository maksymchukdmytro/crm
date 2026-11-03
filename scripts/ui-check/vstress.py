"""Стрес нових виглядів списку на базі ~2 650 замовлень: швидкість, догрузка, J/K, дії карток, фільтри, ширини екрана."""
import json, re, time
from playwright.sync_api import sync_playwright
B="http://localhost:8078"; O="/tmp/claude-0/vs"
import os; os.makedirs(O,exist_ok=True)
def mocks(pg):
    j=lambda r,d: r.fulfill(status=200,content_type="application/json",body=json.dumps(d,ensure_ascii=False))
    pg.route(re.compile(r".*/api/np/cities.*"), lambda r: j(r,{"ok":True,"items":[{"ref":"CK","name":"Київ","label":"Київ"}]}))
    pg.route(re.compile(r".*/api/np/warehouses.*"), lambda r: j(r,{"ok":True,"items":[{"ref":"W1","name":"Відділення №1","label":"Відділення №1","max_weight":30,"kind":"branch"}]}))
CHK="""()=>{const o={x:document.documentElement.scrollWidth-innerWidth};const c=[];
for(const el of document.querySelectorAll('.ocd *, .ib-item *, .list-head *, .list-tabsrow *, .oc-embed-foot *')){const r=el.getBoundingClientRect();if(!r.width||r.bottom<0||r.top>innerHeight)continue;
const p=el.closest('.ocd, .ib-item, .list-head, .list-tabsrow, .oc-embed-foot').getBoundingClientRect(); if(r.right>p.right+1||r.left<p.left-1){c.push((el.className||el.tagName)+'');}}
o.out=[...new Set(c)].slice(0,5);return o;}"""
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1243/chrome-linux64/chrome",args=["--no-sandbox"])
    for W,H in [(1024,768),(1280,800),(1920,1080)]:
        ctx=b.new_context(viewport={"width":W,"height":H})
        ctx.add_init_script("window.__lt=[];new PerformanceObserver(l=>l.getEntries().forEach(e=>window.__lt.push(Math.round(e.duration)))).observe({entryTypes:['longtask']});")
        pg=ctx.new_page(); errs=[]; bad=[]
        pg.on("pageerror",lambda e: errs.append(str(e)[:200]))
        pg.on("console", lambda m: m.type=="error" and "401" not in m.text and errs.append("console: "+m.text[:160]))
        pg.on("response", lambda r: ("/api/" in r.url and r.status>=400 and r.status!=401) and bad.append(f"{r.status} {r.url.split('8078')[1][:70]}"))
        pg.on("dialog", lambda d: d.accept()); mocks(pg)
        pg.goto(B+"/login"); pg.wait_for_timeout(500)
        pg.locator("input").nth(0).fill("admin"); pg.locator("input[type=password]").fill("admin12345"); pg.keyboard.press("Enter"); pg.wait_for_timeout(1200)
        def rep(tag):
            c=pg.evaluate(CHK); pg.screenshot(path=f"{O}/{W}-{tag}.png")
            print(f"[{W}] {tag}: прокрутка вшир {c['x']}, вилазить {c['out']}, JS {errs[:2]}, API {sorted(set(bad))[:3]}"); errs.clear(); bad.clear()
        for v in ["table","cards","inbox"]:
            pg.evaluate(f"localStorage.setItem('crm-orders-view','{v}')")
            t=time.time(); pg.goto(B+"/orders"); pg.wait_for_selector(".dense-row, .ocd:not(.sk), .ib-item:not(.sk)",timeout=15000); dt=time.time()-t
            if v=="inbox": pg.wait_for_selector(".oc-embed .oc-cust",timeout=15000); dt2=time.time()-t
            print(f"[{W}] {v}: перші дані за {dt:.2f} с" + (f", картка праворуч за {dt2:.2f} с" if v=='inbox' else ""))
            pg.wait_for_timeout(800); rep(v)
        # картки: прокрутка з догрузкою
        pg.evaluate("localStorage.setItem('crm-orders-view','cards')"); pg.goto(B+"/orders"); pg.wait_for_selector(".ocd:not(.sk)")
        pg.evaluate("window.__lt=[]"); t=time.time()
        for _ in range(40):
            pg.evaluate("document.querySelector('.ocd-wrap').scrollBy(0,3000)"); pg.wait_for_timeout(150)
        n=pg.evaluate("document.querySelectorAll('.ocd').length"); lt=pg.evaluate("window.__lt")
        print(f"[{W}] картки: після прокрутки {n} карток за {time.time()-t:.1f} с, найдовша задача {max(lt or [0])} мс, задач >50 мс: {len(lt)}")
        t=time.time(); pg.locator(".list-tabs button", has_text="Завершений").first.click(); pg.wait_for_timeout(300)
        pg.wait_for_selector(".ocd:not(.sk)"); print(f"[{W}] картки: перемкнути вкладку з {n} карток — {time.time()-t:.2f} с")
        rep("cards-scrolled")
        # скринька: J ×15
        pg.evaluate("localStorage.setItem('crm-orders-view','inbox')"); pg.goto(B+"/orders"); pg.wait_for_selector(".oc-embed .oc-cust",timeout=15000)
        ts=[]
        for i in range(40):
            prev=pg.url; t=time.time(); pg.keyboard.press("j")
            pg.wait_for_function("u=>location.href!==u",arg=prev,timeout=5000); nid=pg.url.split('/orders/')[1].split('?')[0]
            pg.wait_for_function("n=>{const b=document.querySelector('.oc-emb-t b');return b&&b.textContent==='№'+n&&document.querySelector('.oc-embed .oc-cust')}",arg=nid,timeout=10000); ts.append(time.time()-t)
        on=pg.evaluate("(()=>{const e=document.querySelector('.ib-item.on');if(!e)return 'нема';const r=e.getBoundingClientRect(),l=document.querySelector('.ib-list').getBoundingClientRect();return r.top>=l.top&&r.bottom<=l.bottom?'видно':'за краєм'})()")
        print(f"[{W}] скринька J×40: середньо {sum(ts)/len(ts):.2f} с, макс {max(ts):.2f} с; вибраний у списку — {on}")
        rep("inbox-after-j")
        # редагування й одразу перехід (дозбереження)
        pg.locator(".oc-embed textarea, .oc-embed input[placeholder*='оментар']").first.fill("стрес-коментар "+str(W))
        oid=pg.url.split("/orders/")[1].split("?")[0]; pg.keyboard.press("Escape"); pg.locator(".ib-item").nth(0).click(); pg.wait_for_timeout(2500)
        saved=pg.evaluate(f"fetch('/api/orders/{oid}').then(r=>r.json()).then(o=>JSON.stringify(o).includes('стрес-коментар {W}'))")
        print(f"[{W}] скринька: правка №{oid} і миттєвий перехід — збережено: {saved}")
        # несортовані: прийняти й далі
        pg.locator(".list-tabs button").first.click(); pg.wait_for_timeout(2000)
        cnt0=pg.locator(".ib-item:not(.sk)").count(); cur=pg.url
        if pg.locator(".oc-embed-foot .btn.primary", has_text="Прийняти й далі").count():
            pg.locator(".oc-embed-foot .btn.primary").click(); pg.wait_for_timeout(2500)
            print(f"[{W}] «Прийняти й далі»: було {cnt0} несортованих у списку, стало {pg.locator('.ib-item:not(.sk)').count()}, відкрито інше: {pg.url!=cur}")
        rep("inbox-accept")
        # фільтри: увімкнути доставку через панель, побачити чип праворуч
        pg.goto(B+"/orders"); pg.wait_for_timeout(1500)
        pg.locator(".lh-filter").click(); pg.wait_for_timeout(300)
        pg.locator(".chips-row .fchip", has_text="Доставка").first.click(); pg.wait_for_timeout(300)
        pg.locator(".chip-pop .pop-item, .chip-pop button", has_text="Нова").first.click(); pg.wait_for_timeout(300)
        pg.keyboard.press("Escape"); pg.locator(".lh-filter").click(); pg.wait_for_timeout(1500)
        print(f"[{W}] фільтр: чипів праворуч від вкладок {pg.locator('.lh-active .fchip').count()}, крапка на кнопці {pg.locator('.lh-filter .dot').count()}")
        rep("filter-active")
        # картки: кнопка ТТН відкриває вікно ТТН
        pg.goto(B+"/orders"); pg.evaluate("localStorage.setItem('crm-orders-view','cards')"); pg.goto(B+"/orders?status=2"); pg.wait_for_timeout(2500)
        if pg.locator(".ocd-go.s", has_text="ТТН").count():
            pg.locator(".ocd-go.s", has_text="ТТН").first.click(); pg.wait_for_timeout(2500)
            print(f"[{W}] картка «ТТН»: вікно ТТН відкрилось — {pg.locator('.tt-win, .ttn-dialog, [aria-label*=ТТН][role=dialog]').count()>0 or pg.locator('text=Нова ТТН').count()>0}")
            rep("cards-ttn"); pg.keyboard.press("Escape"); pg.wait_for_timeout(300); pg.keyboard.press("Escape")
        # «/» фокусує пошук і шукає
        pg.goto(B+"/orders"); pg.wait_for_timeout(1500); pg.keyboard.press("/"); pg.keyboard.type("Коваленко"); t=time.time(); pg.wait_for_timeout(1500)
        print(f"[{W}] пошук «/»: фокус у полі {pg.evaluate('document.activeElement.type')=='search'}, знайдено {pg.locator('.ocd:not(.sk)').count()} карток")
        pg.evaluate("localStorage.setItem('crm-orders-view','table')")
        ctx.close()
    b.close()
