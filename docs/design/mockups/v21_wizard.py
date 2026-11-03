"""Нове замовлення покроково — 3 варіанти × 5 кроків: 1 ПІБ і телефон · 2 Товар · 3 Оплата · 4 Доставка · 5 Джерело.
Поточний етап по центру, великі поля, «Далі» (Enter). Окремого «Зберегти» немає: на останньому кроці «Створити ТТН» і «Створити замовлення»."""
from common import *
from v19_new_order import CSS as BASE19, bg_list
from v18_desktop import sq

CSS = BASE19 + """
.big{height:56px;border-radius:16px;background:#F6F7F8;display:flex;align-items:center;gap:10px;padding:0 18px;font-size:18px;color:var(--ink)}
.big.f{background:#fff;border:2px solid var(--acc);box-shadow:0 0 0 4px var(--acc2)}.big.e{color:var(--faint)}
.big .fl{width:22px;height:16px;border-radius:4px;background:linear-gradient(#2E6BE6 50%,#F5C518 50%)}
.lb{font-size:13px;color:var(--mut);margin:0 0 6px 4px}
.q{font-size:26px;font-weight:600;letter-spacing:-.02em;margin-bottom:4px}.qs{font-size:14px;color:var(--mut);margin-bottom:22px}
.opt{display:flex;align-items:center;gap:12px;min-height:64px;padding:0 16px;border-radius:16px;background:#F6F7F8;font-size:15px;font-weight:500;border:2px solid transparent}
.opt small{display:block;font-size:12.5px;color:var(--mut);font-weight:400}
.opt.on{background:#fff;border-color:var(--acc);box-shadow:0 0 0 4px var(--acc2)}.opt .rd{margin-left:auto;width:22px;height:22px;border-radius:50%;border:2px solid #CFCEC9;flex:none}
.opt.on .rd{border:7px solid var(--acc)}
.res{display:flex;align-items:center;gap:12px;padding:8px 10px;border-radius:12px}.res.hl{background:var(--acc2)}
.next{height:52px;padding:0 26px;border-radius:16px;font-size:16px}
.kb{font:500 11px JB;opacity:.7;margin-left:4px}
.dots{display:flex;align-items:center;gap:0}
.dot2{display:flex;align-items:center;gap:8px;font-size:13.5px;color:var(--faint);font-weight:500}
.dot2 i{width:26px;height:26px;border-radius:50%;display:grid;place-items:center;background:#ECEDEF;color:#8A8984;font-style:normal;font-size:12px;font-weight:600}
.dot2.ok{color:var(--ink)}.dot2.ok i{background:#16A34A;color:#fff}.dot2.cur{color:var(--acc)}.dot2.cur i{background:var(--acc);color:#fff;box-shadow:0 0 0 4px var(--acc2)}
.ln{width:34px;height:2px;background:#E3E3E0;margin:0 10px}.ln.ok{background:#16A34A}
.done{display:flex;align-items:center;gap:12px;padding:8px 16px;border-radius:16px;background:#fff;font-size:14px}
.done .ed{margin-left:auto;color:var(--acc);font-size:13px;font-weight:500}
.todo{display:flex;align-items:center;gap:12px;padding:12px 16px;border-radius:16px;font-size:14px;color:var(--faint);border:1.5px dashed #DADAD6}
.rail{display:flex;flex-direction:column;gap:4px}.rs{display:flex;gap:12px;padding:12px;border-radius:14px}.rs.cur{background:#fff;box-shadow:0 0 0 1.5px var(--acc3)}
.rs .t{display:flex;flex-direction:column;line-height:1.3;min-width:0}.rs .t b{font-size:14.5px}.rs .t small{font-size:12.5px;color:var(--mut);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
"""

STEPS = ["Покупець", "Товар", "Оплата", "Доставка", "Джерело"]
DONE = ["Коваленко Олена · +380 67 111 22 33", "Павербанк Volt 20 000 + кабель · 1 797 ₴", "Контроль оплати НП", "Нова Пошта · ФОП Максимчук", "Instagram · Олена Литвин"]


# ---------------------------------------------------------------- вміст кроків (спільний для варіантів)
def s1():
    return f'''<div class="q">Хто замовляє?</div><div class="qs">ПІБ одним рядком у будь-якому порядку і номер телефону</div>
<div class="lb">ПІБ</div><div class="big" style="margin-bottom:16px;font-weight:500">Коваленко Олена</div>
<div class="lb">Телефон</div><div class="big f"><span class="fl"></span><span class="mut">+380</span><b style="font-weight:500">67 111 22 33</b><span style="margin-left:auto;width:2px;height:24px;background:var(--acc)"></span></div>
<div class="found" style="margin-top:12px;font-size:13.5px;padding:10px 14px">{ic("circle-check-big",16)}<span>Покупець уже є: <b>4 замовлення · викуп 75%</b></span><span style="margin-left:auto;text-decoration:underline">показати</span></div>
<div class="hint" style="margin-top:14px">{ic("plus",14)}Email</div>'''


def s2():
    res = "".join(f'<div class="res{" hl" if k == 0 else ""}"><span class="th">{ic("package",15)}</span><div class="col" style="flex:1;line-height:1.25"><b style="font-weight:500">{n}</b><small class="mut">{sku} · {q}</small></div><b class="num">{p} ₴</b>{"<span class=kb>Enter</span>" if k == 0 else ""}</div>'
                  for k, (n, sku, q, p) in enumerate([("Павербанк Volt 20 000 мА·год", "PB-20", "18 шт · 3 кольори", "1 599"), ("Павербанк Volt 10 000 мА·год", "PB-10", "42 шт", "999"), ("Чохол для павербанка", "CASE-PB", "60 шт · допродаж", "249")]))
    return f'''<div class="q">Що замовляє?</div><div class="qs">Назва, артикул або штрихкод · ↑↓ і Enter — додати</div>
<div class="big f" style="font-weight:500">{ic("search",20)}павер<span style="width:2px;height:24px;background:var(--acc)"></span></div>
<div class="c" style="margin-top:8px;padding:6px;box-shadow:0 12px 30px -12px rgba(31,31,28,.25)">{res}</div>
<div class="lb" style="margin-top:16px">У замовленні</div>
<div class="gi" style="height:52px"><span class="th" style="width:32px;height:32px;border-radius:9px">{ic("zap",15)}</span><span class="nm"><b>Павербанк Volt 20 000 мА·год</b><span class="vp"><i></i>Чорний{ic("chevron-down",11)}</span></span><span></span>
<span class="qty"><span>−</span><b>1</b><span>+</span></span><b class="num" style="text-align:right">1 599 ₴</b><span class="fa">{ic("x",14)}</span></div>
<div class="offer">{ic("sparkles",15)}Часто беруть разом: <b>Кабель USB-C 1 м</b> · 198 ₴<span class="add">{ic("plus",14)}Додати</span></div>
<div class="row" style="justify-content:flex-end;margin-top:12px;gap:18px;font-size:14px"><span class="mut">Знижка <b style="color:var(--ink)">0 ₴</b></span><span>Разом <b style="font-size:18px">1 599 ₴</b></span></div>'''


def s3():
    o = lambda dot, t, sub, on=False: f'<div class="opt{" on" if on else ""}">{dot}<div>{t}<small>{sub}</small></div><span class="rd"></span></div>'
    d = lambda c: f'<span style="width:12px;height:12px;border-radius:50%;background:{c};flex:none"></span>'
    return f'''<div class="q">Як оплачує?</div><div class="qs">Від цього залежить, що піде в ТТН · клавіші 1–4</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">{o(d("#2E6BE6"),"Контроль оплати НП","гроші на рахунок ФОП, без комісії покупцю",True)}{o(d("#2E6BE6"),"Післяплата","грошовий переказ при отриманні")}
{o(d("#16A34A"),"Передоплата","повна або частина наперед")}{o(d("#16A34A"),"Оплачено","Monobank, картка, готівка")}</div>
<div class="hint" style="margin-top:12px;color:var(--mut)">{ic("chevron-down",14)}Інші 43 види оплати</div>
<div class="row" style="margin-top:16px;background:#EAF1FD;border-radius:14px;padding:12px 16px;color:#1F4FB8;font-size:14px">{ic("arrow-up-right",16)}У ТТН піде: <b>контроль оплати · 1 797 ₴</b></div>'''


def s4():
    o = lambda ic_, t, sub, on=False: f'<div class="opt{" on" if on else ""}">{ic_}<div>{t}<small>{sub}</small></div><span class="rd"></span></div>'
    return f'''<div class="q">Як доставити?</div><div class="qs">Місто, відділення й платника вкажете у вікні «Створити ТТН»</div>
<div class="col" style="gap:10px">{o('<span class="np" style="padding:7px 7px;font-size:12px">НП</span>',"Нова Пошта · ФОП Максимчук","основний ключ · відділення, поштомат або кур'єр",True)}
{o('<span class="np" style="padding:7px 7px;font-size:12px">НП</span>',"Нова Пошта · ФОП Максимчук Д. О.","другий ключ")}{o(sq("truck","orange",True,15),"Укрпошта","до 30 кг, дешевше на великі відстані")}
{o(sq("store","gray",True,15),"Самовивіз","без ТТН · з офісу в Тульчині")}</div>
<div class="row" style="margin-top:14px;background:#F2F3F5;border-radius:14px;padding:12px 16px;color:#57564F;font-size:14px">{ic("hand-coins",16)}Післяплата 1 797 ₴ · контроль оплати · береться з оплати</div>'''


def s5():
    ch = lambda items: '<div class="row" style="gap:8px;flex-wrap:wrap">' + "".join(f'<span class="chip" style="height:44px;padding:0 16px;border-radius:14px;font-size:14.5px;{"background:var(--acc);color:#fff" if on else "background:#F6F7F8"}">{x}</span>' for x, on in items) + "</div>"
    v = lambda t: f'<div class="big" style="height:48px;font-size:15px">{t}<span style="margin-left:auto" class="fa">{ic("chevron-down",16)}</span></div>'
    return f'''<div class="q">Звідки замовлення?</div><div class="qs">Останній крок — далі створюємо замовлення або одразу ТТН</div>
<div class="lb">Джерело</div>{ch([("Instagram", True), ("Лендинг", False), ("TikTok", False), ("Facebook", False), ("Дзвінок", False), ("Rozetka", False)])}
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:16px"><div><div class="lb">Менеджер</div>{v("Олена Литвин")}</div><div><div class="lb">Відділ</div>{v("Інтернет-магазин")}</div>
<div><div class="lb">Юрособа</div>{v("ФОП Максимчук О. В.")}</div><div><div class="lb">Позначка</div>{v('<span class="fa">без позначки</span>')}</div>
<div style="grid-column:1 / -1"><div class="lb">Коментар</div><div class="big e" style="height:64px;align-items:flex-start;padding-top:14px;font-size:15px">Що важливо знати складу чи кур'єру…</div></div></div>
<div class="fold" style="margin-top:10px"><span>Поля 1–4{ic("chevron-down",13)}</span><span>UTM і сайт{ic("chevron-down",13)}</span></div>'''


CONTENT = [s1, s2, s3, s4, s5]


def nav(i, center=False):
    back = f'<span class="btn g next">{ic("chevron-left",18)}Назад</span>' if i else '<span class="btn g next">Скасувати</span>'
    if i == 4:
        fwd = f'<span class="btn s next">{ic("truck",18)}Створити ТТН</span><span class="btn p next">{ic("check",18)}Створити замовлення<span class="kb">Ctrl ⏎</span></span>'
    else:
        fwd = f'<span class="btn p next">Далі{ic("chevron-right",18)}<span class="kb">Enter</span></span>'
    return f'<div class="row" style="gap:10px;margin-top:24px">{back}<span style="flex:1"></span>{fwd}</div>'


def shell(inner, step_label):
    return f'''<div style="position:relative;width:1440px;height:900px">{bg_list()}<div class="ov"></div>{inner}</div>'''


# ---------------------------------------------------------------- A. Картка по центру, кроки зверху лінією
def A(i):
    dots = "".join(f'{"<span class=\'ln" + (" ok" if k <= i else "") + "\'></span>" if k else ""}<span class="dot2 {"ok" if k < i else "cur" if k == i else ""}"><i>{ic("check",13,3) if k < i else k + 1}</i>{n}</span>' for k, n in enumerate(STEPS))
    total = f'<div class="row" style="justify-content:center;gap:8px;margin-top:14px;font-size:13px;color:#fff;opacity:.9">{ic("receipt-text",14)}Чернетка · {"1 797 ₴" if i > 1 else "товарів ще немає"} · зберігається сама</div>'
    card = f'''<div style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:760px">
<div class="win d" style="position:relative;inset:auto;left:auto;right:auto;top:auto;bottom:auto;display:block;width:760px;height:auto;padding:22px 34px 26px;background:#fff;border-radius:26px">
<div class="row" style="margin-bottom:22px"><b style="font-size:15px">Нове замовлення</b><span style="flex:1"></span><span class="rb" style="width:36px;height:36px;background:#F2F3F5">{ic("x",16)}</span></div>
<div class="dots" style="justify-content:center;margin-bottom:28px">{dots}</div>{CONTENT[i]()}{nav(i)}</div>{total}</div>'''
    return shell(card, "")


# ---------------------------------------------------------------- B. Розмова: зроблені кроки згортаються над поточним, наступні — пунктиром нижче
def B(i):
    done = "".join(f'<div class="done"><span class="stp ok">{ic("check",12,3)}</span><b style="width:90px">{STEPS[k]}</b><span class="ell">{DONE[k]}</span><span class="ed">змінити</span></div>' for k in range(i))
    todo = "".join(f'<div class="todo"><span class="stp">{k + 1}</span>{STEPS[k]}</div>' for k in range(i + 1, 5))
    cur = f'<div class="c" style="padding:{"16px 28px" if i == 4 else "24px 30px"};border-radius:24px;box-shadow:0 0 0 2px var(--acc3)"><div class="row" style="gap:10px;margin-bottom:10px"><span class="stp cur">{i + 1}</span><span class="mut" style="font-size:13px">Крок {i + 1} з 5 · {STEPS[i]}</span></div>{CONTENT[i]().replace("height:64px;align-items:flex-start", "height:46px;align-items:flex-start" if i == 4 else "height:64px;align-items:flex-start")}{nav(i).replace("margin-top:24px", "margin-top:14px" if i == 4 else "margin-top:24px")}</div>'
    col = f'''<div class="win d" style="display:flex;flex-direction:column;align-items:center;overflow:hidden;width:auto;height:auto"><div class="wh" style="width:100%"><span class="rb" style="background:#F2F3F5">{ic("chevron-left",19)}</span><b style="font-size:18px">Нове замовлення</b><span class="mut" style="font-size:13px">{"сума 1 797 ₴" if i > 1 else "чернетка"}</span><span style="flex:1"></span><span class="rb" style="background:#F2F3F5">{ic("x",18)}</span></div>
<div class="col" style="width:760px;gap:6px;padding:12px 0;flex:1;justify-content:flex-start">{done}{cur}{todo}</div></div>'''
    return shell(col, "")


# ---------------------------------------------------------------- C. Кроки ліворуч зі значеннями, великий етап по центру, підсумок праворуч
def C(i):
    rail = "".join(f'''<div class="rs{" cur" if k == i else ""}"><span class="stp {"ok" if k < i else "cur" if k == i else ""}" style="width:26px;height:26px">{ic("check",12,3) if k < i else k + 1}</span>
<div class="t"><b style="{"color:var(--faint)" if k > i else ""}">{n}</b><small>{DONE[k] if k < i else "заповнюємо зараз" if k == i else "далі"}</small></div></div>''' for k, n in enumerate(STEPS))
    items = '<div class="kv"><span>Павербанк Volt 20 000</span><b>1 599 ₴</b></div><div class="kv"><span>Кабель USB-C 1 м</span><b>198 ₴</b></div>' if i > 1 else '<div class="mut" style="font-size:13px">товарів ще немає</div>'
    summ = f'''<div class="sum" style="height:100%"><small class="mut">Замовлення</small><b style="font-size:16px;margin:2px 0 10px">{"Коваленко Олена" if i else "новий покупець"}</b>{items}
<div class="sep" style="background:#C9DBFA"></div><small class="mut">До сплати при отриманні</small><div class="big2" style="font-size:30px;font-weight:600;color:#1F4FB8">{"1 797 ₴" if i > 1 else "0 ₴"}</div>
<div class="kv"><span>Оплата</span><b style="font-weight:500">{"Контроль оплати НП" if i > 2 else "—"}</b></div><div class="kv"><span>Доставка</span><b style="font-weight:500">{"Нова Пошта" if i > 3 else "—"}</b></div>
<span style="flex:1"></span><div class="mut" style="font-size:12.5px">Чернетка зберігається сама · Esc — закрити</div></div>'''
    body = f'''<div class="win d" style="display:flex;flex-direction:column;overflow:hidden;width:auto;height:auto"><div class="wh"><span class="rb" style="background:#F2F3F5">{ic("chevron-left",19)}</span><b style="font-size:18px">Нове замовлення</b><span class="mut" style="font-size:13px">крок {i + 1} з 5</span><span style="flex:1"></span><span class="rb" style="background:#F2F3F5">{ic("x",18)}</span></div>
<div style="flex:1;display:grid;grid-template-columns:270px 1fr 300px;gap:12px;padding:12px;min-height:0">
<div class="c rail" style="padding:10px">{rail}</div>
<div class="c" style="padding:30px 56px;display:flex;flex-direction:column"><div style="max-width:640px;width:100%;margin:0 auto;flex:1;display:flex;flex-direction:column">{CONTENT[i]()}<span style="flex:1"></span>{nav(i)}</div></div>
{summ}</div></div>'''
    return shell(body, "")


V = [(f"{v}{i + 1}", f"{v} · крок {i + 1} — {STEPS[i]}", f(i)) for v, f in [("A", A), ("B", B), ("C", C)] for i in range(5)]


def build():
    return page("Покрокове нове замовлення — 3 варіанти", CSS, [(k, n, h, 1440, 900) for k, n, h in V], cols=5, gap=40)
