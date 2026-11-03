"""Варіант 4 — «Моно-контраст» (Web Design FR): чорне на білому, вузька колонка іконок з підписами, чорні акцентні блоки, пігулки."""
from common import *

CSS = """
.v4{--ink:#000;--mut:#76766F;--line:#E6E6E2;--bg:#E9E9E6;--soft:#F4F4F1;font:400 14px/1.45 'Golos',sans-serif;color:#111;background:var(--bg);width:100%;height:100%;display:flex;gap:14px;padding:14px}
.v4 .rail{width:92px;background:#fff;border-radius:28px;padding:14px 8px;display:flex;flex-direction:column;align-items:center;gap:2px}
.v4 .rail .lg{width:44px;height:44px;border-radius:15px;background:#000;color:#fff;display:grid;place-items:center;font:700 16px 'Unbounded';margin-bottom:10px}
.v4 .ri{width:76px;display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 0;border-radius:16px;font-size:10.5px;color:#55554F;position:relative;text-align:center;line-height:1.1}
.v4 .ri.on{background:#000;color:#fff}.v4 .ri em{position:absolute;top:3px;right:14px;font-style:normal;font-size:9.5px;font-weight:700;background:#FF4D2E;color:#fff;border-radius:99px;padding:0 5px;line-height:15px}
.v4 .rail hr{width:36px;border:0;border-top:1px solid var(--line);margin:4px 0}
.v4 .rail .me{margin-top:auto;width:44px;height:44px;border-radius:50%;background:#D9D2C8;display:grid;place-items:center;font-weight:700;font-size:13px}
.v4 .main{flex:1;min-width:0;display:flex;flex-direction:column;gap:14px}
.v4 .tb{display:flex;align-items:center;gap:10px}
.v4 h1{font:600 40px/1 'Unbounded',sans-serif;letter-spacing:-.04em}
.v4 .pill{display:inline-flex;align-items:center;gap:7px;height:40px;padding:0 16px;border-radius:99px;background:#fff;font-size:13.5px;font-weight:500;white-space:nowrap}
.v4 .pill.k{background:#000;color:#fff}.v4 .pill.o{background:none;border:1px solid #CFCFCA}
.v4 .circ{width:40px;height:40px;border-radius:50%;background:#fff;display:grid;place-items:center}.v4 .circ.k{background:#000;color:#fff}
.v4 .tb .r{margin-left:auto;display:flex;gap:8px;align-items:center}
.v4 .seg{display:inline-flex;background:#fff;border-radius:99px;padding:4px;gap:2px}.v4 .seg span{padding:7px 14px;border-radius:99px;font-size:13px;color:#55554F;white-space:nowrap}
.v4 .seg span.on{background:#000;color:#fff}
.v4 .pn{background:#fff;border-radius:28px;padding:20px}.v4 .pn.k{background:#000;color:#fff}
.v4 .pn h3{font:600 15px 'Unbounded';letter-spacing:-.02em;display:flex;align-items:center;gap:10px}.v4 .pn h3 .r{margin-left:auto;display:flex;gap:6px}
.v4 .pn h3 .r{font:400 13px "Golos",sans-serif;letter-spacing:0}.v4 .pn h3 small{font:400 12.5px 'Golos';color:var(--mut);letter-spacing:0}
.v4 .grid{display:grid;gap:14px}
.v4 .big{font:500 54px/1 'Unbounded';letter-spacing:-.05em}.v4 .big small{font-size:20px;letter-spacing:-.02em}
.v4 .mut{color:var(--mut)}.v4 .k .mut{color:#9A9A93}
.v4 table{width:100%;border-collapse:separate;border-spacing:0 4px}.v4 th{font-size:12px;color:var(--mut);font-weight:400;text-align:left;padding:4px 12px}
.v4 td{padding:10px 12px;font-size:13.5px;white-space:nowrap;background:var(--soft)}
.v4 td:first-child{border-radius:16px 0 0 16px}.v4 td:last-child{border-radius:0 16px 16px 0}
.v4 tr.sel td{background:#000;color:#fff}.v4 tr.sel .mut{color:#A3A39C}.v4 tr.sel .st{background:#fff;color:#000}
.v4 .st{display:inline-flex;align-items:center;gap:6px;padding:4px 11px;border-radius:99px;background:#fff;font-size:12px;font-weight:500}
.v4 .st i{width:7px;height:7px;border-radius:50%;background:var(--c)}
.v4 .av{width:32px;height:32px;border-radius:50%;display:grid;place-items:center;font-size:11px;font-weight:700;background:#D9D2C8;flex:none}
.v4 .sum{text-align:right;font-weight:600}
.v4 .bars{display:flex;align-items:flex-end;gap:7px;height:96px;margin-top:14px}.v4 .bars i{flex:1;background:#2A2A27;border-radius:8px}.v4 .bars i.on{background:#fff}
.v4 .prog{height:8px;border-radius:99px;background:#2A2A27;overflow:hidden;margin:14px 0 8px}.v4 .prog i{display:block;height:100%;width:62%;background:#fff;border-radius:99px}
/* картка */
.v4 .steps{display:flex;align-items:center;gap:6px}.v4 .steps span{display:inline-flex;align-items:center;gap:7px;height:36px;padding:0 14px;border-radius:99px;background:#fff;font-size:13px;color:#55554F}
.v4 .steps span.done{background:#DCDCD7;color:#000}.v4 .steps span.on{background:#000;color:#fff}.v4 .steps .ln{width:16px;height:1px;background:#BDBDB7;padding:0}
.v4 .name{font:600 30px/1.1 'Unbounded';letter-spacing:-.04em;margin:10px 0 6px}
.v4 .kpi4{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:16px}.v4 .kpi4 div{background:var(--soft);border-radius:18px;padding:12px}
.v4 .kpi4 b{display:block;white-space:nowrap;font:600 18px 'Unbounded';letter-spacing:-.03em}.v4 .kpi4 span{font-size:12px;color:var(--mut)}
.v4 .gd{display:flex;align-items:center;gap:14px;padding:10px;border-radius:20px;background:var(--soft);margin-top:8px}
.v4 .gd .ph{width:58px;height:58px;border-radius:16px;background:radial-gradient(circle at 35% 30%,#555,#000 70%);display:grid;place-items:center;color:#fff}
.v4 .gd .ph.w{background:radial-gradient(circle at 35% 30%,#fff,#D7D7D2 80%);color:#777}
.v4 .gd b{display:block;font-weight:600}.v4 .gd small{color:var(--mut)}.v4 .gd .q{margin-left:auto;display:flex;align-items:center;gap:10px;background:#fff;border-radius:99px;padding:6px 12px;font-weight:600}
.v4 .gd .p{width:90px;text-align:right;font:600 15px 'Unbounded';letter-spacing:-.03em}
.v4 .kv{display:grid;grid-template-columns:110px 1fr;gap:9px;font-size:13.5px}.v4 .kv span{color:var(--mut)}.v4 .k .kv span{color:#9A9A93}
.v4 .ttn{font:600 18px 'JB',monospace;letter-spacing:.04em;margin:12px 0 4px}
.v4 .acts{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:auto}
.v4 .acts span{display:flex;align-items:center;gap:8px;justify-content:center;height:44px;border-radius:99px;background:#1F1F1D;color:#fff;font-size:13px}
.v4 .acts span.w{background:#fff;color:#000}
.v4 .tl .e{display:grid;grid-template-columns:34px 1fr auto;gap:10px;align-items:start;padding:7px 0}
.v4 .tl .e .ic{width:34px;height:34px;border-radius:50%;background:var(--soft);display:grid;place-items:center}
.v4 .tl b{font-weight:600;font-size:13px;display:block}.v4 .tl small{color:var(--mut);font-size:12px}.v4 .tl time{font-size:12px;color:var(--mut)}
/* налаштування */
.v4 .flow{display:flex;align-items:stretch;gap:0}
.v4 .sc{width:172px;background:#fff;border-radius:22px;padding:14px;display:flex;flex-direction:column;gap:8px;position:relative}
.v4 .sc .hd{display:flex;align-items:center;gap:8px}.v4 .sc .hd i{flex:none;width:10px;height:10px;border-radius:50%;background:var(--c)}.v4 .sc .hd b{font-weight:600;font-size:13.5px}
.v4 .sc .hd .i{margin-left:auto;color:#A3A39C}
.v4 .sc .a{display:flex;align-items:center;gap:7px;font-size:12px;color:#33332F;background:var(--soft);border-radius:10px;padding:5px 8px}
.v4 .sc .a.n{background:none;color:#B5B5AE;padding:5px 2px}.v4 .sc.k{background:#000;color:#fff}.v4 .sc.k .a{background:#222;color:#eee}
.v4 .tp{margin-left:auto;font-size:11px;background:#000;color:#fff;border-radius:99px;padding:2px 10px}
.v4 .arrow{width:26px;display:grid;place-items:center;color:#9A9A93}
.v4 .lane{background:rgba(255,255,255,.45);border-radius:28px;padding:16px}
.v4 .lane .lt{display:flex;align-items:center;gap:10px;margin-bottom:12px}.v4 .lane .lt b{font:600 16px 'Unbounded';letter-spacing:-.02em}
/* атрибути */
.v4 .agl .a{display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:18px;margin-bottom:4px}
.v4 .agl .a.on{background:#000;color:#fff}.v4 .agl .a b{font-weight:600;display:block}.v4 .agl .a small{font-size:12px;color:var(--mut)}.v4 .agl .a.on small{color:#A3A39C}
.v4 .agl .a .ic{width:38px;height:38px;border-radius:12px;background:var(--soft);display:grid;place-items:center;color:#000}.v4 .agl .a.on .ic{background:#fff}
.v4 .mx{display:grid;grid-template-columns:150px repeat(3,1fr);gap:8px}
.v4 .mx .h{font-size:12.5px;color:var(--mut);padding:4px 8px}.v4 .mx .rh{display:flex;align-items:center;gap:10px;font-weight:600;padding:0 8px}
.v4 .mx .rh i{width:22px;height:22px;border-radius:50%;background:var(--c);box-shadow:inset 0 0 0 1px rgba(0,0,0,.12)}
.v4 .cell{background:var(--soft);border-radius:18px;padding:12px 14px;display:flex;flex-direction:column;gap:2px;min-height:86px}
.v4 .cell b{font:600 24px 'Unbounded';letter-spacing:-.04em}.v4 .cell small{font-size:12px;color:var(--mut)}.v4 .cell .p{font-weight:600;font-size:13px;margin-top:auto}
.v4 .cell.k{background:#000;color:#fff}.v4 .cell.k small{color:#A3A39C}.v4 .cell.off{background:none;border:1.5px dashed #CFCFCA;color:#A3A39C;align-items:center;justify-content:center}
.v4 .cell.z b{color:#FF4D2E}
.v4 .vchips{display:flex;gap:8px;flex-wrap:wrap}.v4 .vchips span{display:inline-flex;align-items:center;gap:8px;padding:6px 14px 6px 6px;border-radius:99px;background:var(--soft);font-weight:500}
.v4 .vchips span i{width:26px;height:26px;border-radius:50%;background:var(--c);box-shadow:inset 0 0 0 1px rgba(0,0,0,.12)}
"""

SHORT = {"home": "Головна", "leads": "Ліди", "orders": "Замовл.", "board": "Дошка", "customers": "Покупці", "products": "Товари", "warehouse": "Склад",
         "purchases": "Закупівлі", "payments": "Оплати", "stats": "Статист.", "reports": "Звіти", "audit": "Журнал", "settings": "Налашт.", "system": "Система"}


def rail(active):
    out = '<span class="lg">m</span>'
    for gi, (g, items) in enumerate(NAV):
        if gi:
            out += "<hr>"
        for k, n, i, c in items:
            out += f'<span class="ri {"on" if k == active else ""}">{ic(i, 19)}{SHORT[k]}{"<em>5</em>" if k == "leads" else ""}</span>'
    return f'<aside class="rail">{out}<span class="me">ОЛ</span></aside>'


def tb(title, mid="", right=""):
    return f"""<div class="tb"><h1>{title}</h1>{mid}<div class="r">{right}<span class="pill">{ic("search", 16)}Пошук<span class="mut" style="font-size:12px">Ctrl K</span></span>
<span class="circ">{ic("bell", 17)}</span><span class="circ k">{ic("plus", 18, 2.2)}</span></div></div>"""


def orders():
    rows = ""
    for n, o in enumerate(ORDERS[:8]):
        rows += f"""<tr class="{"sel" if n == 0 else ""}"><td class="mut">{o[0]}</td><td><div style="display:flex;gap:10px;align-items:center"><span class="av">{initials(o[1])}</span><span>{o[1]}<div class="mut" style="font-size:12px">{o[2]}</div></span></div></td>
<td>{o[3]}</td><td>{pill(o[6])}</td><td class="mut">{o[7]}</td><td class="mut">{o[8]}</td><td class="sum">{o[5]} ₴</td></tr>"""
    seg = '<span class="seg" style="margin-left:18px"><span class="on">Сьогодні</span><span>Тиждень</span><span>Місяць</span></span>'
    hours = [3, 5, 4, 8, 6, 9, 7, 5, 6, 4]
    bars = "".join(f'<i class="{"on" if n == 5 else ""}" style="height:{h * 10}%"></i>' for n, h in enumerate(hours))
    top = f"""<div class="grid" style="grid-template-columns:1fr 1fr 1.3fr">
<div class="pn"><h3>Апрув<span class="r"><span class="circ" style="width:32px;height:32px;background:var(--soft)">{ic("arrow-up-right", 15)}</span></span></h3>
<div class="big" style="margin-top:16px">68,4<small>%</small></div><div class="mut" style="margin-top:6px">↑ 4,2% до минулого тижня · 31 підтверджено</div></div>
<div class="pn k"><h3>Відправка сьогодні</h3><div class="big" style="margin-top:16px">23<small> / 37</small></div><div class="prog"><i></i></div>
<div class="mut">14 ще без ТТН · реєстр о 17:00</div></div>
<div class="pn k"><h3>Заявки по годинах<small style="color:#9A9A93">· пік о 14:00</small></h3><div class="bars">{bars}</div></div></div>"""
    table = f"""<div class="pn" style="flex:1;overflow:hidden"><h3>Замовлення<small>· 248 за жовтень</small><span class="r"><span class="seg" style="background:var(--soft)">
<span class="on">Усі</span><span>Підтверджено</span><span>Комплектується</span><span>Відправлено</span><span>Відмова</span></span><span class="pill o">{ic("funnel", 15)}Фільтри</span></span></h3>
<table style="margin-top:8px"><thead><tr><th>№</th><th>Покупець</th><th>Товар</th><th>Статус</th><th>Доставка</th><th>Джерело</th><th style="text-align:right">Сума</th></tr></thead><tbody>{rows}</tbody></table></div>"""
    return f'<div class="v4">{rail("orders")}<main class="main">{tb("Замовлення", seg)}{top}{table}</main></div>'


def card():
    o = ORDER
    steps = '<span class="done">Новий</span><span class="ln"></span><span class="on">' + ic("check", 14, 2.4) + 'Підтверджено</span><span class="ln"></span><span>Комплектується</span><span class="ln"></span><span>Відправлено</span><span class="ln"></span><span>Отримано</span>'
    kp = "".join(f"<div><b>{b}</b><span>{a}</span></div>" for a, b in CUSTOMER)
    goods = "".join(f"""<div class="gd" style="{"margin-left:36px" if up else ""}"><span class="ph {"w" if up else ""}">{ic("link" if up else "zap", 20)}</span><span><b>{nm}</b><small>{var} · {sku}</small></span>
<span class="q">{ic("plus", 13) if False else "−"}<span>{q}</span>+</span><span class="p">{s} ₴</span></div>""" for nm, var, sku, q, p, s, up in o["items"])
    tl = "".join(f'<div class="e"><span class="ic">{ic(i, 15)}</span><span><b>{t}</b><small>{d}</small></span><time>{tm}</time></div>' for tm, t, d, i in TIMELINE[1:])
    body = f"""<div class="tb"><span class="circ">{ic("arrow-left", 18)}</span><span class="steps">{steps}</span><div class="r"><span class="pill">{ic("printer", 16)}Друк{ic("chevron-down", 14)}</span><span class="pill">{ic("receipt", 16)}Чек</span></div></div>
<div class="grid" style="grid-template-columns:1.25fr 1fr 360px;flex:1;min-height:0">
<div style="display:flex;flex-direction:column;gap:14px;min-height:0"><div class="pn"><span class="mut">Замовлення №1482 · 29.10.2026, 14:32 · Instagram</span>
<div class="name">{o["name"]}</div><div style="display:flex;gap:8px;align-items:center"><span class="pill" style="background:var(--soft)">{ic("phone", 15)}{o["phone"]}</span>
<span class="circ" style="background:var(--soft)">{ic("message-circle", 16)}</span><span class="circ" style="background:var(--soft)">{ic("message-square", 16)}</span></div><div class="kpi4">{kp}</div></div>
<div class="pn" style="flex:1"><h3>Товари<span class="r"><span class="pill o" style="height:34px">{ic("plus", 14)}Товар</span><span class="pill o" style="height:34px">{ic("sparkles", 14)}Допродаж</span></span></h3>{goods}
<div style="margin-top:14px;padding:14px 16px;border-radius:20px;border:1.5px dashed #CFCFCA;display:flex;align-items:center;gap:12px"><span class="circ k" style="width:34px;height:34px">{ic("sparkles", 15)}</span><span><b style="font-weight:600">Часто беруть разом</b><div class="mut" style="font-size:12.5px">Чохол для павербанка · 249 ₴ — додати одним натиском</div></span><span class="pill k" style="margin-left:auto;height:34px">{ic("plus", 14)}Додати</span></div>
<div class="kv" style="margin-top:16px;grid-template-columns:1fr auto"><span>Товари</span><b style="font-weight:500">1 797 ₴</b><span>Знижка</span><b style="font-weight:500">0 ₴</b><span>Собівартість · прибуток</span><b style="font-weight:500">1 020 ₴ · 777 ₴</b></div></div></div>
<div style="display:flex;flex-direction:column;gap:14px;min-height:0"><div class="pn"><h3>Деталі</h3><div class="kv" style="margin-top:12px"><span>Менеджер</span><b style="font-weight:500">Олена Литвин</b>
<span>Відділ</span><b style="font-weight:500">Інтернет-магазин</b><span>Юрособа</span><b style="font-weight:500">ФОП Максимчук О. В.</b><span>Позначки</span><span style="color:#000">VIP · Подарунок</span>
<span>Коментар</span><b style="font-weight:500">Зателефонувати після 18:00</b></div></div>
<div class="pn" style="flex:1"><h3>Доставка<small>· Нова Пошта</small></h3><div class="ttn">2045 0913 9983 65</div><div class="mut" style="margin-bottom:12px">Прямує до відділення · очікується 30.10</div>
<div class="kv"><span>Куди</span><b style="font-weight:500">Київ, відділення №12</b><span>Платник</span><b style="font-weight:500">Отримувач · 85 ₴</b><span>Ключ НП</span><b style="font-weight:500">ФОП Максимчук</b></div>
<div style="display:flex;gap:6px;margin-top:18px">{"".join(f'<span style="flex:1;height:8px;border-radius:99px;background:{c}"></span>' for c in ["#000","#000","#000","#DCDCD7","#DCDCD7"])}</div>
<div style="display:flex;justify-content:space-between;font-size:12px;margin-top:6px" class="mut"><span>Створено</span><span>У дорозі</span><span>Отримано</span></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:16px"><span class="pill" style="background:var(--soft);justify-content:center">{ic("refresh-cw", 15)}Оновити</span><span class="pill" style="background:var(--soft);justify-content:center">{ic("copy", 15)}Копіювати ТТН</span></div></div></div>
<div class="pn k" style="display:flex;flex-direction:column"><span class="mut">До сплати при отриманні</span><div class="big" style="margin:10px 0 14px">1 797<small> ₴</small></div>
<div class="kv"><span>Передоплата</span><b style="font-weight:500">200 ₴ · Monobank</b><span>Оплата</span><b style="font-weight:500">Контроль оплати НП</b><span>Чек</span><b style="font-weight:500">Передоплата ✓</b></div>
<div class="tl" style="margin-top:16px;border-top:1px solid #222;padding-top:10px">{tl.replace('class="ic"', 'class="ic" style="background:#1F1F1D"').replace('<small>', '<small style="color:#9A9A93">')}</div>
<div class="acts"><span>{ic("tag", 16)}Наклейка</span><span class="w">{ic("truck", 16)}Створити ТТН</span></div></div></div>"""
    return f'<div class="v4">{rail("orders")}<main class="main">{body}</main></div>'


def settings():
    tabs = "".join(f'<span class="{"on" if n == "Статуси" else ""}">{n}</span>' for n, i in SETTINGS[:9]) + '<span>Ще 3 ▾</span>'

    def card(code, stock, chk, sms, dark=False):
        a = lambda i, v: f'<span class="a n">{ic(i, 13)}—</span>' if v == "—" else f'<span class="a">{ic(i, 13)}{v}</span>'
        n, c = ST[code]
        return f'<div class="sc {"k" if dark else ""}"><div class="hd" style="--c:{c}"><i></i><b>{n}</b>{ic("ellipsis", 15)}</div>{a("boxes", stock)}{a("receipt", chk)}{a("message-square", sms)}</div>'

    def lane(sec, title, desc):
        items = [r for r in STATUS_ROWS if r[1] == sec]
        flow = f'<span class="arrow">{ic("chevron-right", 18)}</span>'.join(card(c, st, ch, sm, dark=(c == "sent")) for c, s, st, ch, sm in items)
        return f'<div class="lane"><div class="lt"><b>{title}</b><span class="mut">{desc}</span><span style="margin-left:auto" class="pill o">{ic("plus", 15)}Статус</span></div><div class="flow">{flow}</div></div>'
    body = f"""{tb("Налаштування", "", f'<span class="pill o">{ic("undo-2", 15)}Скасувати</span><span class="pill k">{ic("check", 15)}Зберегти</span>')}
<div><span class="seg">{tabs}</span></div>
{lane("Ліди", "Ліди", "4 статуси · дзвінок і підтвердження")}{lane("Замовлення", "Замовлення", "6 статусів · кожна картка — що CRM зробить сама")}
<div class="lane"><div class="lt"><b>Юрособи й каси</b><span class="mut">замовлення бере касу Checkbox і ключ НП зі своєї юрособи</span><span style="margin-left:auto" class="pill o">{ic("plus", 15)}Юрособа</span></div>
<div class="flow" style="gap:12px">{"".join(f'<div class="sc" style="width:330px"><div class="hd" style="--c:#000"><b>{n}</b>{"<span class=tp>типова</span>" if d else ""}</div><span class="a">{ic("receipt", 13)}Каса Checkbox · {k}</span><span class="a">{ic("truck", 13)}Ключ НП · {np}</span></div>' for n, k, np, d in [("ФОП Максимчук О. В.", "№1, автозміна", "Тульчин", True), ("ФОП Литвин О. С.", "№2", "Київ", False), ("ТОВ «Мдми Трейд»", "№3, тестова", "Київ", False)])}</div></div>
"""
    return f'<div class="v4">{rail("settings")}<main class="main">{body}</main></div>'


def attributes():
    gl = "".join(f'<div class="a {"on" if n == 0 else ""}"><span class="ic">{ic(i, 18)}</span><span><b>{g}</b><small>{len(v)} значення · {u}</small></span></div>'
                 for n, (g, i, t, v, u) in enumerate(ATTR_GROUPS))
    vch = "".join(f'<span style="--c:{c}"><i></i>{n}</span>' for n, c in ATTR_GROUPS[0][3])
    caps = ["10 000", "20 000", "30 000"]
    mx = '<span></span>' + "".join(f'<span class="h">{c} мА·год</span>' for c in caps)
    for col, c in [("Чорний", "#151515"), ("Білий", "#F4F4F2"), ("Синій", "#2F5BEA"), ("Рожевий", "#F2A7C3")]:
        mx += f'<span class="rh" style="--c:{c}"><i></i>{col}</span>'
        for cap in caps:
            v = next((x for x in VARIANTS if x[0] == col and x[2] == cap), None)
            if not v:
                mx += f'<span class="cell off">{ic("plus", 18)}Додати варіант</span>'
            else:
                k = "k" if (col, cap) == ("Чорний", "20 000") else ""
                z = "z" if v[5] == 0 else ""
                mx += f'<span class="cell {k} {z}"><b>{v[5]} шт</b><small>{v[3]} · резерв {v[6]}</small><span class="p">{v[4]} ₴</span></span>'
    body = f"""{tb("Атрибути", '<span class="seg" style="margin-left:18px"><span>Товари</span><span>Категорії</span><span>Бренди</span><span class="on">Атрибути</span></span>')}
<div class="grid" style="grid-template-columns:300px 1fr;flex:1;min-height:0"><div class="pn agl"><h3 style="margin-bottom:12px">Групи<span class="r"><span class="circ k" style="width:32px;height:32px">{ic("plus", 15)}</span></span></h3>{gl}</div>
<div style="display:flex;flex-direction:column;gap:14px;min-height:0"><div class="pn"><h3>Колір<small>· кольорові плашки · 32 товари</small></h3><div class="vchips" style="margin-top:14px">{vch}<span style="padding:6px 14px;background:none;border:1.5px dashed #CFCFCA">{ic("plus", 14)} Значення</span></div></div>
<div class="pn" style="flex:1"><h3>Павербанк Volt<small>· колір × ємність · 6 із 9 комбінацій</small><span class="r"><span class="pill o" style="height:34px">{ic("layers", 14)}Згенерувати решту</span></span></h3>
<div class="mx" style="margin-top:14px">{mx}</div></div></div></div>"""
    return f'<div class="v4">{rail("products")}<main class="main">{body}</main></div>'


def build():
    return page("Варіант 4 — Моно-контраст", CSS, [
        ("1-menu", "Колонка іконок з підписами + замовлення", orders(), None, None), ("2-card", "Картка замовлення з кроками статусу", card(), None, None),
        ("3-settings", "Налаштування — статуси як конвеєр", settings(), None, None), ("4-attrs", "Атрибути — матриця варіантів", attributes(), None, None)])
