"""Варіант 3 — «Документ» (Notion / ofsp_ce / Synapse): спокійний білий, лічильники в меню, картка як сторінка з властивостями."""
from common import *
import mobile

CSS = """
.v3{--ink:#1F1F1C;--mut:#7A7975;--line:#ECECE9;--side:#F7F7F5;--acc:#2E6BE6;font:400 14px/1.5 'Onest',sans-serif;color:var(--ink);background:#fff;width:100%;height:100%;display:flex;position:relative}
.v3 .side{width:256px;background:var(--side);border-right:1px solid var(--line);padding:12px 10px;display:flex;flex-direction:column;gap:2px}
.v3 .ws{display:flex;align-items:center;gap:9px;padding:6px 8px;border-radius:8px;font-weight:600;margin-bottom:6px}
.v3 .ws .lg{width:26px;height:26px;border-radius:7px;background:#1F1F1C;color:#fff;display:grid;place-items:center;font-size:13px;font-weight:700}
.v3 .ws .i:last-child{margin-left:auto;color:var(--mut)}
.v3 .it{display:flex;align-items:center;gap:10px;height:31px;padding:0 8px;border-radius:7px;color:#45443F;font-size:13.5px}
.v3 .it .i{color:#8F8E89}.v3 .it.on{background:#fff;color:var(--ink);font-weight:500;box-shadow:0 0 0 1px var(--line),0 1px 2px rgba(0,0,0,.04)}.v3 .it.on .i{color:var(--ink)}
.v3 .it em{margin-left:auto;font-style:normal;font-size:12px;color:#A3A29D}.v3 .it em.b{color:#fff;background:var(--acc);border-radius:99px;padding:0 7px;font-weight:600}
.v3 .gl{font-size:12px;color:#A3A29D;padding:14px 8px 4px;display:flex;align-items:center}.v3 .gl .i{margin-left:auto}
.v3 .fav i{width:9px;height:9px;border-radius:3px;background:var(--c)}
.v3 .sfoot{margin-top:auto;display:flex;align-items:center;gap:9px;padding:8px;border-top:1px solid var(--line)}
.v3 .sfoot .av{width:28px;height:28px;border-radius:50%;background:#E8D5C4;display:grid;place-items:center;font-size:11px;font-weight:600}
.v3 .sfoot small{display:block;color:var(--mut);font-size:11.5px;line-height:1.2}
.v3 .main{flex:1;min-width:0;display:flex;flex-direction:column}
.v3 .topb{height:52px;display:flex;align-items:center;gap:10px;padding:0 24px;border-bottom:1px solid var(--line)}
.v3 .sbox{flex:1;max-width:520px;display:flex;align-items:center;gap:8px;height:34px;padding:0 12px;border-radius:8px;background:var(--side);color:#A3A29D;font-size:13px}
.v3 .sbox kbd{margin-left:auto;font:500 11px 'Onest';border:1px solid var(--line);background:#fff;border-radius:5px;padding:0 5px;color:var(--mut)}
.v3 .topb .r{margin-left:auto;display:flex;align-items:center;gap:14px;color:var(--mut)}
.v3 .btn{display:inline-flex;align-items:center;gap:6px;height:32px;padding:0 12px;border-radius:8px;border:1px solid var(--line);font-size:13px;font-weight:500;background:#fff;white-space:nowrap;color:var(--ink)}
.v3 .btn.p{background:var(--acc);color:#fff;border-color:var(--acc)}.v3 .btn.k{background:#1F1F1C;color:#fff;border-color:#1F1F1C}
.v3 .crumb{font-size:12.5px;color:var(--mut);display:flex;align-items:center;gap:6px}
.v3 .pg{padding:22px 40px 0;display:flex;flex-direction:column;gap:14px;min-height:0;flex:1}
.v3 h1{font-size:30px;font-weight:600;letter-spacing:-.025em;line-height:1.15}
.v3 .views{display:flex;align-items:center;gap:20px;border-bottom:1px solid var(--line)}
.v3 .views span{display:inline-flex;align-items:center;gap:7px;padding:9px 0;font-size:13.5px;color:var(--mut);border-bottom:2px solid transparent;margin-bottom:-1px}
.v3 .views .r .btn{padding:0 12px;border:1px solid var(--line);margin:0;color:var(--ink)}.v3 .views .r .btn.p{color:#fff;border-color:var(--acc)}
.v3 .views span.on{color:var(--ink);border-color:var(--ink);font-weight:500}.v3 .views .r{margin-left:auto;display:flex;gap:8px;padding-bottom:8px}
.v3 .kb{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;flex:1;min-height:0}
.v3 .col{background:#FAFAF8;border-radius:12px;padding:10px;display:flex;flex-direction:column;gap:8px;overflow:hidden}
.v3 .ch{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:500;padding:2px 4px 4px}
.v3 .ch i{width:8px;height:8px;border-radius:50%;background:var(--c)}.v3 .ch em{font-style:normal;color:var(--mut);font-weight:400;background:#EFEFEC;border-radius:6px;padding:0 6px;font-size:12px}
.v3 .ch .r{margin-left:auto;color:#A3A29D;display:flex;gap:6px}
.v3 .kc{background:#fff;border:1px solid var(--line);border-radius:10px;padding:11px 12px;display:flex;flex-direction:column;gap:7px;box-shadow:0 1px 2px rgba(0,0,0,.03)}
.v3 .kc .id{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--mut)}.v3 .kc .id .i:last-child{margin-left:auto}
.v3 .kc b{font-weight:600;font-size:14px}.v3 .kc .pr{font-size:13px;color:#45443F}
.v3 .kc .ft{display:flex;align-items:center;gap:10px;font-size:12px;color:var(--mut)}.v3 .kc .ft .s{margin-left:auto;color:var(--ink);font-weight:600;font-size:13px}
.v3 .tg{display:inline-flex;align-items:center;gap:5px;font-size:11.5px;padding:1px 7px;border-radius:5px;background:var(--bg,#F1F1EF);color:var(--fg,#55544F)}
.v3 .late{color:#D9480F}.v3 .add{display:flex;align-items:center;gap:6px;color:#A3A29D;font-size:13px;padding:6px 4px}
/* сторінка замовлення */
.v3 .doc{display:grid;grid-template-columns:1fr 330px;flex:1;min-height:0}
.v3 .dl{padding:22px 40px 0;overflow:hidden;display:flex;flex-direction:column;gap:14px}
.v3 .props{display:grid;grid-template-columns:120px 1.15fr 120px 1fr;gap:8px 12px;font-size:13.5px;align-items:center}
.v3 .props .k{display:flex;align-items:center;gap:8px;color:var(--mut)}
.v3 .st{display:inline-flex;align-items:center;gap:6px;padding:2px 9px;border-radius:6px;font-size:12.5px;font-weight:500;background:color-mix(in srgb,var(--c) 14%,#fff);color:color-mix(in srgb,var(--c) 72%,#000)}
.v3 .st i{width:7px;height:7px;border-radius:50%;background:var(--c)}
.v3 .pp{display:inline-flex;align-items:center;gap:6px}.v3 .pp .av{width:20px;height:20px;border-radius:50%;background:#E8D5C4;font-size:9.5px;display:grid;place-items:center;font-weight:600}
.v3 table{width:100%;border-collapse:collapse;font-size:13.5px}.v3 th{font-weight:400;color:var(--mut);text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);font-size:12.5px}
.v3 td{padding:9px 8px;border-bottom:1px solid var(--line)}.v3 td.r,.v3 th.r{text-align:right}
.v3 .mono{font:500 12.5px 'JB',monospace;color:#55544F}
.v3 .blk{border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.v3 .blk h4{font-size:14px;font-weight:600;display:flex;align-items:center;gap:8px;margin-bottom:10px}.v3 .blk h4 .r{margin-left:auto;display:flex;gap:6px}
.v3 .kv{display:grid;grid-template-columns:120px 1fr;gap:6px 12px;font-size:13.5px}.v3 .kv span{color:var(--mut)}
.v3 .feed{border-left:1px solid var(--line);padding:18px 18px 0;display:flex;flex-direction:column;gap:12px;background:#FCFCFB}
.v3 .feed h4{font-size:13px;font-weight:600;display:flex;gap:8px;align-items:center}
.v3 .ev{display:grid;grid-template-columns:24px 1fr;gap:10px;font-size:13px}.v3 .ev .ic{width:24px;height:24px;border-radius:6px;background:#F1F1EF;display:grid;place-items:center;color:#6A6964}
.v3 .ev small{display:block;color:var(--mut);font-size:12px}.v3 .ev time{color:#A3A29D;font-size:11.5px}
.v3 .cmt{margin-top:auto;border:1px solid var(--line);border-radius:10px;padding:10px 12px;color:#A3A29D;font-size:13px;display:flex;align-items:center;gap:8px;margin-bottom:14px;background:#fff}
.v3 .cmt .i:last-child{margin-left:auto;color:var(--acc)}
/* модальне налаштування */
.v3 .dim{position:absolute;inset:0;background:rgba(15,15,12,.38)}
.v3 .modal{position:absolute;left:110px;right:110px;top:56px;bottom:56px;background:#fff;border-radius:14px;display:flex;overflow:hidden;box-shadow:0 30px 80px -20px rgba(0,0,0,.45)}
.v3 .mside{width:240px;background:var(--side);padding:16px 10px;border-right:1px solid var(--line);display:flex;flex-direction:column;gap:1px}
.v3 .mbody{flex:1;padding:26px 34px;overflow:hidden;display:flex;flex-direction:column;gap:12px}
.v3 .mbody h2{font-size:20px;font-weight:600;letter-spacing:-.01em}.v3 .mbody p.d{color:var(--mut);font-size:13.5px;margin-top:-6px}
.v3 .grp{font-size:12.5px;color:var(--mut);display:flex;align-items:center;gap:8px;margin-top:6px}.v3 .grp b{color:var(--ink);font-weight:600}
.v3 .srow td{padding:7px 8px}.v3 .sel{display:inline-flex;align-items:center;gap:6px;color:#45443F;font-size:13px}.v3 .sel .i{color:#A3A29D}
.v3 .sw{display:inline-block;width:30px;height:18px;border-radius:99px;background:var(--acc);position:relative;vertical-align:middle}
.v3 .sw:after{content:"";position:absolute;right:2px;top:2px;width:14px;height:14px;border-radius:50%;background:#fff}.v3 .sw.off{background:#DAD9D5}.v3 .sw.off:after{right:auto;left:2px}
/* атрибути */
.v3 .peek{position:absolute;right:0;top:52px;bottom:0;width:520px;background:#fff;border-left:1px solid var(--line);box-shadow:-20px 0 40px -20px rgba(0,0,0,.18);padding:18px 24px;display:flex;flex-direction:column;gap:12px}
.v3 .peek .hd{display:flex;align-items:center;gap:10px;color:var(--mut)}.v3 .peek .hd .r{margin-left:auto;display:flex;gap:12px}
.v3 .chipv{display:inline-flex;align-items:center;gap:7px;padding:4px 10px 4px 6px;border-radius:7px;border:1px solid var(--line);font-size:13px;margin:0 6px 6px 0}
.v3 .chipv i{width:16px;height:16px;border-radius:5px;background:var(--c);box-shadow:inset 0 0 0 1px rgba(0,0,0,.1)}
.v3 .stk{display:inline-block;min-width:26px;font-weight:600}.v3 .stk.z{color:#D9480F}.v3 .stk.lo{color:#B7791F}
"""

TAGC = {"Instagram": ("#FCE7F0", "#A3245A"), "Лендинг": ("#EAF1FD", "#1F4FB8"), "Rozetka": ("#E6F6EC", "#14763D"), "Facebook": ("#E9EFFC", "#2348A8"),
        "Prom": ("#F1EAFD", "#5B2DB0"), "TikTok": ("#EFEFEC", "#2A2A27")}


def tag(src):
    bg, fg = TAGC[src]
    return f'<span class="tg" style="--bg:{bg};--fg:{fg}">{src}</span>'


def side(active):
    out = f'<div class="ws"><span class="lg">m</span>mdmy{ic("chevrons-up-down" if False else "chevron-down", 15)}</div>'
    out += f'<div class="it">{ic("search", 17)}Пошук<em>Ctrl K</em></div><div class="it">{ic("plus", 17)}Нове замовлення</div><div class="it">{ic("package-plus", 17)}Новий товар</div>'
    for g, items in NAV:
        out += f'<div class="gl">{g}</div>'
        for k, n, i, c in items:
            cnt = {"leads": '<em class="b">5</em>', "orders": "<em>248</em>", "customers": "<em>1 904</em>", "products": "<em>86</em>"}.get(k, "")
            out += f'<div class="it {"on" if k == active else ""}">{ic(i, 17)}{n}{cnt}</div>'
    out += f'<div class="gl">Збережені фільтри{ic("plus", 14)}</div>'
    for n, c, cnt in [("Чекають ТТН", "#F97316", "9"), ("Передзвонити сьогодні", "#8B5CF6", "6"), ("Rozetka · нові", "#16A34A", "3")]:
        out += f'<div class="it fav" style="--c:{c}"><i></i>{n}<em>{cnt}</em></div>'
    out += '<div class="sfoot"><span class="av">ОЛ</span><span>Олена Литвин<small>Менеджер · Інтернет-магазин</small></span></div>'
    return f'<aside class="side">{out}</aside>'


def topb(right=""):
    return f"""<div class="topb"><span class="sbox">{ic("search", 15)}Шукати замовлення, телефон, ТТН або товар…<kbd>Ctrl K</kbd></span>
<div class="r">{right}{ic("bell", 18)}{ic("message-square", 18)}</div></div>"""


def leads():
    data = {"new": [("1481", "Коваленко Ірина", "Набір кабелів USB-C", "Лендинг", "14:18", "649", ""), ("1473", "Лисенко Юлія", "Кабель Lightning 2 м ×2", "Instagram", "09:41", "398", ""),
                    ("1484", "Дорошенко Ігор", "Павербанк 20000 мА·год", "TikTok", "щойно", "1 599", ""), ("1483", "Савчук Олена", "Лампа настільна LED", "Facebook", "3 хв", "899", "")],
            "noans": [("1469", "Петренко Сергій", "Смарт-годинник Fit 3", "Instagram", "2 спроби", "2 199", "late"), ("1466", "Руденко Ганна", "Колонка Go Mini", "Rozetka", "1 спроба", "1 599", "")],
            "call": [("1462", "Захарченко Ольга", "Зарядка GaN 65 Вт", "Лендинг", "о 18:00", "749", ""), ("1460", "Іваненко Петро", "Павербанк 10000 мА·год", "Prom", "завтра", "999", ""),
                     ("1457", "Кузьменко Віра", "Чохол MagSafe ×2", "Instagram", "о 16:30", "898", "late")],
            "dup": [("1471", "Коваленко Ірина", "Набір кабелів USB-C", "Лендинг", "дубль 1481", "649", "")]}
    cols = ""
    for code, cards in data.items():
        n, c = ST[code]
        cs = "".join(f"""<div class="kc"><div class="id">{ic("hash", 13)}{i}<span>·</span>{tag(src)}{ic("ellipsis", 15)}</div><b>{nm}</b><div class="pr">{p}</div>
<div class="ft"><span class="{"late" if late else ""}" style="display:inline-flex;gap:4px;align-items:center">{ic("clock", 13)}{t}</span><span class="s">{s} ₴</span></div></div>""" for i, nm, p, src, t, s, late in cards)
        cols += f'<div class="col"><div class="ch" style="--c:{c}"><i></i>{n}<em>{len(cards)}</em><span class="r">{ic("plus", 15)}{ic("ellipsis", 15)}</span></div>{cs}<div class="add">{ic("plus", 14)}Додати лід</div></div>'
    pg = f"""<div class="pg"><div class="crumb">Продажі {ic("chevron-right", 13)} Ліди</div><h1>Ліди</h1>
<div class="views"><span>{ic("list", 15)}Список</span><span class="on">{ic("square-kanban", 15)}Дошка</span><span>{ic("calendar", 15)}Передзвони</span>
<div class="r"><span class="btn">{ic("funnel", 14)}Фільтр</span><span class="btn">{ic("user", 14)}Мої</span><span class="btn p">{ic("plus", 14)}Лід</span></div></div>
<div class="kb">{cols}</div></div>"""
    return f'<div class="v3">{side("leads")}<main class="main">{topb()}{pg}</main></div>'


def card():
    o = ORDER
    props = [("circle-dot", "Статус", pill("ok")), ("user", "Менеджер", '<span class="pp"><span class="av">ОЛ</span>Олена Литвин</span>'),
             ("phone", "Телефон", f'{o["phone"]} <span class="tg" style="--bg:#E6F6EC;--fg:#14763D">Viber</span>'), ("globe", "Джерело", f'{tag("Instagram")} → Інтернет-магазин'),
             ("landmark", "Юрособа", "ФОП Максимчук О. В."), ("tag", "Позначки", '<span class="tg" style="--bg:#FFF3D6;--fg:#8A5A00">VIP</span> <span class="tg">Подарунок</span>'),
             ("contact", "Покупець", "4 замовлення · викуп 75% · 5 840 ₴".replace(" ", " ")), ("calendar", "Створено", "29 жовтня 2026, 14:32")]
    pr = "".join(f'<span class="k">{ic(i, 15)}{k}</span><span>{v}</span>' for i, k, v in props)
    rows = "".join(f'<tr><td>{"↳ " if up else ""}{nm}<div style="font-size:12px;color:var(--mut)">{var}</div></td><td class="mono">{sku}</td><td class="r">{q}</td><td class="r">{p} ₴</td><td class="r"><b style="font-weight:600">{s} ₴</b></td></tr>'
                   for nm, var, sku, q, p, s, up in o["items"])
    ev = "".join(f'<div class="ev"><span class="ic">{ic(i, 13)}</span><span>{t} <time>· {tm}</time><small>{d}</small></span></div>' for tm, t, d, i in reversed(TIMELINE))
    dl = f"""<div class="dl"><div class="crumb">Замовлення {ic("chevron-right", 13)} Підтверджено {ic("chevron-right", 13)} №1482
<span style="margin-left:auto;display:flex;gap:8px"><span class="btn">{ic("printer", 14)}Друк{ic("chevron-down", 13)}</span><span class="btn">{ic("receipt", 14)}Фіскалізувати</span><span class="btn k">{ic("truck", 14)}Створити ТТН</span></span></div>
<h1>Шевченко Тарас Григорович</h1><div class="props">{pr}</div>
<div class="views"><span class="on">{ic("package", 15)}Товари 2</span><span>{ic("truck", 15)}Доставка</span><span>{ic("wallet", 15)}Оплата</span><span>{ic("message-square", 15)}SMS 1</span><span>{ic("clock", 15)}Історія 5</span></div>
<table><thead><tr><th>Товар</th><th>Артикул</th><th class="r">К-сть</th><th class="r">Ціна</th><th class="r">Сума</th></tr></thead><tbody>{rows}
<tr><td colspan="5" style="color:var(--mut)">{ic("plus", 14)} Додати товар · {ic("sparkles", 14)} Допродаж: Чохол для павербанка, 249 ₴</td></tr>
<tr><td colspan="4" style="border:0;text-align:right;color:var(--mut)">Разом до сплати</td><td class="r" style="border:0;font-size:18px;font-weight:600">1 797 ₴</td></tr></tbody></table>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px"><div class="blk"><h4>{ic("truck", 16)}Нова Пошта<span class="r"><span class="st" style="--c:#F97316"><i></i>Прямує до відділення</span></span></h4>
<div class="kv"><span>Куди</span><b style="font-weight:500">Київ, відділення №12</b><span>ТТН</span><span class="mono" style="color:var(--ink)">20450913998365</span><span>Очікується</span><b style="font-weight:500">30.10, після 13:00</b></div></div>
<div class="blk"><h4>{ic("wallet", 16)}Оплата<span class="r"><span class="st" style="--c:#16A34A"><i></i>Чек: передоплата</span></span></h4>
<div class="kv"><span>Вид</span><b style="font-weight:500">Контроль оплати НП</b><span>Передоплата</span><b style="font-weight:500">200 ₴ · Monobank</b><span>При отриманні</span><b style="font-weight:600">1 597 ₴</b></div></div></div></div>"""
    feed = f'<div class="feed"><h4>{ic("clock", 15)}Активність</h4>{ev}<div class="cmt">{ic("message-square", 15)}Коментар для колег…{ic("send", 15)}</div></div>'
    return f'<div class="v3">{side("orders")}<main class="main">{topb()}<div class="doc">{dl}{feed}</div></main></div>'


def settings():
    ms = "".join(f'<div class="it {"on" if n == "Статуси" else ""}">{ic(i, 16)}{n}</div>' for n, i in SETTINGS)

    def rows(sec):
        out = ""
        for code, s, stock, chk, sms in STATUS_ROWS:
            if s != sec:
                continue
            sel = lambda v: f'<span class="sel">{v if v != "—" else "<span style=color:#C2C1BC>Нічого</span>"}{ic("chevron-down", 13)}</span>'
            out += f'<tr class="srow"><td>{ic("grip-vertical", 14)} {pill(code)}</td><td>{sel(stock)}</td><td>{sel(chk)}</td><td>{sel(sms)}</td><td class="r"><span class="sw {"off" if code == "dup" else ""}"></span></td></tr>'
        return out
    th = '<tr><th>Статус</th><th>Склад</th><th>Чек Checkbox</th><th>SMS / Viber</th><th class="r">Увімкнено</th></tr>'
    modal = f"""<div class="dim"></div><div class="modal"><div class="mside"><div class="gl" style="padding-top:0">Налаштування</div>{ms}</div>
<div class="mbody"><h2>Статуси</h2><p class="d">Що CRM робить сама, коли замовлення переходить у статус. Перетягніть, щоб змінити порядок.</p>
<div class="grp">{ic("inbox", 15)}<b>Ліди</b>— бачать менеджери на дошці лідів</div><table>{th}{rows("Ліди")}</table>
<div class="grp">{ic("receipt-text", 15)}<b>Замовлення</b>— від підтвердження до отримання</div><table>{th}{rows("Замовлення")}</table>
<div style="display:flex;gap:8px;margin-top:auto"><span class="btn">{ic("plus", 14)}Статус</span><span style="margin-left:auto" class="btn">Скасувати</span><span class="btn p">Зберегти зміни</span></div></div></div>"""
    return f'<div class="v3">{side("settings")}<main class="main">{topb()}<div class="pg"><h1>Налаштування</h1></div></main>{modal}</div>'


def attributes():
    rows = ""
    for n, (g, i, t, v, u) in enumerate(ATTR_GROUPS):
        vals = " ".join(f'<span class="tg">{x}</span>' for x, _ in v[:4])
        rows += f'<tr style="{"background:#F5F8FE" if n == 0 else ""}"><td>{ic(i, 15)} <b style="font-weight:500">{g}</b></td><td><span class="tg">{t}</span></td><td>{vals}</td><td class="r">{u.split()[0]}</td></tr>'
    vr = "".join(f'<tr><td><span class="chipv" style="--c:{c};margin:0;border:0;padding:0"><i></i>{col}</span></td><td>{cap}</td><td class="mono">{sku}</td><td class="r">{pr} ₴</td><td class="r"><span class="stk {"z" if st == 0 else ("lo" if st < 5 else "")}">{st}</span></td></tr>'
                 for col, c, cap, sku, pr, st, res in VARIANTS)
    vals = "".join(f'<span class="chipv" style="--c:{c}"><i></i>{n}</span>' for n, c in ATTR_GROUPS[0][3])
    pg = f"""<div class="pg"><div class="crumb">Склад {ic("chevron-right", 13)} Товари {ic("chevron-right", 13)} Атрибути</div><h1>Атрибути</h1>
<div class="views"><span>{ic("package", 15)}Товари</span><span>{ic("layers", 15)}Категорії</span><span>{ic("tag", 15)}Бренди</span><span class="on">{ic("sliders-horizontal", 15)}Атрибути</span></div>
<table style="width:calc(100% - 500px)"><thead><tr><th>Назва</th><th>Тип</th><th>Значення</th><th class="r">Товарів</th></tr></thead><tbody>{rows}
<tr><td colspan="4" style="color:var(--mut)">{ic("plus", 14)} Новий атрибут</td></tr></tbody></table></div>"""
    peek = f"""<div class="peek"><div class="hd">{ic("chevron-right", 16)}{ic("panel-left", 16)}<span class="r">{ic("link", 16)}{ic("ellipsis", 16)}{ic("x", 16)}</span></div>
<h1 style="font-size:24px">{ic("palette", 22)} Колір</h1><div class="kv"><span>Тип</span><span>Кольорові плашки</span><span>У фільтрі сайту</span><span>Так</span><span>Товарів</span><span>32</span></div>
<div><div class="grp" style="margin:4px 0 8px"><b>Значення</b></div>{vals}<span class="chipv" style="color:var(--mut)">{ic("plus", 13)}Додати</span></div>
<div class="grp" style="margin-top:4px"><b>Варіанти товару «Павербанк Volt»</b><span style="margin-left:auto" class="btn">{ic("layers", 14)}Згенерувати</span></div>
<table><thead><tr><th>Колір</th><th>Ємність</th><th>Артикул</th><th class="r">Ціна</th><th class="r">Залишок</th></tr></thead><tbody>{vr}</tbody></table></div>"""
    return f'<div class="v3">{side("products")}<main class="main">{topb()}{pg}</main>{peek}</div>'


def build():
    return page("Варіант 3 — Документ", CSS + mobile.CSS3, [
        ("1-menu", "Бокова панель із лічильниками і збереженими фільтрами + ліди дошкою", leads(), None, None),
        ("2-card", "Картка замовлення як сторінка з властивостями", card(), None, None),
        ("3-settings", "Налаштування — вікно поверх сторінки", settings(), None, None), ("4-attrs", "Атрибути — таблиця + бічна панель", attributes(), None, None),
        ("5-mobile", "Телефон: ліди, картка-сторінка, налаштування, атрибут", mobile.m3(), None, None)])
