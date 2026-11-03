"""Покрокове нове замовлення — варіант A з правками власника (30.10):
1) телефон вище за ПІБ; 3) вид оплати — з усіх видів, великими значками, з пошуком; 4) доставка: для НП — «Створити ТТН» або
«Ввести готову ТТН», для інших перевізників — лише поле номера ТТН."""
from common import *
from v21_wizard import CSS as BASE21, STEPS, s2, s5, nav, shell
from v18_desktop import sq

CSS = BASE21 + """
.pt{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;height:96px;border-radius:16px;background:#F6F7F8;border:2px solid transparent;
  font-size:13px;font-weight:500;text-align:center;line-height:1.2;padding:6px;position:relative}
.pt .ic{width:44px;height:44px;border-radius:14px;display:grid;place-items:center;color:#fff;font:700 13px Onest;flex:none}
.pt.on{background:#fff;border-color:var(--acc);box-shadow:0 0 0 4px var(--acc2)}
.pt.on::after{content:"";position:absolute;top:8px;right:8px;width:18px;height:18px;border-radius:50%;background:var(--acc) url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='3.5' stroke-linecap='round' stroke-linejoin='round'><path d='M20 6 9 17l-5-5'/></svg>") center/11px no-repeat}
.pt small{font-weight:400;color:var(--mut);font-size:11.5px}
.sub{font-size:12.5px;color:var(--mut);margin:14px 4px 8px;display:flex;align-items:center;gap:8px}.sub::after{content:"";flex:1;height:1px;background:#EFEFED}
.mode{display:flex;gap:12px;align-items:flex-start;padding:16px;border-radius:16px;background:#F6F7F8;border:2px solid transparent;flex:1}
.mode.on{background:#fff;border-color:var(--acc);box-shadow:0 0 0 4px var(--acc2)}
.mode b{font-size:15px}.mode small{display:block;color:var(--mut);font-size:12.5px;margin-top:2px;line-height:1.35}
.mode .rd{margin-left:auto;width:22px;height:22px;border-radius:50%;border:2px solid #CFCEC9;flex:none}.mode.on .rd{border:7px solid var(--acc)}
.cr{display:flex;align-items:center;gap:10px;height:56px;padding:0 14px;border-radius:14px;background:#F6F7F8;border:2px solid transparent;font-size:14.5px;font-weight:500}
.cr.on{background:#fff;border-color:var(--acc);box-shadow:0 0 0 4px var(--acc2)}.cr small{font-weight:400;color:var(--mut);font-size:12px}
"""

DONE2 = ["+380 67 111 22 33 · Коваленко Олена", "Павербанк Volt 20 000 + кабель · 1 797 ₴", "Контроль оплати НП", "Нова Пошта · створити ТТН", "Instagram · Олена Литвин"]


# ---------------------------------------------------------------- 1. Телефон, потім ПІБ (за номером підтягується покупець)
def s1():
    return f'''<div class="q">Хто замовляє?</div><div class="qs">Почніть з телефону — якщо покупець уже є, ПІБ підставиться сам</div>
<div class="lb">Телефон</div><div class="big f"><span class="fl"></span><span class="mut">+380</span><b style="font-weight:500">67 111 22 33</b><span style="margin-left:auto;width:2px;height:24px;background:var(--acc)"></span></div>
<div class="found" style="margin-top:10px;font-size:13.5px;padding:10px 14px">{ic("circle-check-big",16)}<span>Покупець уже є: <b>4 замовлення · викуп 75%</b></span><span style="margin-left:auto;text-decoration:underline">показати</span></div>
<div class="lb" style="margin-top:16px">ПІБ<span class="ok" style="margin-left:6px;font-size:12px">· підставлено з бази</span></div><div class="big" style="font-weight:500">Коваленко Олена</div>
<div class="hint" style="margin-top:14px">{ic("plus",14)}Email</div>'''


# ---------------------------------------------------------------- 3. Вид оплати з усіх видів — великими значками й пошуком
PAYS = [  # (позначка, колір, назва, підпис, вибрано)
    ('<span style="font-size:12px">НП</span>', "#E5262B", "Контроль оплати", "НП · без комісії", True),
    (ic("hand-coins", 22), "#2E6BE6", "Післяплата", "грошовий переказ", False),
    (ic("wallet", 22), "#16A34A", "Передоплата", "частково або повна", False),
    ('<span style="font-size:13px">mono</span>', "#1F1F1C", "Monobank", "на рахунок ФОП", False),
    ('<span style="font-size:18px">П</span>', "#1C8E3C", "ПриватБанк", "на картку", False),
    (ic("credit-card", 22), "#6D5BD0", "Оплата карткою", "еквайринг на сайті", False),
    (ic("banknote", 22), "#0E9488", "Готівка", "у офісі", False),
    (ic("landmark", 22), "#57564F", "Рахунок IBAN", "для юросіб", False),
    ('<span style="font-size:16px">R</span>', "#16A34A", "RozetkaPay", "маркетплейс", False),
    ('<span style="font-size:15px">P</span>', "#7C3AED", "Пром-оплата", "маркетплейс", False),
    (ic("refresh-cw", 21), "#D97706", "Обмін", "без оплати", False),
    (ic("check", 22), "#16A34A", "Оплачено", "уже отримали", False),
]


def s3():
    tiles = "".join(f'<div class="pt{" on" if on else ""}"><span class="ic" style="background:{c}">{mark}</span><span>{n}<br><small>{sub}</small></span></div>' for mark, c, n, sub, on in PAYS)
    return f'''<div class="q">Як оплачує?</div><div class="qs">Від виду оплати залежить, що піде в ТТН · найчастіші — першими</div>
<div class="big" style="height:46px;font-size:15px;color:var(--faint)">{ic("search",18)}Знайти серед 47 видів оплати</div>
<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-top:12px">{tiles}</div>
<div class="row" style="margin-top:10px;justify-content:space-between"><span class="hint" style="color:var(--mut)">{ic("chevron-down",14)}Ще 35 видів оплати</span>
<span class="row" style="background:#EAF1FD;border-radius:12px;padding:8px 12px;color:#1F4FB8;font-size:13.5px;gap:6px">{ic("arrow-up-right",15)}У ТТН піде: <b>контроль оплати · 1 797 ₴</b></span></div>'''


# ---------------------------------------------------------------- 4. Доставка: перевізник; для НП — створити ТТН або ввести готову; для інших — лише номер
def carriers(sel):
    items = [("np1", '<span class="np" style="padding:6px">НП</span>', "Нова Пошта", "ФОП Максимчук О. В."), ("np2", '<span class="np" style="padding:6px">НП</span>', "Нова Пошта", "ФОП Максимчук Д. О."),
             ("ukr", sq("truck", "orange", True, 15), "Укрпошта", ""), ("meest", sq("package", "purple", True, 15), "Meest", ""), ("self", sq("store", "gray", True, 15), "Самовивіз", "")]
    return '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">' + "".join(
        f'<div class="cr{" on" if k == sel else ""}">{m}<span>{n}{f"<br><small>{sub}</small>" if sub else ""}</span></div>' for k, m, n, sub in items) + "</div>"


def s4_np():
    return f'''<div class="q">Як доставити?</div><div class="qs">Оберіть перевізника</div>{carriers("np1")}
<div class="sub">ТТН Нової Пошти</div>
<div class="row" style="gap:10px;align-items:stretch">
<div class="mode on">{sq("truck","blue",False,17)}<div><b>Створити ТТН</b><small>одразу після створення замовлення відкриється вікно ТТН: місто, відділення, платник, вага</small></div><span class="rd"></span></div>
<div class="mode">{sq("scan-barcode","gray",False,17)}<div><b>Ввести готову ТТН</b><small>посилку вже оформили в кабінеті НП — лише вставте номер</small></div><span class="rd"></span></div></div>
<div class="row" style="margin-top:12px;background:#F2F3F5;border-radius:14px;padding:11px 16px;color:#57564F;font-size:13.5px;gap:8px">{ic("hand-coins",16)}Післяплата 1 797 ₴ · контроль оплати · береться з оплати</div>'''


def s4_np_ready():
    return f'''<div class="q">Як доставити?</div><div class="qs">Оберіть перевізника</div>{carriers("np1")}
<div class="sub">ТТН Нової Пошти</div>
<div class="row" style="gap:10px;align-items:stretch">
<div class="mode">{sq("truck","blue",False,17)}<div><b>Створити ТТН</b><small>відкриється вікно ТТН після створення</small></div><span class="rd"></span></div>
<div class="mode on">{sq("scan-barcode","blue",False,17)}<div><b>Ввести готову ТТН</b><small>посилку вже оформили в кабінеті НП</small></div><span class="rd"></span></div></div>
<div class="lb" style="margin-top:14px">Номер ТТН</div><div class="big f" style="font:500 18px JB">20 4512 3456 7890<span style="margin-left:auto;font:500 13px Onest" class="ok row">{ic("circle-check-big",15)}знайдено: Тульчин, №3 · 1 797 ₴</span></div>'''


def s4_other():
    return f'''<div class="q">Як доставити?</div><div class="qs">Оберіть перевізника</div>{carriers("ukr")}
<div class="sub">ТТН Укрпошти</div>
<div class="lb">Номер відправлення</div><div class="big f" style="font:500 18px JB">0500 1234 5678 9<span style="width:2px;height:24px;background:var(--acc);margin-left:2px"></span></div>
<div class="hint" style="margin-top:10px;color:var(--mut)">{ic("circle-alert",14)}Для Укрпошти й Meest ТТН з CRM не створюється — введіть номер, коли оформите посилку. Можна пропустити й додати пізніше.</div>'''


# ---------------------------------------------------------------- рамка варіанта A (як погоджено), ширше вікно для значків оплати
def A(i, content, width=760, last_label=None):
    dots = "".join(f'{"<span class=" + chr(39) + "ln" + (" ok" if k <= i else "") + chr(39) + "></span>" if k else ""}<span class="dot2 {"ok" if k < i else "cur" if k == i else ""}"><i>{ic("check",13,3) if k < i else k + 1}</i>{n}</span>' for k, n in enumerate(STEPS))
    total = f'<div class="row" style="justify-content:center;gap:8px;margin-top:14px;font:400 13px Onest,sans-serif;color:#fff;opacity:.9">{ic("receipt-text",14)}Чернетка · {"1 797 ₴" if i > 1 else "товарів ще немає"} · зберігається сама</div>'
    n = nav(i)
    if i == 4:  # доставка НП із «Створити ТТН»: головна дія — створити й одразу відкрити вікно ТТН
        n = f'''<div class="row" style="gap:10px;margin-top:24px"><span class="btn g next">{ic("chevron-left",18)}Назад</span><span style="flex:1"></span>
<span class="btn g next">Створити без ТТН</span><span class="btn p next">{ic("truck",18)}Створити й оформити ТТН<span class="kb">Ctrl ⏎</span></span></div>'''
    card = f'''<div style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:{width}px">
<div class="win d" style="position:relative;inset:auto;display:block;width:{width}px;height:auto;padding:22px 34px 26px;background:#fff;border-radius:26px">
<div class="row" style="margin-bottom:22px"><b style="font-size:15px">Нове замовлення</b><span style="flex:1"></span><span class="rb" style="width:36px;height:36px;background:#F2F3F5">{ic("x",16)}</span></div>
<div class="dots" style="justify-content:center;margin-bottom:26px">{dots}</div>{content()}{n}</div>{total}</div>'''
    return shell(card, "")


V = [("1", "Крок 1 — телефон, потім ПІБ", A(0, s1)), ("2", "Крок 2 — товар", A(1, s2)), ("3", "Крок 3 — вид оплати великими значками", A(2, s3, 900)),
     ("4a", "Крок 4 — Нова Пошта: створити ТТН або ввести готову", A(3, s4_np, 820)), ("4b", "Крок 4 — НП: введено готову ТТН", A(3, s4_np_ready, 820)),
     ("4c", "Крок 4 — Укрпошта / Meest: лише номер", A(3, s4_other, 820)),
     ("5", "Крок 5 — джерело; для НП «Створити ТТН» — головна кнопка", A(4, s5, 760))]


def build():
    return page("Покрокове нове замовлення — варіант A, правки", CSS, [(k, n, h, 1440, 900) for k, n, h in V], cols=3, gap=40)
