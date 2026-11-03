"""Список замовлень на ПК — 5 варіантів у мові v2 (сірий фон, білі картки, статус кольором, лише ввімкнені фільтри видно)."""
from common import *
from v18_desktop import CSS as BASE, sidebar, st, sq, ring, frame, head, ORD, orders as v18_orders

CSS = BASE + """
.tr.one{min-height:40px;font-size:13px;column-gap:10px;white-space:nowrap}.tr.one > *{min-width:0;overflow:hidden;text-overflow:ellipsis}.acts .ok2{white-space:nowrap;display:flex !important;align-items:center;gap:4px}
.acts{display:flex;gap:4px;justify-content:flex-end}.acts span{width:28px;height:28px;border-radius:8px;display:grid;place-items:center;background:#F2F3F5;color:#3D3C38}
.acts .ok2{width:auto;padding:0 10px;background:var(--acc2);color:var(--acc);font-size:12.5px;font-weight:500}
.dt{width:7px;height:7px;border-radius:50%;flex:none;display:inline-block}
.av2{width:22px;height:22px;border-radius:50%;display:inline-grid;place-items:center;background:#EAF1FD;color:#1F56C4;font-size:9.5px;font-weight:600}
.gh{display:flex;align-items:center;gap:10px;padding:12px 16px;background:#FAFAFB;border-top:1px solid #F0F0EE}
.gh b{font-size:14.5px}.gh .cnt{min-width:22px;height:20px;border-radius:99px;display:grid;place-items:center;font-size:11.5px;font-weight:600;padding:0 6px}
.oc{background:#fff;border-radius:18px;padding:12px 14px;display:flex;flex-direction:column;gap:8px}
.oc .t{display:flex;align-items:center;gap:7px}.oc .m{margin-left:auto;font-size:12px;color:var(--faint)}
.oc .n{display:flex;justify-content:space-between;gap:10px}.oc .n b{font-size:16px}
.oc .g{display:flex;align-items:center;gap:8px;padding-top:8px;border-top:1px solid #F0F0EE;font-size:13px;min-width:0;white-space:nowrap}.oc .g > .mut{flex:none;max-width:90px;overflow:hidden;text-overflow:ellipsis}
.oc .a{display:flex;gap:6px}.oc .a span{flex:1;height:32px;border-radius:10px;display:flex;align-items:center;justify-content:center;gap:6px;font-size:12.5px;font-weight:500;background:#F2F3F5}
.oc .a span.p{background:var(--acc);color:#fff}.oc .a span.s{background:var(--acc2);color:var(--acc)}
.mi{display:flex;flex-direction:column;gap:4px;padding:11px 14px;border-radius:14px;cursor:pointer}
.mi.on{background:#fff;box-shadow:0 0 0 1.5px var(--acc3)}
.mi .r1{display:flex;align-items:center;gap:8px}.mi .r1 b{font-size:14.5px}.mi .r1 .s{margin-left:auto;font-weight:600}
.mi .r2{display:flex;align-items:center;gap:8px;font-size:12.5px;color:var(--mut)}
.inp2{height:38px;border-radius:11px;background:#F6F7F8;display:flex;align-items:center;gap:8px;padding:0 12px;font-size:13.5px}
"""

PH = {"44": "+380 67 111 22 33", "43": "+380 93 455 10 07", "42": "+380 50 224 18 90", "41": "+380 97 300 44 21", "40": "+380 66 811 03 52", "39": "+380 68 905 12 44",
      "38": "+380 63 118 90 05", "37": "+380 99 220 41 77", "36": "+380 95 664 82 10", "35": "+380 67 801 55 12"}
MORE = [("done", "34", "27.10", "Ганна Лисенко", "+380 67 220 15 90", "Маска для обличчя", "", "НП", "Полтава, №3", "299", False, ""),
        ("done", "33", "27.10", "Роман Кравченко", "+380 50 331 44 81", "Крем для рук «Лаванда»", "+1", "НП", "Житомир, №7", "598", False, ""),
        ("sent", "32", "26.10", "Юлія Марченко", "+380 93 712 08 64", "Сироватка з вітаміном C", "", "НП", "Київ, №212", "649", False, ""),
        ("wait", "31", "26.10", "Олена Коваль", "+380 67 111 22 33", "Бездротовий мікрофон", "", "НП", "Київ, №12", "1 899", False, ""),
        ("done", "30", "25.10", "Петро Іваненко", "+380 98 004 32 11", "Кільцева лампа 26 см", "", "Укрпошта", "Ніжин", "899", False, ""),
        ("ref", "29", "25.10", "Ярослав Бойко", "+380 73 650 22 18", "Екшн-камера 4К", "", "НП", "Рівне, №2", "5 499", False, "")]
ALL = ORD + MORE
TABS = [("Несортовані", 16, "#7C7B76", False, True), ("Прийняті", 3, "#2E6BE6", False, False), ("Відправлені", 13, "#6D5BD0", False, False), ("Очікує на пошті", 5, "#D97706", False, False),
        ("Завершені", 68, "#16A34A", False, False), ("Відмова", 7, "#DC2626", False, False), ("Усі", 126, "#1F1F1C", True, False)]


def tabs(items=TABS):
    return '<div class="tabs">' + "".join(f'<span class="tab{" on" if on else ""}" style="--c:{c}">{n} <em{" class=h" if h else ""}>{k}</em></span>' for n, k, c, on, h in items) + "</div>"


def hdr(right_extra=""):
    return head("Замовлення", "<b>16</b> несортованих · <b>3</b> чекають відправки · <b>13</b> у дорозі",
                f'<span class="srch" style="width:250px">{ic("search",16)}Пошук у списку<kbd>/</kbd></span><span class="rb">{ic("list-filter",19)}<span class="dot"></span></span>{right_extra}<span class="btn p">{ic("plus",17)}Замовлення</span>')


CHIPS = f'<div class="row" style="gap:6px"><span class="chip on">{ic("calendar",13)}Сьогодні й учора{ic("x",12)}</span><span class="chip on">Нова Пошта{ic("x",12)}</span></div>'
SEG = lambda on: '<span class="seg">' + "".join(f'<span class="{"on" if k == on else ""}">{ic(i,14)}{n}</span>' for k, i, n in [("t", "list", "Таблиця"), ("c", "layout-grid", "Картки"), ("b", "square-kanban", "Дошка")]) + "</span>"
PAY = {"uns": ("#2E6BE6", "Контроль оплати"), "acc": ("#16A34A", "Передоплата"), "sent": ("#2E6BE6", "Післяплата"), "wait": ("#2E6BE6", "Післяплата"), "done": ("#16A34A", "Оплачено"), "ref": ("#2E6BE6", "Післяплата")}
SRC = [("Instagram", "#DB2777"), ("Лендинг", "#2E6BE6"), ("TikTok", "#16A34A"), ("Rozetka", "#D97706")]


# ---------------------------------------------------------------- 1. Щільна таблиця (рядок 40 px, усі колонки, дії при наведенні)
def l1():
    G = "18px 34px minmax(100px,1fr) 136px minmax(90px,1fr) 116px 108px 112px 72px 24px 54px 66px"
    out = f'<div class="tr h one" style="grid-template-columns:{G}"><span class="cb"></span><span>№</span><span>Покупець</span><span>Телефон</span><span>Товар</span><span>Статус</span><span>Оплата</span><span>Доставка</span><span>Джерело</span><span>Мен.</span><span>Дата</span><span style="text-align:right">Сума</span></div>'
    for k, (s, no, t, n, ph, g, more, dl, city, sm, warn, flag) in enumerate(ALL):
        pc, pn = PAY[s]
        src, scol = SRC[k % 4]
        hover = k == 2
        dlv = f'<span class="np">НП</span><span class="ell mut">{city}</span>' if dl == "НП" else f'<span class="ell mut">{dl + " · " if dl else ""}{city}</span>'
        flg = f' <span style="color:var(--warn)">{ic("circle-alert",12)}</span>' if flag == "warn" else (' <span class="st" style="--c:#DC2626;height:17px;font-size:10px">ЧС</span>' if flag == "bl" else "")
        tail = f'<span class="acts" style="grid-column:span 2"><span class="ok2">{ic("check",13)}Прийняти</span><span>{ic("phone",13)}</span><span>{ic("eye",13)}</span></span>' if hover else \
            f'<span class="mut num">{t if ":" in t else t}</span><b class="num" style="text-align:right">{sm} ₴</b>'
        out += f'''<div class="tr one" style="grid-template-columns:{G};{"background:#FAFAF8" if hover else ""}"><span class="cb"></span><span class="num" style="font:600 12px JB;color:#57564F">{no}</span>
<span class="ell" style="font-weight:500">{n}{flg}</span><span class="num mut">{ph}</span><span class="row" style="gap:6px"><span class="ell">{g}</span>{f'<span class="fa" style="flex:none">{more}</span>' if more else ""}</span>
<span>{st(s)}</span><span class="row" style="gap:6px"><i class="dt" style="background:{pc}"></i><span class="ell">{pn}</span></span><span class="row" style="gap:6px">{dlv}</span>
<span class="row" style="gap:6px"><i class="dt" style="background:{scol}"></i><span class="ell">{src}</span></span><span class="av2">ОЛ</span>{tail}</div>'''
    body = f'''{hdr(SEG("t"))}<div class="row" style="justify-content:space-between;margin-bottom:12px">{tabs()}{CHIPS}</div>
<div class="tb" style="flex:1;margin-bottom:16px">{out}</div>'''
    return frame("orders", body)


# ---------------------------------------------------------------- 3. Групи за станом роботи (що робити зараз) з дією на всю групу
def l3():
    G = "18px 58px minmax(150px,1.2fr) minmax(140px,1.2fr) 118px 140px 80px"
    def rows(items):
        o = ""
        for s, no, t, n, ph, g, more, dl, city, sm, warn, flag in items:
            dlv = f'<span class="np">НП</span><span class="ell mut">{city}</span>' if dl == "НП" else f'<span class="ell mut">{dl + " · " if dl else ""}{city}</span>'
            o += f'''<div class="tr" style="grid-template-columns:{G};min-height:52px"><span class="cb"></span><span class="two"><b style="font:600 12.5px JB">№{no}</b><small>{t}</small></span>
<span class="two"><span class="ell" style="font-weight:500">{n}</span><small class="num">{ph}</small></span><span class="row" style="gap:8px"><span class="th" style="width:28px;height:28px;border-radius:8px">{ic("package",12)}</span><span class="ell">{g}</span></span>
<span>{st(s)}</span><span class="row" style="gap:6px">{dlv}</span><b class="num" style="text-align:right">{sm} ₴</b></div>'''
        return o
    def grp(title, c, n, act, items, open_=True, hint=""):
        return f'''<div class="gh"><span style="color:var(--faint)">{ic("chevron-down" if open_ else "chevron-right",16)}</span><i class="dt" style="width:9px;height:9px;background:{c}"></i><b>{title}</b>
<span class="cnt" style="background:color-mix(in srgb,{c} 14%,white);color:color-mix(in srgb,{c} 75%,black)">{n}</span><span class="mut" style="font-size:12.5px">{hint}</span><span style="flex:1"></span>{act}</div>{rows(items) if open_ else ""}'''
    body = f'''{hdr('<span class="seg"><span class="on">Що робити</span><span>За датою</span></span>')}
<div class="row" style="justify-content:space-between;margin-bottom:12px"><div class="row" style="gap:6px"><span class="chip on">Мої й нічиї{ic("x",12)}</span><span class="chip dash">{ic("plus",13)}Дата</span><span class="chip dash">{ic("plus",13)}Доставка</span></div><span class="mut" style="font-size:13px">сортування: найстаріші зверху</span></div>
<div class="tb" style="flex:1;margin-bottom:16px;overflow:hidden">
{grp("Несортовані — прийняти", "#7C7B76", 16, f'<span class="btn sm s">{ic("check",14)}Прийняти вибрані</span>', [ORD[0], ORD[1]], True, "найдовше чекає 2 год")}
{grp("Прийняті — створити ТТН", "#2E6BE6", 3, f'<span class="btn sm p">{ic("truck",14)}Створити 3 ТТН</span>', [ORD[2], ORD[3]], True, "товар зарезервовано")}
{grp("Очікують на пошті — нагадати", "#D97706", 5, f'<span class="btn sm g">{ic("message-square",14)}SMS усім 5</span>', [ORD[6]], True, "3 лежать понад 4 дні")}
{grp("У дорозі", "#6D5BD0", 13, '<span class="ac" style="font-size:13px">оновити трекінг</span>', [], False)}
{grp("Завершені за тиждень", "#16A34A", 68, "", [], False)}
{grp("Відмови й повернення", "#DC2626", 7, '<span class="ac" style="font-size:13px">повернути на склад</span>', [], False)}</div>'''
    return frame("orders", body)


# ---------------------------------------------------------------- 4. Картки сіткою (як на телефоні) з дією в самій картці
def l4():
    def card(o, k):
        s, no, t, n, ph, g, more, dl, city, sm, warn, flag = o
        act = {"uns": f'<span class="p">{ic("check",13)}Прийняти</span>', "acc": f'<span class="s">{ic("truck",13)}ТТН</span>', "wait": f'<span class="s">{ic("message-square",13)}SMS</span>'}.get(s, f'<span>{ic("eye",13)}Відкрити</span>')
        fl = f'<span class="sq sm" style="--s:#FDF1E3;--i:#D97706;width:22px;height:22px;border-radius:7px">{ic("circle-alert",12)}</span>' if flag == "warn" else (f'<span class="sq sm" style="--s:#EAF1FD;--i:#2E6BE6;width:22px;height:22px;border-radius:7px">{ic("message-square",12)}</span>' if flag == "cmt" else "")
        dlv = f'<span class="np">НП</span><span class="mut ell">{city}</span>' if dl == "НП" else f'<span class="mut ell">{dl or "без доставки"}</span>'
        return f'''<div class="oc"><div class="t">{st(s)}{fl}<span class="m">№{no} · {t}</span></div><div class="n"><b class="ell">{n}</b><b class="num">{sm} ₴</b></div>
<div class="g"><span class="th" style="width:28px;height:28px;border-radius:8px">{ic("package",12)}</span><span class="ell" style="flex:1">{g} <span class="fa">{more}</span></span>{dlv}</div>
<div class="a"><span>{ic("phone",13)}</span>{act}</div></div>'''
    grid = "".join(card(o, k) for k, o in enumerate(ALL[:16]))
    body = f'''{hdr(SEG("c"))}<div class="row" style="justify-content:space-between;margin-bottom:12px">{tabs()}{CHIPS}</div>
<div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;align-content:start;flex:1;margin-bottom:16px">{grid}</div>'''
    return frame("orders", body)


# ---------------------------------------------------------------- 5. Скринька: вузький список ліворуч + повна картка праворуч (без вікон)
def l5():
    items = ""
    for k, (s, no, t, n, ph, g, more, dl, city, sm, warn, flag) in enumerate(ALL[:9]):
        items += f'''<div class="mi{" on" if k == 0 else ""}"><div class="r1"><i class="dt" style="background:{dict(uns="#7C7B76",acc="#2E6BE6",sent="#6D5BD0",wait="#D97706",done="#16A34A",ref="#DC2626")[s]}"></i><b class="ell">{n}</b><span class="s num">{sm} ₴</span></div>
<div class="r2"><span class="num" style="font:600 11.5px JB">№{no}</span><span class="ell" style="flex:1">{g}</span><span class="fa">{t}</span></div></div>'''
    goods = f'''<div class="row" style="height:46px;border-radius:12px;background:#F6F7F8;padding:0 10px;gap:10px"><span class="th" style="width:30px;height:30px;border-radius:9px">{ic("package",13)}</span><b style="font-weight:500;flex:1">Бездротовий мікрофон</b><small class="fa">MIC-01 · 3 шт</small>
<span class="row" style="gap:10px;height:30px;border-radius:99px;background:#fff;padding:0 10px"><span class="fa">−</span><b>1</b><span class="fa">+</span></span><b style="width:70px;text-align:right">1 899 ₴</b></div>'''
    right = f'''<div class="c col" style="flex:1;gap:12px;min-width:0">
<div class="row" style="gap:10px"><b style="font:600 14px JB">№44</b><span class="mut">сьогодні 17:10 · лендинг</span><span style="flex:1"></span><span class="rb" style="width:36px;height:36px;background:#F2F3F5">{ic("printer",16)}</span><span class="rb" style="width:36px;height:36px;background:#F2F3F5">{ic("bell",16)}</span><span class="rb" style="width:36px;height:36px;background:#F2F3F5">{ic("arrow-up-right",16)}</span></div>
<div class="row" style="gap:6px">{"".join(f'<span class="chip" style="height:32px;{x}">{n}</span>' for n, x in [("Несортований", "background:#7C7B76;color:#fff"), ("Прийнятий", "background:#F6F7F8"), ("Відправлений", "background:#F6F7F8"), ("На пошті", "background:#F6F7F8"), ("Завершений", "background:#F6F7F8")])}</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px"><div><div class="lab">Покупець</div><div class="inp2" style="font-weight:500">Олена Коваль</div></div><div><div class="lab">Телефон</div><div class="inp2"><span style="width:18px;height:13px;border-radius:3px;background:linear-gradient(#2E6BE6 50%,#F5C518 50%)"></span>+380 67 111 22 33<span style="margin-left:auto" class="ac">{ic("phone",15)}</span></div></div></div>
<div><div class="row lab">Товари<span style="margin-left:auto" class="ac">+ Товар · + Допродаж</span></div>{goods}<div class="row" style="margin-top:8px;height:40px;border-radius:12px;border:1.5px solid var(--acc3);padding:0 12px;color:var(--faint);gap:8px">{ic("search",15)}Додати товар</div></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px"><div><div class="lab">Оплата</div><div class="inp2"><i class="dt" style="background:#2E6BE6"></i>Контроль оплати НП<span style="margin-left:auto" class="fa">{ic("chevron-down",14)}</span></div><div class="hint ac" style="font-size:12.5px;margin-top:6px">У ТТН піде: контроль оплати · 1 899 ₴</div></div>
<div><div class="lab">Доставка</div><div class="inp2"><span class="np">НП</span>Київ, відділення №12<span style="margin-left:auto" class="fa">{ic("chevron-down",14)}</span></div><div style="font-size:12.5px;margin-top:6px" class="mut">ТТН з'явиться після створення</div></div></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px"><div><div class="lab">Джерело · Менеджер</div><div class="inp2">Лендинг · не призначено</div></div><div><div class="lab">Коментар</div><div class="inp2 fa">Коментар до замовлення</div></div></div>
<div style="background:#FDF1E3;border-radius:12px;padding:9px 12px;font-size:12.5px;color:#A85A04" class="row">{ic("circle-alert",14)}Можливий дубль №31 — той самий номер, товар і сума</div>
<span style="flex:1"></span>
<div class="row" style="gap:8px"><span class="mut" style="font-size:12.5px">J / K — наступне / попереднє · зберігається само</span><span style="flex:1"></span><span class="btn s">{ic("truck",16)}Створити ТТН</span><span class="btn p">{ic("check",16)}Прийняти й далі</span></div></div>'''
    body = f'''{hdr('<span class="seg"><span>Таблиця</span><span class="on">Скринька</span></span>')}<div class="row" style="margin-bottom:12px">{tabs([("Несортовані", 16, "#7C7B76", True, True)] + TABS[1:6])}</div>
<div class="row" style="align-items:stretch;gap:12px;flex:1;min-height:0;padding-bottom:16px"><div class="col" style="width:360px;flex:none;gap:2px;background:#ECEDF0;border-radius:18px;padding:6px;overflow:hidden">{items}</div>{right}</div>'''
    return frame("orders", body)


V = [("1", "1 · Щільна таблиця: рядок 40 px, усі колонки, дії при наведенні", l1), ("2", "2 · Два рядки в клітинці + панель перегляду праворуч", v18_orders),
     ("3", "3 · Групи «що робити зараз» з дією на всю групу", l3), ("4", "4 · Картки сіткою з дією в картці", l4), ("5", "5 · Скринька: список ліворуч, картка праворуч, J / K", l5)]


def build():
    return page("Список замовлень — 5 варіантів", CSS, [(k, n, f(), 1440, 900) for k, n, f in V], cols=1, gap=48)
