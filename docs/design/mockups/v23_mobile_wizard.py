"""Телефон: покрокове нове замовлення (як погоджений варіант A на ПК) і нова ТТН у тому ж стилі.
Повноекранний потік без нижньої панелі: зверху хрестик, назва, «крок N з 5» і смуга прогресу; великі поля й плитки;
знизу — чернетка з сумою і кнопки Назад / Далі під великим пальцем."""
from common import *
from v17_mobile import CSS as BASE17, sq, st

CSS = BASE17 + """
.wt{display:flex;align-items:center;gap:10px;padding:16px 14px 12px}
.wt .ttl{flex:1;text-align:center;line-height:1.25}.wt .ttl b{font-size:16px}.wt .ttl small{display:block;color:var(--mut);font-size:12.5px}
.wt .ghost{width:44px;height:44px;flex:none}
.prog{display:flex;gap:5px;padding:0 18px}.prog i{flex:1;height:5px;border-radius:99px;background:#DCDDE1}.prog i.ok{background:#16A34A}.prog i.cur{background:var(--acc)}
.wq{font-size:26px;font-weight:600;letter-spacing:-.02em;padding:20px 18px 4px;line-height:1.15}
.wqs{font-size:14px;color:var(--mut);padding:0 18px 16px;line-height:1.35}
.wb{padding:0 14px}
.lb{font-size:13px;color:var(--mut);margin:0 0 6px 4px}
.big{height:58px;border-radius:17px;background:#fff;display:flex;align-items:center;gap:10px;padding:0 16px;font-size:19px;color:var(--ink)}
.big.f{border:2px solid var(--acc);box-shadow:0 0 0 4px var(--acc2)}.big.e{color:var(--faint)}
.big .fl{width:22px;height:16px;border-radius:4px;background:linear-gradient(#2E6BE6 50%,#F5C518 50%);flex:none}
.cur{width:2px;height:24px;background:var(--acc);flex:none}
.found{display:flex;align-items:center;gap:8px;margin-top:10px;padding:11px 14px;border-radius:14px;background:#E9F6EE;color:#13803D;font-size:13.5px}
.hint{display:flex;align-items:center;gap:6px;font-size:13.5px;color:var(--acc);font-weight:500}
.pt{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:7px;height:104px;border-radius:18px;background:#fff;border:2px solid transparent;
  font-size:13px;font-weight:500;text-align:center;line-height:1.2;padding:6px;position:relative}
.pt .ic{width:46px;height:46px;border-radius:15px;display:grid;place-items:center;color:#fff;font:700 13px Onest;flex:none}
.pt small{font-weight:400;color:var(--mut);font-size:11.5px}
.pt.on{border-color:var(--acc);box-shadow:0 0 0 4px var(--acc2)}
.pt.on::after{content:"";position:absolute;top:8px;right:8px;width:18px;height:18px;border-radius:50%;background:var(--acc) url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='3.5' stroke-linecap='round' stroke-linejoin='round'><path d='M20 6 9 17l-5-5'/></svg>") center/11px no-repeat}
.pt.more{background:transparent;border:2px dashed #D3D4D8;color:var(--acc)}
.cr{display:flex;align-items:center;gap:10px;height:60px;padding:0 12px;border-radius:16px;background:#fff;border:2px solid transparent;font-size:14.5px;font-weight:500;line-height:1.2}
.cr.on{border-color:var(--acc);box-shadow:0 0 0 4px var(--acc2)}.cr small{font-weight:400;color:var(--mut);font-size:11.5px}
.mode{display:flex;gap:12px;align-items:center;padding:14px;border-radius:18px;background:#fff;border:2px solid transparent}
.mode.on{border-color:var(--acc);box-shadow:0 0 0 4px var(--acc2)}
.mode b{font-size:15.5px}.mode small{display:block;color:var(--mut);font-size:12.5px;margin-top:1px;line-height:1.3}
.rd{margin-left:auto;width:22px;height:22px;border-radius:50%;border:2px solid #CFCEC9;flex:none;background:#fff}.on > .rd,.on .rd{border:7px solid var(--acc)}
.sub{font-size:13px;color:var(--mut);margin:16px 4px 8px;display:flex;align-items:center;gap:8px}.sub::after{content:"";flex:1;height:1px;background:#E2E3E6}
.gi{display:flex;align-items:center;gap:12px;padding:12px;border-radius:18px;background:#fff}
.vp{display:inline-flex;align-items:center;gap:5px;height:24px;padding:0 9px;border-radius:99px;background:var(--acc2);color:#1F4FB8;font-size:12.5px;font-weight:500}
.vp i{width:9px;height:9px;border-radius:3px;background:#151515}
.qty{display:flex;align-items:center;gap:14px;height:36px;border-radius:99px;background:#F2F3F5;padding:0 12px;color:var(--mut);font-size:17px}.qty b{color:var(--ink);font-size:15px}
.res{display:flex;align-items:center;gap:12px;padding:10px;border-radius:14px}.res.hl{background:var(--acc2)}
.offer{display:flex;align-items:center;gap:10px;min-height:52px;padding:8px 8px 8px 14px;border-radius:16px;border:1.5px dashed #D3D4D8;color:var(--mut);margin-top:10px;font-size:13.5px;line-height:1.3}
.offer b{color:var(--ink);font-weight:500}.offer .add{margin-left:auto;height:36px;padding:0 14px;border-radius:99px;background:var(--acc2);color:var(--acc);display:flex;align-items:center;gap:4px;font-weight:600;flex:none}
.sel{height:52px;border-radius:15px;background:#fff;display:flex;align-items:center;padding:0 14px;font-size:15px;justify-content:space-between;white-space:nowrap;overflow:hidden}
.bchip{height:44px;padding:0 16px;border-radius:14px;font-size:14.5px;font-weight:500;display:inline-flex;align-items:center;background:#fff}
.bchip.on{background:var(--acc);color:#fff}
.foot{position:absolute;left:0;right:0;bottom:0;padding:26px 14px 24px;background:linear-gradient(rgba(241,242,244,0),var(--bg) 22%)}
.draft{display:flex;align-items:center;justify-content:center;gap:7px;font-size:13px;color:var(--mut);margin-bottom:10px}
.draft b{color:var(--ink)}
.fb{display:flex;gap:10px}.fb .btn{height:56px;border-radius:18px;font-size:16px}
.fb .back{width:56px;flex:none;padding:0}
.kv2{display:flex;justify-content:space-between;font-size:14px;padding:5px 0}.kv2 span{color:var(--mut)}
.tg2{display:flex;align-items:center;gap:10px;font-size:14.5px;padding:9px 0}.tg2 .tgl{margin-left:auto}
.wh{display:flex;align-items:center;gap:12px;padding:11px 12px;border-radius:15px}.wh.on{background:var(--acc2)}
.wh b{font-weight:500}.wh small{color:var(--mut);font-size:12.5px}
.tag{font-size:11.5px;font-weight:500;padding:2px 7px;border-radius:99px;background:#F0F0EE;color:#57564F;white-space:nowrap}
.mt3{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:7px;height:96px;border-radius:18px;background:#fff;border:2px solid transparent;font-size:13.5px;font-weight:500;text-align:center;line-height:1.2}
.mt3 small{font-weight:400;color:var(--mut);font-size:11.5px}.mt3.on{border-color:var(--acc);box-shadow:0 0 0 4px var(--acc2)}
.act{display:flex;align-items:center;gap:12px;height:64px;border-radius:18px;background:#fff;padding:0 14px;font-size:14.5px;font-weight:500;line-height:1.25}
.act small{display:block;color:var(--mut);font-weight:400;font-size:12px}
"""

STEPS = ["Покупець", "Товар", "Оплата", "Доставка", "Джерело"]
NPB = '<span class="np" style="padding:6px">НП</span>'


def top(i, title="Нове замовлення", steps=STEPS, right=None):
    prog = "".join(f'<i class="{"ok" if k < i else "cur" if k == i else ""}"></i>' for k in range(len(steps)))
    return (f'<div class="wt"><span class="rb">{ic("x",20)}</span><span class="ttl"><b>{title}</b><small>Крок {i+1} з {len(steps)} · {steps[i]}</small></span>'
            f'{right or "<span class=ghost></span>"}</div><div class="prog">{prog}</div>')


def foot(i, total="1 797 ₴", last=False, primary="Далі", draft=True):
    d = f'<div class="draft">{ic("receipt-text",14)}Чернетка · <b>{total}</b> · зберігається сама</div>' if draft else ""
    if last:
        return f'''<div class="foot">{d}<div class="fb"><span class="btn p" style="flex:1">{ic("truck",19)}Створити й оформити ТТН</span></div>
<div class="row" style="justify-content:space-between;margin-top:12px;padding:0 6px"><span class="hint" style="color:var(--mut)">{ic("chevron-left",16)}Назад</span><span class="hint">Створити без ТТН</span></div></div>'''
    back = f'<span class="btn back">{ic("chevron-left",22)}</span>' if i else ""
    return f'<div class="foot">{d}<div class="fb">{back}<span class="btn p" style="flex:1">{primary}{ic("chevron-right",19)}</span></div></div>'


def q(t, s):
    return f'<div class="wq">{t}</div><div class="wqs">{s}</div>'


# ---------------------------------------------------------------- кроки
def m1():
    return top(0) + q("Хто замовляє?", "Почніть з телефону — якщо покупець уже є, ПІБ підставиться сам") + f'''<div class="wb">
<div class="lb">Телефон</div><div class="big f"><span class="fl"></span><span class="mut">+380</span><b style="font-weight:500">67 111 22 33</b><span class="cur"></span></div>
<div class="found">{ic("circle-check-big",16)}<span>Покупець уже є: <b>4 замовлення · викуп 75%</b></span><span style="margin-left:auto;text-decoration:underline">показати</span></div>
<div class="lb" style="margin-top:18px">ПІБ<span class="ok" style="margin-left:6px;font-size:12px">· підставлено з бази</span></div><div class="big" style="font-weight:500">Коваленко Олена</div>
<div class="hint" style="margin-top:16px;padding-left:4px">{ic("plus",15)}Email</div></div>''' + foot(0, "товарів ще немає")


def m2():
    res = "".join(f'<div class="res{" hl" if k == 0 else ""}"><span class="thumb">{ic("package",17)}</span><div style="flex:1;line-height:1.3;min-width:0"><b style="font-weight:500">{n}</b><br><small class="mut">{sku} · {qn}</small></div><b>{p} ₴</b></div>'
                  for k, (n, sku, qn, p) in enumerate([("Павербанк Volt 20 000", "PB-20", "18 шт · 3 кольори", "1 599"), ("Павербанк Volt 10 000", "PB-10", "42 шт", "999")]))
    return top(1) + q("Що замовляє?", "Назва, артикул або скан штрихкоду") + f'''<div class="wb">
<div class="row" style="gap:8px"><div class="big f" style="flex:1">{ic("search",20)}<span style="font-weight:500">павер</span><span class="cur"></span></div><span class="rb" style="width:58px;height:58px;border-radius:17px">{ic("scan-barcode",22)}</span></div>
<div class="c" style="margin:8px 0 0;padding:6px;box-shadow:0 12px 30px -12px rgba(31,31,28,.25)">{res}</div>
<div class="lb" style="margin-top:16px">У замовленні · 1 товар</div>
<div class="gi"><span class="thumb">{ic("zap",17)}</span><div style="flex:1;min-width:0;line-height:1.3"><b style="font-weight:500">Павербанк Volt 20 000</b><div class="row" style="gap:8px;margin-top:5px"><span class="vp"><i></i>Чорний{ic("chevron-down",11)}</span><b>1 599 ₴</b></div></div>
<span class="qty"><span>−</span><b>1</b><span>+</span></span></div>
<div class="offer">{ic("sparkles",16)}<span>Часто беруть разом:<br><b>Кабель USB-C 1 м</b> · 198 ₴</span><span class="add">{ic("plus",15)}Додати</span></div></div>''' + foot(1, "1 599 ₴")


PAYS = [('<span style="font-size:12px">НП</span>', "#E5262B", "Контроль оплати", "НП", True),
        (ic("hand-coins", 22), "#2E6BE6", "Післяплата", "переказ", False),
        (ic("wallet", 22), "#16A34A", "Передоплата", "частково", False),
        ('<span style="font-size:13px">mono</span>', "#1F1F1C", "Monobank", "рахунок ФОП", False),
        ('<span style="font-size:18px">П</span>', "#1C8E3C", "ПриватБанк", "на картку", False),
        (ic("credit-card", 22), "#6D5BD0", "Картка", "на сайті", False),
        (ic("banknote", 22), "#0E9488", "Готівка", "в офісі", False),
        (ic("landmark", 22), "#57564F", "IBAN", "юрособи", False)]


def m3():
    tiles = "".join(f'<div class="pt{" on" if on else ""}"><span class="ic" style="background:{c}">{mark}</span><span>{n}<br><small>{s}</small></span></div>' for mark, c, n, s, on in PAYS)
    tiles += f'<div class="pt more">{ic("layout-grid",24)}<span>Усі види<br><small style="color:var(--acc)">ще 39</small></span></div>'
    return top(2) + q("Як оплачує?", "Найчастіші — першими") + f'''<div class="wb">
<div class="big" style="height:50px;font-size:15.5px;color:var(--faint);border-radius:15px">{ic("search",18)}Знайти серед 47 видів оплати</div>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:10px">{tiles}</div>
<div class="row" style="margin-top:10px;background:#EAF1FD;border-radius:14px;padding:11px 14px;color:#1F4FB8;font-size:13.5px;gap:7px">{ic("arrow-up-right",15)}У ТТН піде: <b>контроль оплати · 1 797 ₴</b></div></div>''' + foot(2)


def carriers(sel):
    items = [("np1", NPB, "Нова Пошта", "ФОП О. В."), ("np2", NPB, "Нова Пошта", "ФОП Д. О."),
             ("ukr", sq("truck", "orange", True, 15), "Укрпошта", ""), ("meest", sq("package", "purple", True, 15), "Meest", "")]
    g = "".join(f'<div class="cr{" on" if k == sel else ""}">{m}<span>{n}{f"<br><small>{s}</small>" if s else ""}</span></div>' for k, m, n, s in items)
    return f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">{g}</div><div class="hint" style="margin:10px 0 0 4px;color:var(--mut)">{ic("store",15)}Самовивіз · кур\'єр по місту<span style="margin-left:2px">{ic("chevron-down",13)}</span></div>'


def m4a():
    return top(3) + q("Як доставити?", "Перевізник і що робимо з ТТН") + f'''<div class="wb">{carriers("np1")}
<div class="sub">ТТН Нової Пошти</div>
<div class="mode on">{sq("truck","blue",False,17)}<div><b>Створити ТТН</b><small>після створення відкриється вікно ТТН</small></div><span class="rd"></span></div>
<div class="mode" style="margin-top:8px">{sq("scan-barcode","gray",False,17)}<div><b>Ввести готову ТТН</b><small>уже оформили в кабінеті НП</small></div><span class="rd"></span></div></div>''' + foot(3)


def m4b():
    return top(3) + q("Як доставити?", "Перевізник і що робимо з ТТН") + f'''<div class="wb">{carriers("np1")}
<div class="sub">ТТН Нової Пошти</div>
<div class="seg" style="background:#E3E4E8;margin-bottom:12px"><span>Створити ТТН</span><span class="on">Ввести готову</span></div>
<div class="lb">Номер ТТН</div><div class="big f" style="font:500 19px JB">20 4512 3456 7890</div>
<div class="found">{ic("circle-check-big",16)}<span>Знайдено: <b>Тульчин, №3 · 1 797 ₴</b> · отримувач збігається</span></div>
<div class="hint" style="margin-top:12px;padding-left:4px">{ic("scan-barcode",15)}Сканувати з наклейки</div></div>''' + foot(3)


def m4c():
    return top(3) + q("Як доставити?", "Перевізник і номер відправлення") + f'''<div class="wb">{carriers("ukr")}
<div class="sub">ТТН Укрпошти</div>
<div class="lb">Номер відправлення</div><div class="big f" style="font:500 19px JB">0500 1234 5678 9<span class="cur" style="margin-left:-6px"></span></div>
<div class="row" style="margin-top:12px;background:#E8E9EC;border-radius:14px;padding:12px 14px;color:#57564F;font-size:13.5px;gap:8px;align-items:flex-start;line-height:1.35">{ic("circle-alert",16)}<span>Для Укрпошти й Meest ТТН з CRM не створюється. Номер можна додати й пізніше.</span></div></div>''' + foot(3, primary="Далі")


def m5():
    ch = lambda items: '<div class="row" style="gap:8px;flex-wrap:wrap">' + "".join(f'<span class="bchip{" on" if on else ""}">{x}</span>' for x, on in items) + "</div>"
    v = lambda t: f'<div class="sel">{t}<span class="fa">{ic("chevron-down",16)}</span></div>'
    return top(4) + q("Звідки замовлення?", "Останній крок") + f'''<div class="wb">
<div class="lb">Джерело</div>{ch([("Instagram", True), ("Лендинг", False), ("TikTok", False), ("Дзвінок", False), ("Rozetka", False), ("Ще…", False)])}
<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:16px"><div><div class="lb">Менеджер</div>{v("Олена Литвин")}</div><div><div class="lb">Відділ</div>{v("Магазин")}</div>
<div><div class="lb">Юрособа</div>{v("ФОП Максимчук")}</div><div><div class="lb">Позначка</div>{v('<span class="fa">немає</span>')}</div></div>
<div class="lb" style="margin-top:14px">Коментар</div><div class="big e" style="height:56px;font-size:15px">Для складу чи кур'єра…</div>
<div class="row" style="gap:16px;margin-top:12px;padding-left:4px"><span class="hint">Поля 1–4{ic("chevron-down",14)}</span><span class="hint">UTM і сайт{ic("chevron-down",14)}</span></div></div>''' + foot(4, last=True)


# ---------------------------------------------------------------- ТТН на телефоні: 2 кроки + готово
TS = ["Куди", "Посилка й оплата"]


def key_chip():
    return f'<div class="row" style="gap:8px;margin:14px 14px 0;background:#fff;border-radius:15px;padding:10px 12px;font-size:13.5px">{NPB}<span style="flex:1;line-height:1.25">ФОП Максимчук О. В.<br><small class="mut">основний ключ · відправник</small></span>{ic("chevron-down",16)}</div>'


def t1():
    whs = [("Відділення №1", "вул. Леонтовича, 46", "8:00–20:00", False), ("Відділення №3", "вул. Шевченка, 12", "9:00–19:00", True), ("Поштомат №5718", "АТБ, вул. Гагаріна, 5", "цілодобово", False)]
    lst = "".join(f'<div class="wh{" on" if on else ""}"><span style="flex:1;line-height:1.3"><b>{n}</b><br><small>{a} · {h}</small></span><span class="rd"></span></div>' for n, a, h, on in whs)
    modes = "".join(f'<div class="mt3{" on" if on else ""}">{sq(i, t, False, 17)}<span>{n}<br><small>{s}</small></span></div>' for i, t, n, s, on in
                    [("store", "blue", "Відділення", "до 30 кг", True), ("package", "purple", "Поштомат", "до 20 кг", False), ("truck", "orange", "Кур'єр", "+35 ₴", False)])
    return top(0, "Нова ТТН · №27", TS) + key_chip() + f'''<div class="wb" style="margin-top:12px">
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px">{modes}</div>
<div class="lb" style="margin-top:14px">Місто</div><div class="big" style="font-weight:500;height:54px">Тульчин<span class="mut" style="font-weight:400;font-size:13.5px">Вінницька обл.</span></div>
<div class="lb" style="margin-top:12px">Відділення</div><div class="big f" style="height:54px">{ic("search",19)}<span style="font-weight:500">3</span><span class="cur"></span><span class="mut" style="font-size:13px;margin-left:auto">12 у місті</span></div>
<div class="c" style="margin:8px 0 0;padding:5px;box-shadow:0 12px 30px -12px rgba(31,31,28,.25)">{lst}</div></div>
<div class="foot"><div class="draft">{ic("truck",14)}Доставка <b>≈ 85 ₴</b> · завтра, 31 жовтня</div><div class="fb"><span class="btn p" style="flex:1">Далі{ic("chevron-right",19)}</span></div></div>'''


def t2():
    payer = "".join(f'<div class="mt3{" on" if on else ""}" style="height:60px;flex-direction:row;gap:9px">{sq(i, t, True, 15)}{n}</div>' for i, t, n, on in
                    [("user", "blue", "Отримувач", True), ("store", "gray", "Відправник", False)])
    return top(1, "Нова ТТН · №27", TS) + q("Посилка й оплата", "Усе підставлено з замовлення — перевірте") + f'''<div class="wb">
<div class="lb">Хто платить за доставку</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">{payer}</div>
<div class="c" style="margin:12px 0 0;padding:12px 14px">
<div class="row" style="gap:10px">{sq("package","gray",True,15)}<span style="flex:1;line-height:1.3"><b style="font-weight:500">Посилка · 0,3 кг</b><br><small class="mut">20 × 15 × 10 см · 1 місце · «Павербанк»</small></span><span class="hint">Змінити</span></div>
<div class="sep"></div>
<div class="kv2"><span>Контроль оплати</span><b>1 797 ₴</b></div><div class="kv2"><span>Оголошена вартість</span><b>1 797 ₴</b></div></div>
<div class="lb" style="margin-top:14px">Одразу після створення</div>
<div class="c" style="margin:0;padding:4px 14px">
<div class="tg2">{ic("printer",17)}Друкувати наклейку<span class="tgl on"></span></div>
<div class="tg2">{ic("list-checks",17)}У реєстр на сьогодні<span class="tgl on"></span></div>
<div class="tg2">{ic("message-square",17)}SMS покупцю з ТТН<span class="tgl on"></span></div></div></div>
<div class="foot"><div class="row" style="justify-content:space-between;background:#EAF1FD;border-radius:16px;padding:10px 14px;margin-bottom:10px;color:#1F4FB8">
<span style="line-height:1.25"><small style="font-size:12px">Доставка · платить отримувач</small><br><b style="font-size:20px">≈ 85 ₴</b></span><span class="row" style="gap:6px;font-size:13.5px">{ic("calendar",15)}завтра, 31 жовт.</span></div>
<div class="fb"><span class="btn back">{ic("chevron-left",22)}</span><span class="btn p" style="flex:1">{ic("truck",19)}Створити ТТН</span></div></div>'''


def t3():
    acts = [("printer", "blue", "Друкувати наклейку", "100 × 100 мм"), ("message-square", "purple", "SMS із ТТН надіслано", "покупцю, щойно"),
            ("list-checks", "green", "Додано в реєстр", "на 30 жовтня")]
    tiles = "".join(f'<div class="act" style="margin-bottom:8px">{sq(i, t, False, 17)}<span>{n}<small>{s}</small></span>{"<span class=hint style=margin-left:auto>Ще раз</span>" if i == "printer" else ""}</div>' for i, t, n, s in acts)
    return f'''<div class="wt"><span class="rb">{ic("x",20)}</span><span class="ttl"><b>Нова ТТН · №27</b><small>Готово</small></span><span class="ghost"></span></div>
<div style="text-align:center;padding:26px 18px 0"><div style="width:84px;height:84px;border-radius:50%;background:#E9F6EE;color:#16A34A;display:grid;place-items:center;margin:0 auto">{ic("check",42,2.6)}</div>
<div style="font-size:26px;font-weight:600;letter-spacing:-.02em;margin:16px 0 8px">ТТН створено</div>
<div class="row" style="justify-content:center;gap:10px">{NPB}<span style="font:600 23px JB;letter-spacing:.01em">20 4512 3456 7890</span></div>
<div class="row" style="justify-content:center;margin-top:12px"><span class="chip" style="height:38px;padding:0 16px;font-size:14px">{ic("copy",15)}Скопіювати</span></div>
<div class="mut" style="margin-top:12px;font-size:14px;line-height:1.4">Тульчин, відділення №3<br>доставка завтра · ≈ 85 ₴ · платить отримувач</div></div>
<div class="wb" style="margin-top:20px">{tiles}</div>
<div class="foot"><div class="fb"><span class="btn" style="flex:1">Замовлення</span><span class="btn p" style="flex:1.4">Готово</span></div></div>'''


V = [("1", "Крок 1 — телефон, потім ПІБ", m1()), ("2", "Крок 2 — товар", m2()), ("3", "Крок 3 — вид оплати великими значками", m3()),
     ("4a", "Крок 4 — НП: створити ТТН або ввести готову", m4a()), ("4b", "Крок 4 — НП: введено готову ТТН", m4b()),
     ("4c", "Крок 4 — Укрпошта / Meest: лише номер", m4c()), ("5", "Крок 5 — джерело й створення", m5()),
     ("ttn1", "ТТН 1 — куди: спосіб, місто, відділення", t1()), ("ttn2", "ТТН 2 — посилка й оплата, ціна над кнопкою", t2()), ("ttn3", "ТТН — готово", t3())]


def build():
    return page("Телефон: покрокове замовлення й ТТН", CSS, [(k, n, f'<div class="m">{h}</div>', 390, 844) for k, n, h in V], cols=5, gap=36)
