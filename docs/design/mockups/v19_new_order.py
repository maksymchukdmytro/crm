"""Нове замовлення на ПК — 5 варіантів. Правила власника: покупець (ПІБ, телефон) → товари → оплата → доставка; товари найбільші,
рядок товару низький; деталі компактні (Джерело | Менеджер, Відділ | Юрособа, коментар 2×2), поля 1–4 і UTM згорнуті;
окремого «Зберегти» немає — «Створити ТТН» завжди активна й сама створює замовлення; місто й відділення — у вікні ТТН;
жодних плиток, історії й «Що лишилось» у новому замовленні."""
from common import *
from v18_desktop import CSS as BASE, sidebar, st, sq

CSS = BASE + """
.ov{position:absolute;inset:0;background:rgba(24,24,22,.36)}
.win{position:absolute;left:24px;right:24px;top:20px;bottom:20px;background:var(--bg);border-radius:22px;display:flex;flex-direction:column;overflow:hidden}
.wh{display:flex;align-items:center;gap:12px;padding:12px 16px;background:#fff;flex:none}
.wb{flex:1;min-height:0;padding:12px;display:grid;gap:12px}
.stp{width:22px;height:22px;border-radius:50%;display:grid;place-items:center;font-size:11.5px;font-weight:600;flex:none;background:#ECEDEF;color:#57564F}
.stp.ok{background:#16A34A;color:#fff}.stp.cur{background:var(--acc);color:#fff}
.bh{display:flex;align-items:center;gap:9px;font-size:15.5px;font-weight:600;margin-bottom:10px}.bh .r{margin-left:auto;display:flex;gap:6px}
.gi{display:grid;grid-template-columns:32px minmax(0,1fr) auto 104px 84px 20px;align-items:center;gap:10px;height:46px;padding:0 10px;border-radius:12px;background:#F6F7F8}
.gi.up{margin-left:28px;background:#FAFAFB}
.gi .nm{display:flex;align-items:center;gap:8px;min-width:0;white-space:nowrap}.gi .nm b{font-weight:500;overflow:hidden;text-overflow:ellipsis}
.qty{display:flex;align-items:center;justify-content:space-between;height:30px;border-radius:99px;background:#fff;padding:0 10px;color:var(--faint)}.qty b{color:var(--ink)}
.vp{display:inline-flex;align-items:center;gap:5px;height:22px;padding:0 8px;border-radius:99px;background:var(--acc2);color:#1F4FB8;font-size:12px;font-weight:500;flex:none}
.vp i{width:8px;height:8px;border-radius:3px;background:#151515}
.gsrch{display:flex;align-items:center;gap:8px;height:42px;padding:0 14px;border-radius:12px;border:1.5px solid var(--acc3);background:#fff;color:var(--faint);margin-top:8px}
.offer{display:flex;align-items:center;gap:10px;height:40px;padding:0 6px 0 12px;border-radius:12px;border:1px dashed #D6D6D3;color:var(--mut);margin-top:8px;font-size:13px}
.offer b{color:var(--ink);font-weight:500}.offer .add{margin-left:auto;height:30px;padding:0 12px;border-radius:99px;background:var(--acc2);color:var(--acc);display:flex;align-items:center;gap:4px;font-weight:500}
.ph{display:flex;align-items:center;gap:8px;height:42px;border-radius:12px;padding:0 12px;background:#fff;border:1.5px solid var(--acc);box-shadow:0 0 0 3px var(--acc2);font-size:15px}
.ph .fl{width:18px;height:13px;border-radius:3px;background:linear-gradient(#2E6BE6 50%,#F5C518 50%)}
.in{display:flex;align-items:center;gap:8px;height:42px;border-radius:12px;padding:0 12px;background:#F6F7F8;font-size:14px}.in.ph2{color:var(--faint)}.in .cv{margin-left:auto;color:var(--faint)}
.found{display:flex;align-items:center;gap:8px;margin-top:8px;padding:7px 10px;border-radius:10px;background:#E9F6EE;color:#13803D;font-size:12.5px}
.hint{display:flex;align-items:center;gap:6px;font-size:12.5px;color:var(--acc)}
.ro{display:flex;align-items:center;gap:8px;height:40px;border-radius:12px;padding:0 12px;background:#F2F3F5;color:#57564F;font-size:13px}
.det{display:grid;grid-template-columns:76px 1fr 76px 1fr;align-items:center;gap:8px 10px;font-size:13px}
.det span{color:var(--mut)}.det .v{height:34px;border-radius:10px;background:#F6F7F8;display:flex;align-items:center;justify-content:space-between;padding:0 10px;color:var(--ink)}
.det .cm{grid-column:2 / -1;height:52px;align-items:flex-start;padding-top:8px;color:var(--faint)}
.fold{display:flex;gap:16px;font-size:13px;color:var(--acc);margin-top:8px}.fold span{display:flex;align-items:center;gap:3px}
.sum{background:#EAF1FD;border-radius:18px;padding:16px 18px;display:flex;flex-direction:column}
.sum .big{font-size:34px;font-weight:600;letter-spacing:-.02em;color:#1F4FB8;line-height:1.1}
.sum .kv{font-size:13px}
.acts{display:flex;gap:8px}.acts .btn{height:46px}
.lst{position:absolute;inset:0;padding:16px 24px 0 256px;opacity:.9}
"""

C = "Коваленко Олена"


def bg_list():
    rows = "".join(f'<div class="row" style="height:56px;border-top:1px solid #F2F2F0;padding:0 16px;gap:20px"><b class="num" style="width:40px">№{44-k}</b><span style="width:180px">{n}</span><span style="flex:1" class="mut">Товар</span>{st(s)}</div>'
                   for k, (n, s) in enumerate([("Олена Коваль", "uns"), ("Андрій Мельник", "uns"), ("Микола Бондаренко", "acc"), ("Ірина Савчук", "acc"), ("Тарас Ткаченко", "sent"), ("Денис Мельник", "wait"), ("Олег Бондаренко", "done"), ("Інна Ковальчук", "done"), ("Віктор Поліщук", "ref")]))
    return f'<div class="d">{sidebar("orders")}<main class="mn"><div class="hd"><div><h1>Замовлення</h1></div></div><div class="tb">{rows}</div></main></div>'


def wrap(head, body, cols):
    return f'''<div style="position:relative;width:1440px;height:900px">{bg_list()}<div class="ov"></div>
<div class="win d" style="display:flex;grid-template-columns:none;width:auto;height:auto">{head}<div class="wb" style="{cols}">{body}</div></div></div>'''


def whead(extra="", ttn=True):
    return f'''<div class="wh"><span class="rb" style="background:#F2F3F5">{ic("chevron-left",19)}</span><b style="font-size:18px">Нове замовлення</b>
<span class="mut" style="font-size:13px">чернетка · не збережено</span><span style="flex:1"></span>{extra}
{f'<span class="btn s">{ic("truck",17)}Створити ТТН<span style="font:500 11px JB;opacity:.6">Ctrl ⏎</span></span>' if ttn else ""}
<span class="btn p">{ic("check",17)}Створити замовлення</span><span class="rb" style="background:#F2F3F5">{ic("x",18)}</span></div>'''


def step(n, state, title, right=""):
    mark = ic("check", 12, 3) if state == "ok" else str(n)
    return f'<div class="bh"><span class="stp {state}">{mark}</span>{title}{f"<span class=r>{right}</span>" if right else ""}</div>'


def customer(found=True, compact=False):
    f = f'<div class="found">{ic("circle-check-big",14)}<span>Знайдено: <b>4 замовлення · викуп 75%</b></span><span style="margin-left:auto;text-decoration:underline;white-space:nowrap">інші ▾</span></div>' if found else ""
    if compact:
        return f'''<div class="c" style="padding:12px 16px">{step(1,"ok","Покупець")}
<div style="display:grid;grid-template-columns:1.3fr 1fr auto;gap:10px;align-items:center"><div class="in" style="font-size:15px;font-weight:500">{C}</div>
<div class="ph"><span class="fl"></span><span class="mut">+380</span><b style="font-weight:500">67 111 22 33</b></div><span class="hint" style="white-space:nowrap">{ic("plus",13)}Email</span></div>{f}</div>'''
    return f'''<div class="c">{step(1,"ok","Покупець")}
<div class="lab">ПІБ одним рядком</div><div class="in" style="font-size:15px;font-weight:500;margin-bottom:10px">{C}</div>
<div class="lab">Телефон</div><div class="ph"><span class="fl"></span><span class="mut">+380</span><b style="font-weight:500">67 111 22 33</b></div>
{f}<div class="hint" style="margin-top:10px">{ic("plus",13)}Email</div></div>'''


def goods(fill=True, big=True, offer=True):
    rows = f'''<div class="gi"><span class="th" style="width:32px;height:32px;border-radius:9px">{ic("zap",15)}</span><span class="nm"><b>Павербанк Volt 20 000 мА·год</b><span class="vp"><i></i>Чорний{ic("chevron-down",11)}</span><small class="fa">PB-20 · 18 шт</small></span><span></span>
<span class="qty"><span>−</span><b>1</b><span>+</span></span><b class="num" style="text-align:right">1 599 ₴</b><span class="fa">{ic("x",14)}</span></div>
<div class="gi up" style="margin-top:6px"><span class="th" style="width:32px;height:32px;border-radius:9px;background:#fff">{ic("link",14)}</span><span class="nm"><b>Кабель USB-C → USB-C 1 м</b><small class="fa">допродаж · CB-C1</small></span><span></span>
<span class="qty"><span>−</span><b>1</b><span>+</span></span><b class="num" style="text-align:right">198 ₴</b><span class="fa">{ic("x",14)}</span></div>'''
    off = f'<div class="offer">{ic("sparkles",15)}Часто беруть разом: <b>Чохол для павербанка</b> · 249 ₴<span class="add">{ic("plus",14)}Додати</span></div>' if offer else ""
    tot = '<div class="row" style="gap:22px;margin-top:12px;font-size:13.5px"><span><span class="mut">Товари</span> <b>1 797 ₴</b></span><span class="row" style="gap:6px"><span class="mut">Знижка</span><span style="height:30px;width:70px;border-radius:9px;background:#F6F7F8;display:flex;align-items:center;justify-content:flex-end;padding:0 8px" class="fa">0 ₴</span></span><span><span class="mut">Собівартість · прибуток</span> <b>1 020 ₴ · <span class="ok">777 ₴</span></b></span></div>'
    return f'''<div class="c" style="display:flex;flex-direction:column;{"flex:1;" if big else ""}">{step(2,"ok","Товари",'<span class="btn sm g">'+ic("plus",14)+'Товар</span><span class="btn sm g">'+ic("sparkles",14)+'Допродаж</span>')}
{rows if fill else ""}<div class="gsrch">{ic("search",16)}Додати товар: назва, артикул або штрихкод<span style="margin-left:auto;font:500 11px JB" class="fa">/</span></div>{off}<span style="flex:1"></span>{tot}</div>'''


def payment():
    return f'''<div class="c">{step(3,"cur","Оплата")}
<div class="in"><span style="width:10px;height:10px;border-radius:50%;background:#2E6BE6"></span>Контроль оплати НП<span class="cv">{ic("chevron-down",15)}</span></div>
<div class="hint" style="margin-top:8px">{ic("arrow-up-right",13)}У ТТН піде: контроль оплати · 1 797 ₴</div>
<div class="hint" style="margin-top:6px;color:var(--mut)">{ic("plus",13)}Передоплата</div></div>'''


def delivery():
    return f'''<div class="c">{step(4,"","Доставка")}
<div class="in"><span class="np">НП</span>Нова Пошта · ФОП Максимчук<span class="cv">{ic("chevron-down",15)}</span></div>
<div class="ro" style="margin-top:8px">{ic("hand-coins",15)}Післяплата 1 797 ₴ · контроль оплати · з оплати</div>
<div class="hint" style="margin-top:8px;color:var(--mut)">{ic("map-pin",13)}Місто, відділення й платник — у вікні «Створити ТТН»</div></div>'''


def details(cols2=True):
    if not cols2:
        cell = lambda l, v: f'<div><div class="lab">{l}</div><div class="v" style="height:36px;border-radius:10px;background:#F6F7F8;display:flex;align-items:center;justify-content:space-between;padding:0 10px;font-size:13px;white-space:nowrap;overflow:hidden">{v}{ic("chevron-down",13)}</div></div>'
        return f'''<div class="c" style="padding:14px 16px"><div class="bh" style="margin-bottom:8px">{sq("list","gray",True,13)}Деталі</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">{cell("Джерело","Instagram")}{cell("Менеджер","Олена Литвин")}{cell("Відділ","Інтернет-магазин")}{cell("Юрособа","ФОП Максимчук")}
<div style="grid-column:1 / -1"><div class="lab">Коментар</div><div style="height:58px;border-radius:10px;background:#F6F7F8;padding:9px 10px;font-size:13px" class="fa">Коментар до замовлення</div></div></div>
<div class="fold"><span>Поля 1–4{ic("chevron-down",13)}</span><span>UTM і сайт{ic("chevron-down",13)}</span><span>Позначка{ic("chevron-down",13)}</span></div></div>'''
    return f'''<div class="c" style="padding:14px 16px"><div class="bh" style="margin-bottom:8px">{sq("list","gray",True,13)}Деталі</div>
<div class="det"><span>Джерело</span><div class="v">Instagram{ic("chevron-down",13)}</div><span>Менеджер</span><div class="v">Олена Литвин{ic("chevron-down",13)}</div>
<span>Відділ</span><div class="v">Інтернет-магазин{ic("chevron-down",13)}</div><span>Юрособа</span><div class="v">ФОП Максимчук О. В.{ic("chevron-down",13)}</div>
<span style="align-self:start;padding-top:8px">Коментар</span><div class="v cm">Коментар до замовлення</div></div>
<div class="fold"><span>Поля 1–4{ic("chevron-down",13)}</span><span>UTM і сайт{ic("chevron-down",13)}</span><span>Позначка{ic("chevron-down",13)}</span></div></div>'''


def summary(buttons=True, tall=True):
    b = f'<span style="flex:1"></span><div class="col" style="gap:8px;margin-top:12px"><span class="btn s" style="height:46px;background:#fff">{ic("truck",17)}Створити ТТН</span><span class="btn p" style="height:46px">{ic("check",17)}Створити замовлення</span></div>' if buttons else ""
    return f'''<div class="sum" style="{"flex:1;" if tall else ""}"><small class="mut">До сплати при отриманні</small><div class="big">1 797 <span style="font-size:22px">₴</span></div>
<div class="sep" style="background:#C9DBFA"></div><div class="kv"><span>Товари</span><b>1 797 ₴</b></div><div class="kv"><span>Знижка</span><b>0 ₴</b></div><div class="kv"><span>Оплата</span><b style="font-weight:500">Контроль оплати НП</b></div><div class="kv"><span>Доставка</span><b style="font-weight:500">Нова Пошта</b></div>{b}</div>'''


# ---------------------------------------------------------------- 1. Як погоджений макет: 4/12 ліворуч, товари праворуч, знизу деталі + підсумок
def v1():
    body = f'''<div class="col" style="gap:12px">{customer()}{payment()}{delivery()}</div>
<div class="col" style="gap:12px;min-width:0">{goods()}<div style="display:grid;grid-template-columns:1fr 300px;gap:12px">{details()}{summary(False,False)}</div></div>'''
    return wrap(whead(), body, "grid-template-columns:400px 1fr")


# ---------------------------------------------------------------- 2. Кроки зверху вниз посередині, праворуч закріплений підсумок з кнопками
def v2():
    body = f'''<div class="col" style="gap:12px;min-width:0">{customer(compact=True)}{goods()}
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">{payment()}{delivery()}</div></div>
<div class="col" style="gap:12px">{summary(True,False)}{details(False)}</div>'''
    return wrap(whead(ttn=False).replace('<span class="btn p">' + ic("check", 17) + 'Створити замовлення</span>', ""), body, "grid-template-columns:1fr 380px")


# ---------------------------------------------------------------- 3. Покупець смугою зверху, товари великі, оплата й доставка праворуч, деталі знизу смугою
def v3():
    det = f'''<div class="c" style="grid-column:1 / -1;padding:12px 16px"><div class="row" style="gap:10px;font-size:13px">{sq("list","gray",True,13)}<b style="font-size:14.5px">Деталі</b>
<span class="mut" style="margin-left:8px">Джерело</span><span class="chip" style="background:#F6F7F8;height:30px">Instagram{ic("chevron-down",12)}</span><span class="mut">Менеджер</span><span class="chip" style="background:#F6F7F8;height:30px">Олена Литвин{ic("chevron-down",12)}</span>
<span class="mut">Відділ</span><span class="chip" style="background:#F6F7F8;height:30px">Інтернет-магазин{ic("chevron-down",12)}</span><span class="mut">Юрособа</span><span class="chip" style="background:#F6F7F8;height:30px">ФОП Максимчук{ic("chevron-down",12)}</span>
<span class="in ph2" style="flex:1;height:30px">Коментар…</span><span class="ac row" style="gap:3px">Поля 1–4{ic("chevron-down",12)}</span><span class="ac row" style="gap:3px">UTM{ic("chevron-down",12)}</span></div></div>'''
    body = f'''<div style="grid-column:1 / -1">{customer(compact=True)}</div>{goods()}<div class="col" style="gap:12px">{payment()}{delivery()}{summary(False,True)}</div>{det}'''
    return wrap(whead(), body, "grid-template-columns:1fr 380px;grid-template-rows:auto 1fr auto")


# ---------------------------------------------------------------- 4. Три колонки: покупець + деталі · товари · оплата, доставка, підсумок з кнопками
def v4():
    body = f'''<div class="col" style="gap:12px">{customer()}{details(False)}</div>{goods()}
<div class="col" style="gap:12px">{payment()}{delivery()}{summary(True,True)}</div>'''
    return wrap(whead(ttn=False).replace('<span class="btn p">' + ic("check", 17) + 'Створити замовлення</span>', ""), body, "grid-template-columns:330px 1fr 330px")


# ---------------------------------------------------------------- 5. Швидке введення: одна форма згори вниз, вибір оплати й доставки пігулками, знизу смуга з сумою
def v5():
    pills = lambda items: '<div class="row" style="gap:6px;flex-wrap:wrap">' + "".join(f'<span class="chip" style="height:38px;border-radius:12px;{"background:var(--acc);color:#fff" if on else "background:#F6F7F8"}">{x}</span>' for x, on in items) + "</div>"
    body = f'''<div class="col" style="gap:12px;min-width:0;max-width:1040px;width:100%;justify-self:center">
{customer(compact=True)}{goods(big=True)}
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
<div class="c">{step(3,"cur","Оплата")}{pills([("Контроль оплати НП", True), ("Післяплата", False), ("Передоплата", False), ("Оплачено", False), ("Ще 43 ▾", False)])}<div class="hint" style="margin-top:8px">{ic("arrow-up-right",13)}У ТТН піде: контроль оплати · 1 797 ₴</div></div>
<div class="c">{step(4,"","Доставка")}{pills([("<span class=np>НП</span> Нова Пошта", True), ("Укрпошта", False), ("Meest", False), ("Самовивіз", False)])}<div class="hint" style="margin-top:8px;color:var(--mut)">{ic("map-pin",13)}Місто й відділення — у вікні «Створити ТТН»</div></div></div>
<div class="row" style="gap:16px;font-size:13px;padding:0 6px" ><span class="ac row" style="gap:3px">{ic("list",13)}Деталі: Instagram · Олена Литвин · ФОП Максимчук{ic("chevron-down",13)}</span><span class="ac row" style="gap:3px">Коментар{ic("chevron-down",13)}</span><span class="ac row" style="gap:3px">Поля 1–4{ic("chevron-down",13)}</span><span class="ac row" style="gap:3px">UTM і сайт{ic("chevron-down",13)}</span></div></div>'''
    bar = f'''<div class="row" style="padding:12px 20px;gap:12px;background:#fff;flex:none"><div class="col"><small class="mut">До сплати при отриманні</small><b style="font-size:24px;color:#1F4FB8">1 797 ₴</b></div>
<span class="mut" style="margin-left:16px">2 товари · контроль оплати · Нова Пошта</span><span style="flex:1"></span><span class="btn s" style="height:48px">{ic("truck",17)}Створити ТТН</span><span class="btn p" style="height:48px;padding:0 24px">{ic("check",17)}Створити замовлення</span></div>'''
    h = whead(ttn=False).replace('<span class="btn p">' + ic("check", 17) + 'Створити замовлення</span>', "")
    return f'''<div style="position:relative;width:1440px;height:900px">{bg_list()}<div class="ov"></div>
<div class="win d" style="display:flex;grid-template-columns:none;width:auto;height:auto">{h}<div class="wb" style="grid-template-columns:1fr;overflow:hidden">{body}</div>{bar}</div></div>'''


V = [("1", "1 · Як погоджений макет: покупець, оплата, доставка ліворуч · товари праворуч", v1), ("2", "2 · Одна колонка кроків + закріплений підсумок праворуч", v2),
     ("3", "3 · Покупець смугою зверху · деталі смугою знизу", v3), ("4", "4 · Три колонки: покупець і деталі · товари · оплата, доставка, підсумок", v4),
     ("5", "5 · Швидке введення: вибір пігулками, сума й кнопки внизу", v5)]


def build():
    return page("Нове замовлення — 5 варіантів", CSS, [(k, n, f(), 1440, 900) for k, n, f in V], cols=1, gap=48)
