"""Створення ТТН на ПК — у стилі погодженого покрокового замовлення (варіант A): біла картка по центру над затемненим
списком, великі поля й плитки вибору з синім кільцем, одна синя дія. Без кроків: ТТН заповнюється за один екран,
бо зазвичай треба лише місто й відділення — решта підставляється з ключа НП і замовлення."""
from common import *
from v22_wizard_a import CSS as BASE22
from v21_wizard import shell
from v18_desktop import sq

CSS = BASE22 + """
.tt{--ink:#1F1F1C;--mut:#6F6E69;--faint:#A3A29D;--bg:#F1F2F4;--acc:#2E6BE6;--acc2:#EAF1FD;--acc3:#C9DBFA;--ok:#16A34A;font:400 14px/1.4 Onest,sans-serif;color:var(--ink)}
.tt .card{background:#fff;border-radius:26px;padding:22px 30px 26px}
.tt .sec{font-size:15px;font-weight:600;margin:18px 0 10px;display:flex;align-items:center;gap:8px}.tt .sec small{font-weight:400;color:var(--mut);font-size:13px}
.tt .sec:first-child{margin-top:0}
.tt .mt{display:flex;align-items:center;gap:12px;height:64px;padding:0 16px;border-radius:16px;background:#F6F7F8;border:2px solid transparent;flex:1;font-size:15px;font-weight:500}
.tt .mt small{display:block;font-weight:400;color:var(--mut);font-size:12.5px}
.tt .mt.on{background:#fff;border-color:var(--acc);box-shadow:0 0 0 4px var(--acc2)}
.tt .wh{display:flex;align-items:center;gap:12px;padding:10px 14px;border-radius:14px}
.tt .wh.on{background:var(--acc2)}.tt .wh b{font-weight:500}.tt .wh small{color:var(--mut);font-size:12.5px}
.tt .wh .rd{margin-left:auto;width:20px;height:20px;border-radius:50%;border:2px solid #CFCEC9;flex:none}.tt .wh.on .rd{border:6px solid var(--acc);background:#fff}
.tt .tag{font-size:11.5px;font-weight:500;padding:2px 7px;border-radius:99px;background:#F0F0EE;color:#57564F;white-space:nowrap}
.tt .pk{display:flex;align-items:center;gap:12px;height:58px;padding:0 16px;border-radius:16px;background:#F6F7F8;font-size:14.5px}
.tt .pk .ch{margin-left:auto;color:var(--acc);font-weight:500;font-size:13.5px}
.tt .side{background:#EAF1FD;border-radius:20px;padding:18px 20px;display:flex;flex-direction:column}
.tt .side .kv{display:flex;justify-content:space-between;font-size:13.5px;padding:4px 0}.tt .side .kv span{color:#4B5B7C}
.tt .tg{display:flex;align-items:center;gap:10px;font-size:13.5px;padding:7px 0}.tt .tg .tgl{margin-left:auto}
.tt .tgl{width:40px;height:24px;border-radius:99px;background:#D2D6DE;position:relative;flex:none}.tt .tgl::after{content:"";position:absolute;left:3px;top:3px;width:18px;height:18px;border-radius:50%;background:#fff}
.tt .tgl.on{background:var(--acc)}.tt .tgl.on::after{left:19px}
.tt .act{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;height:112px;border-radius:18px;background:#F6F7F8;font-size:14px;font-weight:500;text-align:center;line-height:1.25}
.tt .act small{display:block;color:var(--mut);font-weight:400;font-size:12px}
.tt .bigok{width:76px;height:76px;border-radius:50%;background:#E9F6EE;color:#16A34A;display:grid;place-items:center;margin:0 auto}
.tt .ttn{font:600 34px JB;letter-spacing:.02em;text-align:center}
.tt .hdr{display:flex;align-items:center;gap:12px;margin-bottom:20px}
.tt .key{display:flex;align-items:center;gap:8px;height:40px;padding:0 12px;border-radius:12px;background:#F6F7F8;font-size:13.5px}
.tt .x{width:38px;height:38px;border-radius:50%;background:#F2F3F5;display:grid;place-items:center}
"""

NPB = '<span class="np" style="padding:6px 6px;font-size:12px">НП</span>'


def header(sub="Замовлення №27 · Коваленко Олена · +380 67 111 22 33"):
    return f'''<div class="hdr">{NPB}<div style="line-height:1.25"><b style="font-size:22px;letter-spacing:-.01em">Нова ТТН</b><div class="mut" style="font-size:13px">{sub}</div></div>
<span style="flex:1"></span><span class="key">{sq("key-round","gray",True,14)}<span><span class="mut">Відправник:</span> <b style="font-weight:500">ФОП Максимчук О. В.</b> · основний ключ</span>{ic("chevron-down",15)}</span>
<span class="x">{ic("x",17)}</span></div>'''


def modes(sel):
    it = [("wh", "store", "blue", "Відділення", "до 30 кг"), ("pm", "package", "purple", "Поштомат", "до 20 кг, 40×30×60"), ("cr", "truck", "orange", "Кур'єр на адресу", "+ 35 ₴ до вартості")]
    return '<div class="row" style="gap:10px">' + "".join(
        f'<div class="mt{" on" if k == sel else ""}">{sq(i, t, False, 17)}<span>{n}<small>{s}</small></span></div>' for k, i, t, n, s in it) + "</div>"


def side(cost="85", when="завтра, 31 жовтня", extra=""):
    return f'''<div class="side">
<div class="mut" style="color:#4B5B7C;font-size:13px">Вартість доставки</div>
<div style="font-size:38px;font-weight:600;letter-spacing:-.02em;color:#1F4FB8;line-height:1.15">≈ {cost} ₴</div>
<div class="row" style="gap:6px;color:#1F4FB8;font-size:13.5px;margin-bottom:12px">{ic("calendar",15)}Орієнтовно {when}</div>
<div class="kv"><span>Платить</span><b>отримувач</b></div>
<div class="kv"><span>Контроль оплати</span><b>1 797 ₴</b></div>
<div class="kv"><span>Оголошена вартість</span><b>1 797 ₴</b></div>{extra}
<div style="height:1px;background:#D5E2F9;margin:12px 0 6px"></div>
<div style="font-size:12.5px;color:#4B5B7C;margin-bottom:2px">Одразу після створення</div>
<div class="tg">{ic("printer",16)}Друкувати наклейку<span class="tgl on"></span></div>
<div class="tg">{ic("list-checks",16)}У реєстр на сьогодні<span class="tgl on"></span></div>
<div class="tg">{ic("message-square",16)}SMS покупцю з ТТН<span class="tgl on"></span></div>
<div class="tg">{ic("send",16)}Статус «Відправлений»<span class="tgl"></span></div>
<span style="flex:1"></span>
<span class="btn p next" style="margin-top:14px;justify-content:center">{ic("truck",18)}Створити ТТН<span class="kb">Ctrl ⏎</span></span>
<div class="mut" style="text-align:center;font-size:12px;margin-top:8px;color:#4B5B7C">Вартість рахує НП, остаточна — у ТТН</div></div>'''


def parcel():
    return f'''<div class="sec">Посилка <small>з товарів замовлення</small></div>
<div class="pk">{sq("package","gray",True,15)}<span><b style="font-weight:500">Посилка</b> · 0,3 кг · 20 × 15 × 10 см · 1 місце</span><span class="mut">опис «Павербанк»</span><span class="ch">Змінити</span></div>'''


def payer():
    return f'''<div class="sec">Хто платить за доставку</div>
<div class="row" style="gap:10px"><div class="mt on" style="height:56px">{sq("user","blue",True,15)}<span>Отримувач</span></div>
<div class="mt" style="height:56px">{sq("store","gray",True,15)}<span>Відправник</span></div><div class="mt" style="height:56px">{sq("users","gray",True,15)}<span>Третя особа</span></div></div>'''


def warehouse_body():
    whs = [("Відділення №1", "вул. Миколи Леонтовича, 46", "до 30 кг", "8:00–20:00", False),
           ("Відділення №3", "вул. Шевченка, 12 · біля ринку", "до 30 кг", "9:00–19:00", True),
           ("Поштомат №5718", "АТБ, вул. Гагаріна, 5", "до 20 кг", "цілодобово", False)]
    lst = "".join(f'<div class="wh{" on" if on else ""}">{sq("store" if "Відд" in n else "package","blue" if on else "gray",True,15)}<span style="line-height:1.3"><b>{n}</b> <span class="tag">{kg}</span><br><small>{a} · {h}</small></span><span class="rd"></span></div>' for n, a, kg, h, on in whs)
    return f'''<div class="sec">Куди</div>{modes("wh")}
<div style="display:grid;grid-template-columns:1fr 1.25fr;gap:12px;margin-top:14px">
<div><div class="lb">Місто</div><div class="big" style="font-weight:500;height:56px">Тульчин<span class="mut" style="font-weight:400;font-size:14px">Вінницька обл.</span></div>
<div class="hint" style="margin-top:10px;color:#13803D">{ic("circle-check-big",14)}Як у минулому замовленні покупця</div></div>
<div><div class="lb">Відділення</div><div class="big f" style="height:56px">{ic("search",19)}<span style="font-weight:500">3</span><span style="width:2px;height:22px;background:var(--acc)"></span><span class="mut" style="font-size:13.5px;margin-left:auto">12 у місті</span></div>
<div class="c" style="margin-top:8px;padding:6px;border-radius:16px;box-shadow:0 12px 30px -12px rgba(31,31,28,.25)">{lst}</div></div></div>'''


def courier_body():
    return f'''<div class="sec">Куди</div>{modes("cr")}
<div style="display:grid;grid-template-columns:1fr 1.25fr;gap:12px;margin-top:14px">
<div><div class="lb">Місто</div><div class="big" style="font-weight:500;height:56px">Тульчин<span class="mut" style="font-weight:400;font-size:14px">Вінницька обл.</span></div></div>
<div><div class="lb">Вулиця</div><div class="big f" style="height:56px">{ic("search",19)}<span style="font-weight:500">Шевченка</span><span style="width:2px;height:22px;background:var(--acc)"></span><span class="mut" style="font-size:13.5px;margin-left:auto">з довідника НП</span></div></div></div>
<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1.6fr;gap:12px;margin-top:14px">
<div><div class="lb">Будинок</div><div class="big" style="height:56px;font-weight:500">12</div></div>
<div><div class="lb">Квартира</div><div class="big e" style="height:56px">—</div></div>
<div><div class="lb">Поверх</div><div class="big e" style="height:56px">—</div></div>
<div><div class="lb">Бажаний час</div><div class="big" style="height:56px;font-size:16px;font-weight:500">9:00–12:00<span class="fa" style="margin-left:auto">{ic("chevron-down",16)}</span></div></div></div>
<div class="hint" style="margin-top:12px;color:var(--mut)">{ic("circle-alert",14)}Кур'єр зателефонує отримувачу перед доставкою — номер береться із замовлення</div>'''


def window(body, cost="85", when="завтра, 31 жовтня", extra=""):
    card = f'''<div class="tt" style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:1080px">
<div class="card">{header()}<div style="display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:24px;align-items:stretch">
<div>{body}{payer()}{parcel()}</div>{side(cost, when, extra)}</div></div>
<div class="row" style="justify-content:center;gap:8px;margin-top:14px;font-size:13px;color:#fff;opacity:.9">{ic("receipt-text",14)}Замовлення вже створене · ТТН можна закрити й оформити пізніше</div></div>'''
    return shell(card, "")


def success():
    acts = [("printer", "blue", "Друкувати наклейку", "100 × 100 мм"), ("list-checks", "green", "Додано в реєстр", "на 30 жовтня"),
            ("message-square", "purple", "SMS із ТТН", "надіслано покупцю"), ("copy", "gray", "Скопіювати номер", "у буфер обміну")]
    tiles = "".join(f'<div class="act">{sq(i, t, False, 18)}<span>{n}<small>{s}</small></span></div>' for i, t, n, s in acts)
    card = f'''<div class="tt" style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:720px">
<div class="card" style="padding:30px 34px 28px;text-align:center">
<div class="bigok">{ic("check",38,2.6)}</div>
<div style="font-size:26px;font-weight:600;letter-spacing:-.02em;margin:16px 0 6px">ТТН створено</div>
<div class="row" style="justify-content:center;gap:12px">{NPB}<span class="ttn">20 4512 3456 7890</span><span class="x" style="width:40px;height:40px">{ic("copy",17)}</span></div>
<div class="mut" style="margin-top:8px;font-size:14.5px">Тульчин, відділення №3 · доставка завтра · ≈ 85 ₴ платить отримувач</div>
<div class="row" style="justify-content:center;gap:8px;margin-top:12px">{st("acc")}<span class="fa">{ic("chevron-right",15)}</span><span class="st" style="--c:#6D5BD0"><i></i>Відправлений</span><span class="mut" style="font-size:13px">після передачі кур'єру НП</span></div>
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:22px;text-align:center">{tiles}</div>
<div class="row" style="gap:10px;margin-top:22px"><span class="btn g next" style="flex:1;justify-content:center">{ic("receipt-text",17)}Відкрити замовлення</span>
<span class="btn p next" style="flex:1;justify-content:center">Готово<span class="kb">Enter</span></span></div></div>
<div class="row" style="justify-content:center;gap:8px;margin-top:14px;font-size:13px;color:#fff;opacity:.9">{ic("circle-check-big",14)}Наклейку відправлено на принтер</div></div>'''
    return shell(card, "")


def st(k):
    from v18_desktop import st as s
    return s(k)


V = [("1", "ТТН на ПК — відділення: місто, пошук відділення, платник, посилка; праворуч ціна й одна кнопка", window(warehouse_body())),
     ("2", "ТТН на ПК — кур'єр на адресу: вулиця з довідника НП, будинок, бажаний час", window(courier_body(), "120", "завтра, 9:00–12:00")),
     ("3", "ТТН на ПК — готово: номер, що вже зроблено, наступні дії", success())]


def build():
    return page("Створення ТТН — ПК", CSS, [(k, n, h, 1440, 900) for k, n, h in V], cols=3, gap=40)
