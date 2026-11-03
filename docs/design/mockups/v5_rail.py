"""Варіант 5 — «Дві панелі» (темна смуга іконок + дерево розділу): щільно, як робочий інструмент; фіолетовий акцент."""
from common import *
import mobile

CSS = """
.v5{--ink:#17171C;--mut:#70707B;--line:#ECECF0;--acc:#6D4AFF;--acc2:#F1EDFF;font:400 13.5px/1.45 'Inter',sans-serif;color:var(--ink);background:#fff;width:100%;height:100%;display:flex}
.v5 .rail{width:68px;background:#16171B;display:flex;flex-direction:column;align-items:center;padding:14px 0;gap:4px;color:#9A9AA6}
.v5 .rail .lg{width:36px;height:36px;border-radius:10px;background:var(--acc);color:#fff;display:grid;place-items:center;font-weight:700;margin-bottom:12px}
.v5 .rb{width:52px;display:flex;flex-direction:column;align-items:center;gap:4px;padding:8px 0;border-radius:10px;font-size:10px;position:relative}
.v5 .rb.on{background:#26272E;color:#fff}.v5 .rb.on:before{content:"";position:absolute;left:-8px;top:10px;bottom:10px;width:3px;border-radius:3px;background:var(--acc)}
.v5 .rb em{position:absolute;top:4px;right:8px;width:8px;height:8px;border-radius:50%;background:#FF5C5C;border:2px solid #16171B}
.v5 .rail .bt{margin-top:auto;display:flex;flex-direction:column;align-items:center;gap:14px}
.v5 .rail .av{width:34px;height:34px;border-radius:50%;background:#E8D5C4;color:#3A2A1C;display:grid;place-items:center;font-weight:600;font-size:12px}
.v5 .panel{width:268px;background:#FAFAFB;border-right:1px solid var(--line);padding:16px 12px;display:flex;flex-direction:column;gap:6px}
.v5 .ph{display:flex;align-items:center;gap:8px;padding:0 6px 8px}.v5 .ph b{font-size:16px;font-weight:600}.v5 .ph .r{margin-left:auto;display:flex;gap:6px;align-items:center}
.v5 .sbtn{display:inline-flex;align-items:center;gap:5px;height:28px;padding:0 10px;border-radius:7px;border:1px solid var(--line);background:#fff;font-size:12.5px;font-weight:500;white-space:nowrap}
.v5 .sbtn.p{background:var(--acc);border-color:var(--acc);color:#fff}
.v5 .tr{display:flex;align-items:center;gap:8px;height:32px;padding:0 8px;border-radius:7px;color:#3A3A44;font-size:13px}
.v5 .tr .pm{width:16px;height:16px;border-radius:4px;border:1px solid #D7D7DE;display:grid;place-items:center;color:#70707B;flex:none;background:#fff}
.v5 .tr .v{margin-left:auto;font-variant-numeric:tabular-nums;color:#3A3A44;font-weight:500}
.v5 .tr.on{background:#fff;box-shadow:0 0 0 1px var(--line),0 1px 2px rgba(0,0,0,.04);font-weight:600}
.v5 .tr.sub{padding-left:32px;height:28px;font-size:12.5px;color:#55555F;position:relative}
.v5 .tr.sub:before{content:"";position:absolute;left:15px;top:0;bottom:0;border-left:1px solid #DDDDE3}
.v5 .tr.sub i{width:7px;height:7px;border-radius:50%;background:var(--c);flex:none}.v5 .tr.sub .v{font-weight:400;color:var(--mut)}
.v5 .tr.sub.on{background:var(--acc2);color:var(--acc);box-shadow:none}
.v5 .tr .ct{margin-left:auto;font-size:11.5px;color:var(--mut)}.v5 .tr .ct.hot{background:var(--acc);color:#fff;border-radius:99px;padding:0 7px;font-weight:600}
.v5 .pl{font-size:11.5px;color:#9A9AA6;padding:10px 8px 2px}
.v5 .addl{display:flex;align-items:center;gap:6px;color:var(--acc);font-size:12.5px;font-weight:500;padding:6px 8px}
.v5 .big{margin-top:auto;height:40px;border-radius:9px;background:#0E7C5B;color:#fff;display:flex;align-items:center;justify-content:center;gap:8px;font-weight:600}
.v5 .main{flex:1;min-width:0;padding:16px 22px;display:flex;flex-direction:column;gap:14px;background:#fff}
.v5 .mh{display:flex;align-items:center;gap:10px}.v5 .mh h2{font-size:17px;font-weight:600}.v5 .mh .r{margin-left:auto;display:flex;gap:6px}
.v5 .crd{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.v5 .mc{border:1px solid var(--line);border-radius:12px;padding:14px 16px}.v5 .mc .t{display:flex;color:var(--mut);font-size:12.5px}.v5 .mc .t .i{margin-left:auto}
.v5 .mc b{display:block;font-size:24px;font-weight:600;letter-spacing:-.02em;margin:6px 0 8px;font-variant-numeric:tabular-nums}
.v5 .mc .f{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--mut)}.v5 .mc .f b{font-size:12px;margin:0;color:var(--ink);display:inline;font-weight:600}
.v5 .pos{color:#0E7C5B}.v5 .neg{color:#D33C3C}
.v5 .tbx{border:1px solid var(--line);border-radius:12px;flex:1;min-height:0;overflow:hidden;display:flex;flex-direction:column}
.v5 .tbh{display:flex;align-items:center;gap:8px;padding:10px 14px;border-bottom:1px solid var(--line)}.v5 .tbh h3{font-size:14.5px;font-weight:600}
.v5 .tbh .r{margin-left:auto;display:flex;gap:6px;align-items:center}
.v5 .srch{white-space:nowrap;overflow:hidden;display:inline-flex;align-items:center;gap:6px;height:28px;padding:0 10px;border:1px solid var(--line);border-radius:7px;color:#9A9AA6;font-size:12.5px;width:210px}
.v5 table{width:100%;border-collapse:collapse}.v5 th{font-size:11.5px;color:var(--mut);font-weight:500;text-align:left;padding:7px 10px;background:#FAFAFB;border-bottom:1px solid var(--line)}
.v5 td{padding:7px 10px;border-bottom:1px solid #F3F3F6;font-size:13px;white-space:nowrap}
.v5 tr.gr td{background:#fff;color:var(--mut);font-size:12px;font-weight:500;padding:9px 10px}
.v5 .cb{width:15px;height:15px;border-radius:4px;border:1.5px solid #CFCFD7;display:inline-grid;place-items:center;vertical-align:middle}
.v5 .cb.on{background:var(--acc);border-color:var(--acc);color:#fff}
.v5 .st{display:inline-flex;align-items:center;gap:5px;height:22px;padding:0 8px;border-radius:6px;font-size:12px;font-weight:500;background:color-mix(in srgb,var(--c) 12%,#fff);color:color-mix(in srgb,var(--c) 72%,#000)}
.v5 .st i{width:6px;height:6px;border-radius:50%;background:var(--c)}
.v5 .tg{display:inline-block;font-size:11.5px;padding:1px 7px;border-radius:5px;background:#F2F2F5;color:#55555F;margin-right:3px}
.v5 .ac{display:flex;gap:10px;color:#9A9AA6}.v5 .sum{text-align:right;font-weight:600;font-variant-numeric:tabular-nums}
.v5 tr.sel td{background:#F7F5FF}
/* картка */
.v5 .of{display:grid;grid-template-columns:1fr 300px;gap:16px;flex:1;min-height:0}
.v5 .sec{border:1px solid var(--line);border-radius:12px;padding:14px 16px}.v5 .sec h4{font-size:13.5px;font-weight:600;display:flex;align-items:center;gap:8px;margin-bottom:10px}
.v5 .sec h4 .r{margin-left:auto;display:flex;gap:6px}
.v5 .fg{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.v5 .fl label{display:block;font-size:11.5px;color:var(--mut);margin-bottom:3px}
.v5 .in{display:flex;align-items:center;gap:6px;height:34px;padding:0 10px;border:1px solid #E2E2E8;border-radius:8px;background:#fff;font-size:13px}
.v5 .in .i:last-child{margin-left:auto;color:#9A9AA6}.v5 .in.f{border-color:var(--acc);box-shadow:0 0 0 3px var(--acc2)}
.v5 .mono{font:500 12.5px 'JB',monospace}
.v5 .side2{display:flex;flex-direction:column;gap:12px}
.v5 .sumb{border-radius:12px;background:#16171B;color:#fff;padding:16px}.v5 .sumb .l{display:flex;justify-content:space-between;font-size:12.5px;color:#A6A6B3;padding:5px 0}
.v5 .sumb .l b{color:#fff;font-weight:500}.v5 .sumb .tt{font-size:30px;font-weight:600;letter-spacing:-.02em;margin:4px 0 10px}
.v5 .wb{display:flex;align-items:center;justify-content:center;gap:7px;height:36px;border-radius:8px;font-weight:600;font-size:13px;border:1px solid var(--line);background:#fff}
.v5 .wb.p{background:var(--acc);color:#fff;border-color:var(--acc)}
.v5 .ev{display:grid;grid-template-columns:18px 1fr auto;gap:8px;font-size:12.5px;padding:5px 0}.v5 .ev i{width:8px;height:8px;border-radius:50%;background:var(--acc);margin:5px 0 0 4px}
.v5 .ev small{display:block;color:var(--mut);font-size:11.5px}.v5 .ev time{color:#9A9AA6;font-size:11.5px}
/* налаштування */
.v5 .dd{display:inline-flex;align-items:center;gap:6px;height:28px;padding:0 8px;border:1px solid #E6E6EC;border-radius:7px;font-size:12.5px;min-width:118px;background:#fff}
.v5 .dd .i{margin-left:auto;color:#9A9AA6}.v5 .dd.n{color:#B4B4BE}
.v5 .sw{display:inline-block;width:28px;height:16px;border-radius:99px;background:var(--acc);position:relative;vertical-align:middle}.v5 .sw:after{content:"";position:absolute;right:2px;top:2px;width:12px;height:12px;border-radius:50%;background:#fff}
.v5 .sw.off{background:#D6D6DE}.v5 .sw.off:after{right:auto;left:2px}
.v5 .colr{display:inline-block;width:18px;height:18px;border-radius:5px;background:var(--c);vertical-align:middle}
.v5 .bulk{display:flex;align-items:center;gap:10px;padding:8px 12px;background:#16171B;color:#fff;border-radius:10px;font-size:12.5px}
.v5 .bulk .sbtn{background:#26272E;border-color:#33343C;color:#fff}
.v5 .pin{display:inline-flex;align-items:center;height:26px;padding:0 8px;border:1px solid #E6E6EC;border-radius:6px;min-width:76px;font-variant-numeric:tabular-nums}
"""

RAIL = [("sales", "Продажі", "receipt-text"), ("stock", "Склад", "boxes"), ("money", "Гроші", "wallet"), ("stats", "Аналітика", "chart-column-stacked"),
        ("audit", "Журнал", "clock-fading"), ("settings", "Налашт.", "settings")]


def rail(on):
    r = "".join(f'<span class="rb {"on" if k == on else ""}">{ic(i, 20)}{n}{"<em></em>" if k == "sales" else ""}</span>' for k, n, i in RAIL)
    return f'<aside class="rail"><span class="lg">m</span>{r}<div class="bt">{ic("search", 19)}{ic("bell", 19)}<span class="av">ОЛ</span></div></aside>'


def sales_panel(active_sub="all"):
    subs = [("all", "Усі", None, "248"), ("ok", None, "ok", "31"), ("pack", None, "pack", "14"), ("sent", None, "sent", "57"), ("arr", None, "arr", "22"),
            ("got", None, "got", "96"), ("ref", None, "ref", "9")]
    s = ""
    for k, n, code, v in subs:
        nm, c = (n, "#6D4AFF") if n else ST[code]
        s += f'<div class="tr sub {"on" if k == active_sub else ""}" style="--c:{c}"><i></i>{nm}<span class="v">{v}</span></div>'
    return f"""<div class="panel"><div class="ph"><b>Продажі</b><span class="r"><span class="sbtn p">{ic("plus", 14)}Нове</span></span></div>
<div class="tr">{ic("house", 16)}Головна</div>
<div class="tr"><span class="pm">{ic("plus", 11)}</span>Ліди<span class="ct hot">5 нових</span></div>
<div class="tr on"><span class="pm">{ic("chevron-down", 11)}</span>Замовлення<span class="v">312 840 ₴</span></div>{s}
<div class="tr">{ic("square-kanban", 16)}Дошка</div><div class="tr"><span class="pm">{ic("plus", 11)}</span>Покупці<span class="ct">1 904</span></div>
<div class="pl">Мої фільтри</div><div class="tr">{ic("truck", 16)}Чекають ТТН<span class="ct">9</span></div><div class="tr">{ic("phone", 16)}Передзвонити сьогодні<span class="ct">6</span></div>
<div class="tr">{ic("store", 16)}Rozetka · нові<span class="ct">3</span></div><div class="addl">{ic("plus", 14)}Зберегти поточний фільтр</div>
<div class="big">{ic("printer", 16)}Реєстр НП на сьогодні · 14</div></div>"""


def orders():
    groups = [("Сьогодні, 29 жовтня · 10 замовлень · 12 316 ₴", ORDERS[:6]), ("Вчора, 28 жовтня · 14 замовлень · 18 902 ₴", ORDERS[6:10])]
    tags = {1482: ["VIP"], 1479: ["Подарунок"], 1476: ["Опт", "Повторний"], 1474: ["Повторний"]}
    rows = ""
    for title, os_ in groups:
        rows += f'<tr class="gr"><td colspan="9">{ic("chevron-down", 13)} {title}</td></tr>'
        for o in os_:
            sel = o[0] == 1482
            t = "".join(f'<span class="tg">{x}</span>' for x in tags.get(o[0], []))
            rows += f"""<tr class="{"sel" if sel else ""}"><td><span class="cb {"on" if sel else ""}">{ic("check", 10, 3) if sel else ""}</span></td><td class="mono">{o[0]}</td><td><b style="font-weight:500">{o[1]}</b> <span style="color:var(--mut)">{o[2]}</span></td>
<td>{o[3]}</td><td>{pill(o[6])}</td><td>{t}</td><td style="color:var(--mut)">{o[8]}</td><td class="sum">{o[5]} ₴</td><td><span class="ac">{ic("printer", 15)}{ic("eye", 15)}</span></td></tr>"""
    cards = f"""<div class="crd"><div class="mc"><div class="t">Надійшло сьогодні{ic("ellipsis", 15)}</div><b class="pos">+24 870 ₴</b><div class="f">{ic("wallet", 14)}<b>NovaPay</b> · 11 переказів</div></div>
<div class="mc"><div class="t">Післяплата в дорозі{ic("ellipsis", 15)}</div><b>48 300 ₴</b><div class="f">{ic("truck", 14)}<b>Нова Пошта</b> · 57 посилок</div></div>
<div class="mc"><div class="t">Повернення за тиждень{ic("ellipsis", 15)}</div><b class="neg">−3 297 ₴</b><div class="f">{ic("undo-2", 14)}<b>4 відмови</b> · викуп 81%</div></div></div>"""
    table = f"""<div class="tbx"><div class="tbh"><h3>Замовлення</h3><span style="color:var(--mut)">· усі статуси</span><div class="r"><span class="srch">{ic("search", 14)}Пошук за телефоном, ТТН…</span>
<span class="sbtn">{ic("list-filter", 14)}Фільтри 2</span><span class="sbtn">{ic("layout-grid", 14)}Колонки</span><span class="sbtn">{ic("arrow-up-right", 14)}Експорт</span></div></div>
<table><thead><tr><th></th><th>№</th><th>Покупець</th><th>Товар</th><th>Статус</th><th>Позначки</th><th>Джерело</th><th style="text-align:right">Сума</th><th></th></tr></thead><tbody>{rows}</tbody></table></div>"""
    return f'<div class="v5">{rail("sales")}{sales_panel()}<main class="main">{cards}{table}</main></div>'


def card():
    o = ORDER
    nav = [("user", "Покупець", ""), ("package", "Товари", "2"), ("truck", "Доставка", ""), ("wallet", "Оплата", ""), ("receipt", "Чеки", "1"),
           ("message-square", "SMS і Viber", "1"), ("clock-fading", "Історія", "5")]
    nv = "".join(f'<div class="tr {"on" if n == "Товари" else ""}">{ic(i, 16)}{n}<span class="ct">{c}</span></div>' for i, n, c in nav)
    other = "".join(f'<div class="tr sub" style="--c:{ST[st][1]}"><i></i>№{n} · {p}<span class="v">{s}</span></div>' for n, p, st, s in
                    [(1391, "TWS Pro", "got", "1 290"), (1207, "Павербанк 10000", "ref", "999"), (1102, "Кабель ×3", "got", "449")])
    panel = f"""<div class="panel"><div class="ph">{ic("arrow-left", 16)}<b>№1482</b><span class="r">{pill("ok")}</span></div>
<div style="padding:0 8px 8px;color:var(--mut);font-size:12px">29.10.2026, 14:32 · Instagram</div>{nv}
<div class="pl">Інші замовлення покупця</div>{other}<div class="pl">Швидкі дії</div>
<div class="tr">{ic("phone", 16)}Подзвонити</div><div class="tr">{ic("message-circle", 16)}Написати у Viber</div><div class="tr">{ic("copy", 16)}Дублювати замовлення</div></div>"""
    goods = "".join(f"""<tr><td>{"&nbsp;&nbsp;↳ " if up else ""}<b style="font-weight:500">{nm}</b><div style="color:var(--mut);font-size:12px">{var}</div></td><td class="mono">{sku}</td>
<td><span class="pin">{q}</span></td><td><span class="pin">{p} ₴</span></td><td class="sum">{s} ₴</td><td><span class="ac">{ic("trash", 15)}</span></td></tr>""" for nm, var, sku, q, p, s, up in o["items"])
    f = lambda l, v, i=None, cls="": f'<div class="fl"><label>{l}</label><div class="in {cls}">{ic(i, 15) if i else ""}{v}{ic("chevron-down", 14)}</div></div>'
    main = f"""<div class="mh"><h2>Шевченко Тарас Григорович</h2><span class="tg">VIP</span><span class="tg">Подарунок</span><div class="r"><span class="sbtn">{ic("printer", 14)}Друк{ic("chevron-down", 13)}</span>
<span class="sbtn">{ic("tag", 14)}Наклейка</span><span class="sbtn">{ic("receipt", 14)}Фіскалізувати</span></div></div>
<div class="of"><div style="display:flex;flex-direction:column;gap:12px;min-height:0">
<div class="sec"><h4>{ic("user", 15)}Покупець<span class="r" style="color:var(--mut);font-weight:400;font-size:12px">4 замовлення · викуп 75% · 5 840 ₴</span></h4>
<div class="fg"><div class="fl"><label>ПІБ — одним рядком</label><div class="in">{o["name"]}</div></div>{f("Телефон", o["phone"], "phone")}{f("Менеджер", "Олена Литвин", "user")}
{f("Джерело", "Instagram", "globe")}{f("Юрособа", "ФОП Максимчук О. В.", "landmark")}{f("Статус", pill("ok"))}</div></div>
<div class="sec"><h4>{ic("package", 15)}Товари<span class="r"><span class="sbtn">{ic("plus", 13)}Товар</span><span class="sbtn">{ic("sparkles", 13)}Допродаж</span></span></h4>
<table><thead><tr><th>Товар</th><th>Артикул</th><th>К-сть</th><th>Ціна</th><th style="text-align:right">Сума</th><th></th></tr></thead><tbody>{goods}</tbody></table></div>
<div class="sec"><h4>{ic("truck", 15)}Доставка<span class="r"><span class="st" style="--c:#F97316"><i></i>Прямує до відділення</span></span></h4>
<div class="fg">{f("Служба", "Нова Пошта", "truck")}{f("Місто", "Київ", "map-pin")}{f("Відділення", "№12 · Межигірська, 1")}
<div class="fl"><label>ТТН</label><div class="in"><span class="mono">20450913998365</span>{ic("copy", 14)}</div></div>{f("Платник доставки", "Отримувач")}{f("Ключ НП", "ФОП Максимчук · Тульчин")}</div></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px"><div class="sec"><h4>{ic("message-square", 15)}Коментар</h4><div class="in" style="height:58px;align-items:flex-start;padding-top:8px">Зателефонувати після 18:00, подарункове пакування</div></div>
<div class="sec"><h4>{ic("tag", 15)}Позначки й UTM</h4><div><span class="tg">VIP</span><span class="tg">Подарунок</span><span class="tg" style="color:var(--acc)">+ позначка</span></div>
<div style="margin-top:8px;color:var(--mut);font-size:12px" class="mono">instagram / stories / powerbank-20</div></div></div></div>
<div class="side2"><div class="sumb"><div style="font-size:12.5px;color:#A6A6B3">До сплати при отриманні</div><div class="tt">1 597 ₴</div>
<div class="l"><span>Товари</span><b>1 797 ₴</b></div><div class="l"><span>Передоплата · Monobank</span><b>−200 ₴</b></div><div class="l"><span>Вид оплати</span><b>Контроль оплати НП</b></div>
<div class="l"><span>Чек Checkbox</span><b style="color:#B9A8FF">Передоплата ✓</b></div></div>
<span class="wb p">{ic("truck", 16)}Створити ТТН</span><span class="wb">{ic("check", 16)}Зберегти · Ctrl S</span>
<div class="sec"><h4>{ic("clock-fading", 15)}Історія</h4>{"".join(f'<div class="ev"><i></i><span>{t}<small>{d}</small></span><time>{tm}</time></div>' for tm, t, d, i in TIMELINE[1:])}</div></div></div>"""
    return f'<div class="v5">{rail("sales")}{panel}<main class="main">{main}</main></div>'


def settings():
    tree = [("Продажі", [("Статуси", True), ("Довідники", False), ("Джерела й відділи", False)]),
            ("Доставка", [("Нова Пошта · 2 ключі", False), ("Укрпошта", False), ("Meest", False)]),
            ("Гроші", [("Юрособи", False), ("Checkbox · 3 каси", False), ("Види оплат", False)]),
            ("Зв'язок", [("SMS і Viber", False), ("Telegram", False)]), ("Система", [("Користувачі", False), ("Документи", False), ("Маркетплейси", False)])]
    t = ""
    for g, items in tree:
        t += f'<div class="tr" style="font-weight:600"><span class="pm">{ic("chevron-down", 11)}</span>{g}</div>'
        t += "".join(f'<div class="tr sub {"on" if on else ""}" style="--c:#6D4AFF">{n}</div>' for n, on in items)
    panel = f'<div class="panel"><div class="ph"><b>Налаштування</b></div><div class="srch" style="width:auto;margin:0 4px 8px">{ic("search", 14)}Знайти налаштування</div>{t}</div>'
    rows = ""
    np = {"sent": "1, 2", "arr": "7, 8", "got": "9, 10", "ref": "102, 103"}
    for code, s, stock, chk, sms in STATUS_ROWS:
        n, c = ST[code]
        sl = lambda v: f'<span class="dd {"n" if v == "—" else ""}">{v if v != "—" else "Нічого"}{ic("chevron-down", 13)}</span>'
        rows += f"""<tr><td style="color:#C4C4CC">{ic("grip-vertical", 14)}</td><td><span class="colr" style="--c:{c}"></span></td><td><b style="font-weight:500">{n}</b></td>
<td><span class="tg">{s}</span></td><td>{sl(stock)}</td><td>{sl(chk)}</td><td>{sl(sms)}</td><td class="mono" style="color:var(--mut)">{np.get(code, "—")}</td><td><span class="sw {"off" if code == "dup" else ""}"></span></td></tr>"""
    main = f"""<div class="mh"><h2>Статуси</h2><span style="color:var(--mut)">· 10 статусів · 2 розділи</span><div class="r"><span class="sbtn">{ic("eye", 14)}Перевірити на замовленні</span><span class="sbtn p">{ic("check", 14)}Зберегти</span></div></div>
<div class="tbx"><table><thead><tr><th></th><th>Колір</th><th>Назва</th><th>Розділ</th><th>Склад</th><th>Чек Checkbox</th><th>SMS / Viber</th><th>Коди НП → статус</th><th>Увімк.</th></tr></thead><tbody>{rows}
<tr><td></td><td colspan="8" style="color:var(--acc);font-weight:500">{ic("plus", 14)} Додати статус</td></tr></tbody></table></div>"""
    return f'<div class="v5">{rail("settings")}{panel}<main class="main">{main}</main></div>'


def attributes():
    t = ""
    for n, (g, i, typ, v, u) in enumerate(ATTR_GROUPS):
        t += f'<div class="tr {"on" if n == 0 else ""}"><span class="pm">{ic("chevron-down" if n == 0 else "plus", 11)}</span>{g}<span class="ct">{u.split()[0]}</span></div>'
        if n == 0:
            t += "".join(f'<div class="tr sub" style="--c:{c}"><i style="width:10px;height:10px;border-radius:3px;box-shadow:inset 0 0 0 1px rgba(0,0,0,.15)"></i>{x}<span class="v">{[12, 9, 7, 4][k]}</span></div>' for k, (x, c) in enumerate(v))
    panel = f"""<div class="panel"><div class="ph"><b>Склад</b><span class="r"><span class="sbtn p">{ic("plus", 14)}Товар</span></span></div>
<div class="tr">{ic("package", 16)}Товари<span class="ct">86</span></div><div class="tr">{ic("layers", 16)}Категорії<span class="ct">12</span></div><div class="tr">{ic("tag", 16)}Бренди<span class="ct">7</span></div>
<div class="pl">Атрибути</div>{t}<div class="addl">{ic("plus", 14)}Новий атрибут</div></div>"""
    rows = ""
    for n, (col, c, cap, sku, pr, st, res) in enumerate(VARIANTS):
        sel = n in (2, 3)
        rows += f"""<tr class="{"sel" if sel else ""}"><td><span class="cb {"on" if sel else ""}">{ic("check", 10, 3) if sel else ""}</span></td><td><span class="colr" style="--c:{c};width:14px;height:14px;box-shadow:inset 0 0 0 1px rgba(0,0,0,.15)"></span> {col}</td>
<td>{cap} мА·год</td><td class="mono">{sku}</td><td><span class="pin">{pr} ₴</span></td><td><span class="pin">{"1 020" if "20" in cap else "640"} ₴</span></td>
<td class="sum" style="color:{"#D33C3C" if st == 0 else ("#B7791F" if st < 5 else "inherit")}">{st}</td><td class="sum" style="font-weight:400;color:var(--mut)">{res}</td><td><span class="sw {"off" if st == 0 else ""}"></span></td></tr>"""
    main = f"""<div class="mh"><h2>Павербанк Volt</h2><span class="tg">Колір</span><span class="tg">Ємність</span><span style="color:var(--mut)">· 6 варіантів · 63 шт · 2 закінчуються</span>
<div class="r"><span class="sbtn">{ic("layers", 14)}Згенерувати комбінації</span><span class="sbtn p">{ic("check", 14)}Зберегти</span></div></div>
<div class="crd"><div class="mc"><div class="t">На складі</div><b>63 шт</b><div class="f">резерв <b>6</b> · вільно <b>57</b></div></div>
<div class="mc"><div class="t">Продано за 30 днів</div><b>148 шт</b><div class="f">найкраще: <b>Чорний · 20 000</b></div></div>
<div class="mc"><div class="t">Закінчиться</div><b class="neg">~ 9 днів</b><div class="f">{ic("shopping-cart", 14)}<b>Створити закупівлю</b></div></div></div>
<div class="bulk"><span class="cb on">{ic("check", 10, 3)}</span>Вибрано 2 варіанти<span class="sbtn">Змінити ціну</span><span class="sbtn">Списати / оприбуткувати</span><span class="sbtn">Вимкнути продаж</span><span style="margin-left:auto">{ic("x", 15)}</span></div>
<div class="tbx"><table><thead><tr><th></th><th>Колір</th><th>Ємність</th><th>Артикул</th><th>Ціна</th><th>Собівартість</th><th style="text-align:right">Залишок</th><th style="text-align:right">Резерв</th><th>Продаж</th></tr></thead><tbody>{rows}</tbody></table></div>"""
    return f'<div class="v5">{rail("stock")}{panel}<main class="main">{main}</main></div>'


def build():
    return page("Варіант 5 — Дві панелі", CSS + mobile.CSS5, [
        ("1-menu", "Смуга розділів + дерево статусів із сумами", orders(), None, None), ("2-card", "Картка замовлення: навігація по блоках зліва", card(), None, None),
        ("3-settings", "Налаштування — дерево розділів + щільна таблиця", settings(), None, None), ("4-attrs", "Атрибути у дереві + варіанти з масовими діями", attributes(), None, None),
        ("5-mobile", "Телефон: дерево статусів, список, картка, варіанти", mobile.m5(), None, None)])
