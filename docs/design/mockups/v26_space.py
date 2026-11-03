"""v26 — простір і поля: телефон і доставка значками з підказкою, плюс 20 покращень по всій CRM (лише ПК).
Кожен кадр — макет 1440×900 і праворуч пояснення до рожевих номерів на макеті."""
from common import *
from v18_desktop import CSS as BASE, sidebar, st, sq, ring, head, SC

CSS = BASE + """
.wrap{display:flex;width:1820px;height:900px;background:#fff}
.wrap > .d{flex:none}
.lg{width:380px;flex:none;padding:26px 24px;display:flex;flex-direction:column;gap:13px;overflow:hidden;font:400 13px/1.4 'Onest',sans-serif;color:#1F1F1C;border-left:1px solid #ECECEA}
.lg h2{font-size:19px;font-weight:600;letter-spacing:-.01em;line-height:1.2}
.lg .lead{font-size:12.5px;color:#6F6E69;margin-top:-6px}
.lg .li{display:flex;gap:10px;align-items:flex-start}
.lg .li b{display:block;font-size:13.5px;font-weight:600;margin-bottom:2px}
.lg .li p{font-size:12.5px;color:#57564F}
.lg .li.user .mk{background:#1F1F1C}
.mk{display:inline-grid;place-items:center;min-width:20px;height:20px;padding:0 5px;border-radius:99px;background:#DB2777;color:#fff;font:700 11px/1 'Onest',sans-serif;flex:none;
  box-shadow:0 0 0 2px #fff;vertical-align:middle;font-style:normal}
.mk.u{background:#1F1F1C}
.mk.a{position:absolute;z-index:9}
.pop{position:absolute;background:#fff;border-radius:14px;box-shadow:0 18px 40px -12px rgba(0,0,0,.30),0 0 0 1px rgba(0,0,0,.05);padding:12px 14px;z-index:8;font-size:13px}
.pop .t{font-size:11.5px;color:var(--mut);margin-bottom:6px}
.ib{width:28px;height:28px;border-radius:9px;background:#F2F3F5;display:inline-grid;place-items:center;color:#3D3C38;flex:none}
.ib.on{background:var(--acc2);color:var(--acc)}.ib.g{background:#E9F6EE;color:#16A34A}.ib.o{background:#FDF1E3;color:#D97706}.ib.r{background:#FDECEC;color:#DC2626}.ib.v{background:#F1ECFB;color:#7C3AED}
.sig{display:inline-grid;place-items:center;width:18px;height:18px;border-radius:6px;flex:none}
.tr.one{min-height:44px;white-space:nowrap}.tr.one > *{min-width:0}
.dt{width:7px;height:7px;border-radius:50%;display:inline-block;flex:none}
.av2{width:24px;height:24px;border-radius:50%;display:inline-grid;place-items:center;background:#EAF1FD;color:#1F56C4;font-size:10px;font-weight:600}
.sum-row{display:flex;align-items:center;gap:18px;padding:0 16px;height:44px;border-top:1px solid #EFEFED;background:#FAFAFA;font-size:13px;color:var(--mut)}
.sum-row b{color:var(--ink)}
.menu .mi{display:flex;align-items:center;gap:8px;height:32px;padding:0 8px;border-radius:9px;font-size:13px}.menu .mi.on{background:#F2F3F5}
.spark{display:block}
.gi{display:grid;grid-template-columns:40px minmax(0,1fr) 92px 110px 90px;align-items:center;gap:12px;padding:8px 0;border-top:1px solid #F2F2F0}
.ph{width:40px;height:40px;border-radius:11px;background:linear-gradient(135deg,#E8E2D8,#CFC6B8);flex:none}
.ph.b{background:linear-gradient(135deg,#DCE6F5,#AFC2E2)}.ph.g{background:linear-gradient(135deg,#DDEFE3,#A9D3B7)}.ph.o{background:linear-gradient(135deg,#F6E6D2,#E8C190)}
.stk{display:inline-flex;align-items:center;gap:6px;font-size:12.5px}
.dots{display:inline-flex;gap:3px}.dots i{width:7px;height:7px;border-radius:50%;background:#E3E3DF}.dots i.on{background:var(--warn)}
.wait{display:inline-flex;align-items:center;gap:5px;height:22px;padding:0 8px;border-radius:99px;font-size:12px;font-weight:600}
.kb{font:500 11px 'JB',monospace;color:var(--mut);background:#F2F3F5;border-radius:6px;padding:2px 6px}
"""

USER = "u"


def mk(n, style=""):
    """Номер покращення на макеті. style з position — абсолютний, інакше в рядку."""
    cls = "mk" + (" u" if str(n) in ("А", "Б") else "") + (" a" if "top" in style or "left" in style else "")
    return f'<span class="{cls}" style="{style}">{n}</span>'


def legend(title, lead, items):
    rows = "".join(f'<div class="li">{mk(n)}<div><b>{t}</b><p>{d}</p></div></div>' for n, t, d in items)
    return f'<aside class="lg"><h2>{title}</h2><div class="lead">{lead}</div>{rows}</aside>'


def shot(active, body, lg, extra=""):
    return f'<div class="wrap"><div class="d">{sidebar(active)}<main class="mn" style="position:relative">{body}</main>{extra}</div>{lg}</div>'


SEARCH = f'<span class="srch" style="width:260px;height:40px;border-radius:99px">{ic("search",16)}Пошук у списку<kbd>/</kbd></span>'
FILT = f'<span class="rb" style="width:40px;height:40px">{ic("list-filter",18)}<span class="dot"></span></span>'
PLUS = lambda t: f'<span class="btn p" style="height:40px">{ic("plus",17)}{t}</span>'


# ============================================================ 1. Замовлення — таблиця з новим набором полів
ROWS = [  # статус, №, час, ім'я, сигнали, товар, +n, оплата, перевізник, стан ТТН, джерело-колір, сума
    ("uns", "44", "17:10", "Олена Коваль", ["dup"], "Бездротовий мікрофон", "", "ctrl", "np", "", "#2E6BE6", "1 899"),
    ("uns", "43", "17:00", "Андрій Мельник", [], "Набір капсул 50 шт", "+1", "ctrl", "", "", "#DB2777", "2 000"),
    ("acc", "42", "16:37", "Микола Бондаренко", ["vip"], "Радіосистема DJI Mic 2", "", "pre", "np", "", "#16A34A", "3 899"),
    ("acc", "41", "15:58", "Ірина Савчук", [], "Кільцева лампа 26 см", "+2", "pre", "np", "", "#D97706", "1 297"),
    ("sent", "40", "15:50", "Тарас Ткаченко", [], "Екшн-камера 4К", "", "cod", "np", "move", "#DB2777", "5 499"),
    ("sent", "39", "14:12", "Світлана Олійник", ["bl"], "Штатив-монопод", "", "cod", "up", "move", "#2E6BE6", "2 797"),
    ("wait", "38", "учора", "Денис Мельник", ["rem"], "Смарт-годинник Fit 3", "", "cod", "np", "wait", "#16A34A", "2 398"),
    ("done", "37", "учора", "Олег Бондаренко", [], "Павербанк Volt 20 000", "+1", "paid", "np", "done", "#D97706", "1 999"),
    ("done", "36", "28.10", "Інна Ковальчук", [], "Навушники TWS Pro", "", "paid", "np", "done", "#DB2777", "1 649"),
    ("ref", "35", "28.10", "Віктор Поліщук", [], "Чохол MagSafe", "", "cod", "np", "back", "#2E6BE6", "449"),
    ("done", "34", "27.10", "Ганна Лисенко", [], "Маска для обличчя", "", "paid", "np", "done", "#16A34A", "299"),
    ("done", "33", "27.10", "Роман Кравченко", [], "Крем для рук «Лаванда»", "+1", "paid", "np", "done", "#D97706", "598"),
    ("sent", "32", "26.10", "Юлія Марченко", [], "Сироватка з вітаміном C", "", "cod", "np", "move", "#DB2777", "649"),
    ("done", "30", "25.10", "Петро Іваненко", [], "Кільцева лампа 26 см", "", "paid", "up", "done", "#2E6BE6", "899"),
]
PAYI = {"ctrl": ("shield-check", "on", "Контроль оплати НП"), "pre": ("credit-card", "v", "Передоплата на картку"),
        "cod": ("banknote", "o", "Післяплата"), "paid": ("check", "g", "Оплачено")}
DST = {"": "#C9C8C3", "move": "#6D5BD0", "wait": "#D97706", "done": "#16A34A", "back": "#DC2626"}
SIG = {"dup": ("copy", "#FDF1E3", "#D97706"), "vip": ("crown", "#FBF3DB", "#A16207"), "bl": ("ban", "#FDECEC", "#DC2626"), "rem": ("alarm-clock", "#FDECEC", "#DC2626")}


def orders_body(with_pops=True):
    G = "18px 40px minmax(170px,1.25fr) minmax(190px,1.5fr) 132px 34px 58px 26px 28px 54px 86px 30px"
    hd = f'''<div class="tr h one" style="grid-template-columns:{G}"><span class="cb"></span><span>№</span><span>Покупець</span><span>Товар</span><span>Статус</span>
<span title="Оплата">{ic("wallet",14)}</span><span>{ic("truck",14)}</span><span>{ic("radio",13) if False else "Дж."}</span><span>М.</span><span>Дата</span><span style="text-align:right">Сума</span><span>{ic("phone",13)}</span></div>'''
    out = hd
    for k, (s, no, t, n, sig, g, more, pay, car, ds, src, sm) in enumerate(ROWS):
        sigs = "".join(f'<span class="sig" style="background:{SIG[x][1]};color:{SIG[x][2]}">{ic(SIG[x][0],11)}</span>' for x in sig)
        pi, pc, pn = PAYI[pay]
        carb = {"np": '<span class="np">НП</span>', "up": '<span class="np" style="background:#F5B800;color:#1F1F1C">УП</span>', "": f'<span class="fa">{ic("minus",14)}</span>'}[car]
        dlv = f'<span class="row" style="gap:6px">{carb}{f"<i class=dt style=background:{DST[ds]}></i>" if car else ""}</span>'
        hover = k == 1
        stc = st(s) if k != 8 else st(s).replace("</span>", f'{ic("chevron-down",12)}</span>', 1)
        phone = f'<span class="ib{" on" if k == 1 else ""}">{ic("phone",14)}</span>'
        out += f'''<div class="tr one" style="grid-template-columns:{G};{"background:#FAFAF8;" if hover else ""}position:relative"><span class="cb"></span><span class="num" style="font:600 12px JB;color:#57564F">{no}</span>
<span class="row" style="gap:6px"><span class="ell" style="font-weight:500">{n}</span>{sigs}</span>
<span class="row" style="gap:6px"><span class="th" style="width:26px;height:26px;border-radius:8px">{ic("package",12)}</span><span class="ell">{g}</span>{f'<span class="st" style="--c:#7C7B76;height:20px;padding:0 7px">{more}</span>' if more else ""}</span>
<span>{stc}</span><span class="ib {pc}" style="width:26px;height:26px">{ic(pi,13)}</span>{dlv}<i class="dt" style="background:{src};width:9px;height:9px"></i><span class="av2">ОЛ</span>
<span class="mut num">{t}</span><b class="num" style="text-align:right">{sm} ₴</b>{phone}</div>'''
    pops = f'''
<div class="pop" style="right:6px;top:236px;width:280px">{mk("А","top:-9px;left:-9px")}<div class="t">Телефон · наведення на значок</div>
<div class="row" style="gap:8px"><b style="font-size:16px" class="num">+380 93 455 10 07</b><span class="ib" style="width:26px;height:26px;margin-left:auto">{ic("copy",13)}</span></div>
<div class="row" style="gap:6px;margin-top:10px"><span class="btn sm p" style="flex:1;height:32px">{ic("phone",14)}Дзвінок</span><span class="ib v" style="width:32px;height:32px">{ic("message-circle",15)}</span><span class="ib on" style="width:32px;height:32px">{ic("send",15)}</span><span class="ib" style="width:32px;height:32px">{ic("message-square",15)}</span></div>
<div class="sep" style="margin:10px 0 8px"></div><div class="row mut" style="font-size:12.5px;gap:10px"><span>4 замовлення</span><span>викуп 75%</span><span class="bd">1 відмова</span></div></div>
<div class="pop" style="left:770px;top:392px;width:300px">{mk("Б","top:-9px;left:-9px")}<div class="t">Доставка · наведення на значок</div>
<div class="row" style="gap:8px"><span class="np">НП</span><b>Київ, відділення №12</b></div><div class="mut" style="font-size:12.5px;margin:3px 0 8px 34px">вул. Хрещатик, 22 · до 30 кг</div>
<div class="row" style="gap:8px;font-size:12.5px"><span class="num" style="font:500 12.5px JB">20450012345678</span><span class="ib" style="width:22px;height:22px;border-radius:7px">{ic("copy",11)}</span></div>
<div class="row" style="gap:8px;margin-top:8px"><span class="st" style="--c:#6D5BD0"><i></i>У дорозі</span><span class="mut" style="font-size:12.5px">прибуде завтра · 85 ₴</span></div></div>
<div class="pop" style="left:380px;top:346px;width:290px">{mk(3,"top:-9px;left:-9px")}<div class="t">Склад замовлення · наведення на «+2»</div>
{"".join(f'<div class="row" style="gap:8px;padding:4px 0"><span class="th" style="width:26px;height:26px;border-radius:8px">{ic("package",12)}</span><span class="ell" style="flex:1">{a}</span><span class="mut">× {q}</span><b class="num" style="width:62px;text-align:right">{p} ₴</b></div>' for a, q, p in [("Кільцева лампа 26 см", 1, "899"), ("Штатив 2 м", 1, "299"), ("Пульт Bluetooth", 1, "99")])}</div>
<div class="pop menu" style="left:628px;top:568px;width:200px;padding:6px">{mk(4,"top:-9px;left:-9px")}
{"".join(f'<div class="mi{" on" if k == "acc" else ""}">{st(k)}</div>' for k in ["uns", "acc", "sent", "wait", "done", "ref"])}</div>'''
    tbl = f'''<div class="tb" style="flex:1;margin-bottom:16px;display:flex;flex-direction:column;position:relative">{out}<span style="flex:1"></span>
<div class="sum-row">{mk(5) if with_pops else ""}<span><b>126</b> замовлень</span><span>на <b>184 350 ₴</b></span><span>післяплата чекає <b>23 490 ₴</b></span><span style="flex:1"></span><span class="ac">вибрано 0</span></div></div>'''
    marks = f'''{mk(1,"left:300px;top:184px")}{mk(2,"left:860px;top:184px")}{mk("А","left:1166px;top:184px")}{mk("Б","left:902px;top:184px")}'''
    if not with_pops:
        pops = marks = ""
    body = f'''{head("Замовлення", "<b>16</b> несортованих · <b>3</b> чекають відправки · <b>13</b> у дорозі", SEARCH + FILT + '<span class="seg"><span class="on">' + ic("list",14) + 'Таблиця</span><span>' + ic("layout-grid",14) + '</span><span>' + ic("inbox",14) + '</span></span>' + PLUS("Замовлення"))}
<div class="row" style="justify-content:space-between;margin-bottom:12px"><div class="tabs">{"".join(f'<span class="tab{" on" if on else ""}" style="--c:{c}">{n} <em{" class=h" if h else ""}>{q}</em></span>' for n, q, c, on, h in [("Несортовані", 16, "#7C7B76", False, True), ("Прийняті", 3, "#2E6BE6", False, False), ("Відправлені", 13, "#6D5BD0", False, False), ("На пошті", 5, "#D97706", False, False), ("Завершені", 68, "#16A34A", False, False), ("Відмова", 7, "#DC2626", False, False), ("Усі", 126, "#1F1F1C", True, False)])}</div>
<span class="chip on">{ic("calendar",13)}Сьогодні й учора{ic("x",12)}</span></div>{tbl}{pops}{marks}'''
    return body


def orders_table():
    body = orders_body()
    lg = legend("Замовлення: що лишити в рядку", "Було 12 колонок тексту, і ім'я та товар обрізались. Тепер текстом — лише те, що читають щоразу; решта — значками з підказкою.", [
        ("А", "Телефон — значок у кінці рядка", "Наведення: номер, копіювати, дзвінок, Viber, Telegram, SMS і коротко про покупця (замовлення, викуп, відмови)."),
        ("Б", "Доставка — бейдж перевізника й крапка стану ТТН", "Адресу в рядку не показуємо. Наведення: місто, відділення, адреса, ТТН з копіюванням, стан і дата прибуття."),
        (1, "Сигнали — маленькі значки біля імені", "«Дубль?», «ЧС», VIP, нагадування замість слів-таблеток: 18 px замість 60–70 px."),
        (2, "Оплата — кольоровий значок", "Контроль оплати, передоплата, післяплата, оплачено. Наведення — назва, сума, чек."),
        (3, "«+2» відкриває склад замовлення", "Не треба заходити в картку, щоб побачити всі товари й ціни."),
        (4, "Статус міняється прямо в таблиці", "Клік по таблетці — меню статусів; той самий захист складу й підтвердження, що в картці."),
        (5, "Рядок підсумку", "Скільки замовлень і на яку суму за фільтром, скільки післяплати чекає; для вибраних — їхня сума."),
    ])
    lg = lg.replace('<div class="li">' + mk("А"), '<div class="li user">' + mk("А")).replace('<div class="li">' + mk("Б"), '<div class="li user">' + mk("Б"))
    return shot("orders", body, lg)


# ============================================================ 2. Картка замовлення — щільніше
def card():
    goods = "".join(f'''<div class="gi"><span class="ph {c}"></span><div class="col"><span class="ell" style="font-weight:500">{n}</span><small class="mut">{a}</small></div>
<span class="stk"><i class="dt" style="background:{sc}"></i>{s}</span><span class="row" style="gap:10px;height:30px;border-radius:99px;background:#F6F7F8;padding:0 12px;justify-content:center"><span class="fa">−</span><b>{q}</b><span class="fa">+</span></span><b class="num" style="text-align:right">{p} ₴</b></div>'''
                    for n, a, s, sc, q, p, c in [("Кільцева лампа 26 см", "LAMP-26 · 899 ₴", "142 шт", "#16A34A", 1, "899", "o"), ("Штатив 2 м", "TRI-2 · 299 ₴", "6 шт", "#D97706", 1, "299", "b"), ("Пульт Bluetooth", "BT-REM · допродаж", "0 — під замовлення", "#DC2626", 1, "99", "g")])
    hist = "".join(f'<div class="row" style="gap:10px;padding:6px 0;align-items:flex-start">{sq(i,t,True,13)}<div class="col"><span style="font-size:13px">{a}</span><small class="fa">{b}</small></div></div>'
                   for i, t, a, b in [("check", "blue", "Статус: Прийнятий", "Олена · 16:40"), ("message-square", "purple", "«Передзвонити після 18:00»", "Олена · 16:12"), ("send", "green", "SMS: замовлення прийнято", "система · 16:40"), ("inbox", "gray", "Заявка з лендингу", "16:05")])
    body = f'''<div class="hd" style="min-height:48px;margin-bottom:10px"><span class="rb" style="width:38px;height:38px">{ic("arrow-left",17)}</span>
<div class="row" style="gap:6px;margin-left:6px">{"".join(f'<span class="chip" style="height:34px;{x}">{n}</span>' for n, x in [("✓ Несортований", "background:#E6E7EA;color:#6F6E69"), ("Прийнятий", "background:#1F1F1C;color:#fff"), ("Відправлений", ""), ("На пошті", ""), ("Завершений", "")])}</div>
<span class="sp"></span><span class="fa" style="font-size:12.5px">{ic("circle-check",14)} Збережено</span><span class="rb" style="width:38px;height:38px">{ic("printer",16)}</span><span class="rb" style="width:38px;height:38px">{ic("bell",16)}</span><span class="rb" style="width:38px;height:38px">{ic("ellipsis",16)}</span></div>
<div style="display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:12px;flex:1;min-height:0;padding-bottom:16px">
<div class="col" style="gap:12px">
 <div class="c row" style="gap:14px;padding:14px 18px">{mk(6)}<span class="av l">ІС</span><div class="col" style="flex:1"><b style="font-size:20px">Ірина Савчук</b>
  <div class="row" style="gap:8px;margin-top:4px"><span class="chip" style="height:26px;background:#F2F3F5;font-size:12.5px">4 замовлення</span><span class="chip" style="height:26px;background:#E9F6EE;color:#15803D;font-size:12.5px">викуп 75%</span><span class="chip" style="height:26px;background:#FDECEC;color:#B91C1C;font-size:12.5px">1 відмова</span></div></div>
  <span class="ib" style="width:38px;height:38px;border-radius:12px">{ic("phone",16)}</span><span class="ib v" style="width:38px;height:38px;border-radius:12px">{ic("message-circle",16)}</span><span class="ib on" style="width:38px;height:38px;border-radius:12px">{ic("send",16)}</span><span class="ib" style="width:38px;height:38px;border-radius:12px">{ic("pencil",15)}</span></div>
 <div class="c" style="flex:1"><h3>{sq("package","blue",True,15)}Товари <small>3 позиції · 1 297 ₴</small>{mk(7)}<span class="r">+ Товар · + Допродаж</span></h3>{goods}
  <div class="row" style="margin-top:10px;height:40px;border-radius:12px;background:#F6F7F8;padding:0 12px;color:var(--faint);gap:8px">{ic("search",15)}Додати товар: назва, артикул або штрихкод</div></div>
 <div class="row" style="gap:12px">{mk(8)}
  <div class="c row" style="flex:1;gap:12px;padding:14px 16px">{sq("credit-card","purple",False,16)}<div class="col" style="flex:1"><small class="mut">Оплата</small><b>Передоплата на картку</b><small class="ok">{ic("check",12)} 1 297 ₴ надійшло · чек пробито</small></div><span class="fa">{ic("pencil",15)}</span></div>
  <div class="c row" style="flex:1;gap:12px;padding:14px 16px">{sq("truck","red",False,16)}<div class="col" style="flex:1"><small class="mut">Доставка</small><b>НП · Вінниця, №2</b><small class="mut">ТТН ще немає · ≈ 70 ₴, завтра</small></div><span class="fa">{ic("pencil",15)}</span></div></div>
</div>
<div class="col" style="gap:12px">
 <div class="c" style="background:#EAF1FD"><small class="mut">До сплати при отриманні</small><div style="font-size:34px;font-weight:600;color:var(--acc);letter-spacing:-.02em">0 ₴</div>
  <div class="kv"><span>Товари</span><b>1 297 ₴</b></div><div class="kv"><span>Передоплата</span><b>−1 297 ₴</b></div><span class="btn p" style="width:100%;margin-top:10px">{ic("truck",16)}Створити ТТН</span></div>
 <div class="c"><h3>Деталі</h3><div class="row" style="gap:6px;flex-wrap:wrap">{"".join(f'<span class="chip" style="height:28px;background:#F2F3F5;font-size:12.5px">{a}</span>' for a in ["Instagram", "Олена Литвин", "Відділ Київ", "ФОП Петренко"])}</div>
  <div class="inp e" style="margin-top:10px">Коментар до замовлення</div></div>
 <div class="c" style="flex:1"><h3>Історія{mk(9)}<span class="r">усе</span></h3><div class="row" style="gap:5px;margin-bottom:6px">{"".join(f'<span class="chip" style="height:26px;font-size:12px;{x}">{n}</span>' for n, x in [("Усе", "background:#1F1F1C;color:#fff"), ("Статуси", "background:#F2F3F5"), ("SMS", "background:#F2F3F5"), ("Коментарі", "background:#F2F3F5")])}</div>{hist}
  <div class="inp e" style="margin-top:8px">Написати коментар…</div></div>
</div></div>'''
    lg = legend("Картка замовлення", "Той самий варіант C, але без порожнього місця: дрібні блоки згорнуто, головне — більшим.", [
        (6, "Покупець одним рядком", "Ім'я, лічильники-чипи й кнопки зв'язку в одній смузі замість чотирьох великих плиток. Редагування — олівцем."),
        (7, "Товари з фото й залишком", "Мініатюра, артикул і ціна дрібно; залишок кольоровою крапкою: зелений — є, жовтий — мало, червоний — немає."),
        (8, "Оформлені оплата й доставка — підсумком", "Коли все заповнено, блок стискається до двох рядків зі станом (надійшло, чек, ціна доставки). Олівець — розгорнути форму."),
        (9, "Історія з фільтрами й коментарем", "Перемикач «Усе / Статуси / SMS / Коментарі» і поле коментаря прямо тут, без бічної панелі."),
    ])
    return shot("orders", body, lg)


# ============================================================ 3. Головна
def spark(points, color, w=120, h=34):
    mx, mn = max(points), min(points)
    xs = [i * w / (len(points) - 1) for i in range(len(points))]
    ys = [h - 3 - (p - mn) / (mx - mn or 1) * (h - 6) for p in points]
    d = " ".join(f'{"M" if i == 0 else "L"}{x:.1f},{y:.1f}' for i, (x, y) in enumerate(zip(xs, ys)))
    return f'<svg class="spark" width="{w}" height="{h}"><path d="{d}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="{xs[-1]:.1f}" cy="{ys[-1]:.1f}" r="3" fill="{color}"/></svg>'


def home():
    todo = "".join(f'''<div class="c row" style="gap:12px;padding:14px 16px;flex:1">{sq(i,t,False,17)}<div class="col" style="flex:1;line-height:1.2"><b style="font-size:24px">{n}</b><small class="mut">{l}</small></div><span class="fa">{ic("chevron-right",16)}</span></div>'''
                   for i, t, n, l in [("inbox", "gray", "16", "несортованих · найдовше 2 год"), ("truck", "blue", "3", "прийняті без ТТН"), ("alarm-clock", "red", "2", "нагадування настали"), ("package", "orange", "4", "лежать на пошті > 3 дн"), ("phone", "purple", "5", "лідів чекають дзвінка")])
    kpi = "".join(f'''<div class="c" style="flex:1"><div class="row"><small class="mut" style="flex:1">{l}</small><span class="{"ok" if up else "bd"}" style="font-size:12.5px;font-weight:600">{ic("trending-up" if up else "trending-down",13)} {d}</span></div>
<div class="row" style="align-items:flex-end;margin-top:6px"><b style="font-size:26px;letter-spacing:-.02em;flex:1">{v}</b>{spark(pts, "#16A34A" if up else "#DC2626")}</div><small class="fa">7 днів · порівняно з минулим тижнем</small></div>'''
                  for l, v, d, up, pts in [("Замовлень", "126", "+12%", True, [12, 15, 14, 19, 17, 22, 27]), ("Виручка", "184 350 ₴", "+8%", True, [20, 24, 21, 26, 25, 29, 31]), ("Викуп", "87%", "−3%", False, [91, 90, 92, 89, 88, 88, 87]), ("Середній чек", "1 463 ₴", "+4%", True, [13, 14, 13, 15, 14, 15, 15])])
    rem = "".join(f'<div class="row" style="gap:10px;padding:8px 0;border-top:1px solid #F2F2F0"><b class="num" style="width:44px;font-size:13px">{t}</b><span class="ell" style="flex:1">{a}</span><span class="mut" style="font-size:12.5px">№{n}</span><span class="ib" style="width:26px;height:26px">{ic("phone",13)}</span></div>'
                  for t, a, n in [("11:30", "Передзвонити: уточнити колір", "41"), ("14:00", "Нагадати про посилку", "38"), ("16:00", "Оплата не надійшла", "37"), ("18:00", "Передзвонити після роботи", "43")])
    body = f'''{head("Добрий день, Олено", "вівторок, 3 листопада · у вас <b>11</b> справ", '<span class="srch" style="width:300px">' + ic("search",16) + 'Пошук по CRM<kbd>Ctrl K</kbd></span>' + PLUS("Замовлення"))}
<div class="row" style="gap:8px;margin-bottom:6px"><b style="font-size:15px">Що зробити зараз</b>{mk(10)}</div>
<div class="row" style="gap:10px;margin-bottom:14px">{todo}</div>
<div class="row" style="gap:8px;margin-bottom:6px"><b style="font-size:15px">Тиждень</b>{mk(11)}</div>
<div class="row" style="gap:10px;margin-bottom:14px">{kpi}</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;flex:1;min-height:0;padding-bottom:16px">
<div class="c"><h3>{sq("alarm-clock","red",True,14)}Мої нагадування на сьогодні{mk(12)}<span class="r">усі</span></h3>{rem}</div>
<div class="c"><h3>{sq("chart-column-stacked","blue",True,14)}Замовлення за годинами<span class="r">тиждень</span></h3>
<div class="row" style="align-items:flex-end;gap:6px;height:190px;padding-top:10px">{"".join(f'<div class="col" style="flex:1;align-items:center;gap:6px"><span style="width:100%;height:{h}px;border-radius:7px 7px 3px 3px;background:{"#2E6BE6" if h > 120 else "#C9DBFA"}"></span><small class="fa" style="font-size:11px">{t}</small></div>' for t, h in [("8", 30), ("10", 70), ("12", 110), ("14", 150), ("16", 130), ("18", 160), ("20", 120), ("22", 60)])}</div></div>
</div>'''
    lg = legend("Головна", "Головна відповідає на одне питання: що мені зробити зараз.", [
        (10, "«Що зробити зараз» — п'ять лічильників-дій", "Несортовані, без ТТН, нагадування, лежать на пошті понад 3 дні, ліди без дзвінка. Клік — список із таким фільтром."),
        (11, "Показники з міні-графіком", "Одне число, стрілка порівняно з минулим тижнем і лінія за 7 днів замість окремої сторінки статистики."),
        (12, "Мої нагадування на сьогодні", "За часом, з кнопкою дзвінка: менеджер бачить день одним списком."),
    ])
    return shot("home", body, lg)


# ============================================================ 4. Ліди
def leads():
    G = "18px minmax(180px,1.2fr) minmax(170px,1.2fr) 92px 70px 150px 210px"
    rows = f'<div class="tr h one" style="grid-template-columns:{G}"><span class="cb"></span><span>Лід</span><span>Що цікавить</span><span>Чекає</span><span>Спроби</span><span>Статус</span><span>Результат дзвінка</span></div>'
    for k, (n, g, w, wc, tries, s, src) in enumerate([("Петренко Іван", "Кавоварка Delonghi", "4 хв", "#16A34A", 0, "new", "#DB2777"), ("Олена Шевчук", "Мультиварка Redmond", "22 хв", "#D97706", 1, "new", "#2E6BE6"),
                                                      ("Сергій Коваль", "Пилосос Xiaomi G10", "1 год 40", "#DC2626", 2, "no", "#16A34A"), ("Марія Ткач", "Блендер Philips", "3 год", "#DC2626", 3, "no", "#DB2777"),
                                                      ("Андрій Бойко", "Ваги кухонні", "завтра 10:00", "#7C3AED", 1, "cb", "#D97706"), ("Наталія Гнатюк", "Тостер Bosch", "12 хв", "#16A34A", 0, "new", "#2E6BE6"),
                                                      ("Віталій Руденко", "Праска Tefal", "45 хв", "#D97706", 1, "new", "#16A34A"), ("Юрій Олексюк", "Чайник Xiaomi", "2 год", "#DC2626", 2, "no", "#DB2777")]):
        dots = "".join(f'<i class="{"on" if j < tries else ""}"></i>' for j in range(3))
        res = f'<span class="row" style="gap:5px"><span class="btn sm g" style="height:30px;padding:0 9px;font-size:12px">{ic("phone-missed",13)}Не відповів</span><span class="ib v" style="width:30px;height:30px">{ic("clock",14)}</span><span class="ib g" style="width:30px;height:30px">{ic("check",14)}</span></span>'
        rows += f'''<div class="tr one" style="grid-template-columns:{G};min-height:50px{";background:#FAFAF8" if k == 1 else ""}"><span class="cb"></span><span class="row" style="gap:8px"><i class="dt" style="background:{src}"></i><span class="ell" style="font-weight:500">{n}</span><span class="ib" style="width:24px;height:24px;margin-left:auto">{ic("phone",12)}</span></span>
<span class="ell mut">{g}</span><span class="wait" style="background:color-mix(in srgb,{wc} 12%,white);color:color-mix(in srgb,{wc} 80%,black)">{ic("clock",12)}{w}</span><span class="dots">{dots}</span><span>{st(s)}</span>{res}</div>'''
    body = f'''{head("Ліди", "<b>5</b> нових · <b>2</b> передзвонити · <b>3</b> недодзвон", SEARCH + FILT + PLUS("Лід"))}
<div class="tabs" style="margin-bottom:12px">{"".join(f'<span class="tab{" on" if on else ""}" style="--c:{c}">{n} <em>{q}</em></span>' for n, q, c, on in [("Нові", 5, "#2E6BE6", False), ("Недодзвон", 3, "#D97706", False), ("Передзвонити", 2, "#7C3AED", False), ("Усі активні", 10, "#1F1F1C", True)])}</div>
<div class="tb" style="flex:1;margin-bottom:16px;position:relative">{rows}</div>
{mk(13,"left:660px;top:142px")}{mk(14,"left:1100px;top:154px")}'''
    lg = legend("Ліди", "Лід цінний перші хвилини, тож на першому місці — скільки він чекає.", [
        (13, "Таймер очікування й спроби", "«Чекає 22 хв» кольором (зелений до 15 хв, жовтий, червоний понад годину) і три крапки спроб дзвінка замість колонок «Створено» й «Коментар»."),
        (14, "Результат дзвінка одним кліком", "«Не відповів» (+1 спроба, нагадування через годину), «Передзвонити» (час), «Оформити» (відкриває майстер замовлення з даними ліда)."),
    ])
    return shot("leads", body, lg)


# ============================================================ 5. Товари
def products():
    G = "40px minmax(220px,1.6fr) 120px 200px 130px 120px"
    rows = f'<div class="tr h one" style="grid-template-columns:{G}"><span></span><span>Товар</span><span>Ціна</span><span>Залишок</span><span>Продажі · 30 дн</span><span></span></div>'
    for k, (n, a, p, m, mc, have, cap, days, dcol, sold, c) in enumerate([
            ("Бездротовий мікрофон", "MIC-01", "1 899", "42%", "#16A34A", 142, 200, "≈ 2 міс", "#16A34A", 68, "o"), ("Кільцева лампа 26 см", "LAMP-26", "899", "51%", "#16A34A", 18, 200, "≈ 6 днів", "#D97706", 94, "b"),
            ("Штатив-монопод", "TRI-M", "699", "18%", "#D97706", 3, 200, "≈ 1 день", "#DC2626", 61, "g"), ("Екшн-камера 4К", "CAM-4K", "5 499", "27%", "#16A34A", 0, 200, "немає · 4 в резерві", "#DC2626", 12, "o"),
            ("Смарт-годинник Fit 3", "FIT-3", "2 398", "35%", "#16A34A", 56, 200, "≈ 1 міс", "#16A34A", 40, "b"), ("Павербанк Volt 20 000", "PB-20K", "1 999", "31%", "#16A34A", 77, 200, "≈ 3 тиж", "#16A34A", 70, "g"),
            ("Навушники TWS Pro", "TWS-P", "1 649", "−4%", "#DC2626", 210, 260, "≈ 4 міс", "#16A34A", 30, "o"), ("Чохол MagSafe", "CASE-MS", "449", "62%", "#16A34A", 9, 200, "≈ 4 дні", "#D97706", 66, "b")]):
        bar = f'<div class="col" style="gap:4px"><div class="row" style="gap:6px"><b class="num">{have} шт</b><small style="color:{dcol};font-weight:500">{days}</small></div><div class="bar" style="width:150px"><i style="width:{min(100, have / cap * 100):.0f}%;background:{dcol}"></i></div></div>'
        sp = spark([3, 5, 4, 6, 5, 7, 6, 8] if k % 2 else [6, 5, 7, 4, 5, 3, 4, 3], "#2E6BE6", 70, 24)
        rows += f'''<div class="tr one" style="grid-template-columns:{G};min-height:58px"><span class="ph {c}"></span><div class="col"><span class="ell" style="font-weight:500">{n}</span><small class="mut" style="font:500 11.5px JB">{a}</small></div>
<div class="col"><b class="num">{p} ₴</b><small style="color:{mc};font-weight:500">маржа {m}</small></div>{bar}<span class="row" style="gap:8px">{sp}<b class="num">{sold}</b></span>
<span class="row" style="gap:6px;justify-content:flex-end">{f'<span class="btn sm s" style="height:30px">{ic("shopping-cart",13)}Закупити</span>' if dcol != "#16A34A" else ""}</span></div>'''
    body = f'''{head("Товари", "<b>13</b> товарів · <b>3</b> закінчуються · <b>1</b> немає", SEARCH + PLUS("Товар"))}
<div class="row" style="gap:6px;margin-bottom:12px"><span class="chip on">Усі 13</span><span class="chip">{ic("triangle-alert",13)}Закінчуються 3</span><span class="chip">Немає 1</span><span class="chip">Збиткові 1</span></div>
<div class="tb" style="flex:1;margin-bottom:16px">{rows}</div>{mk(15,"left:752px;top:141px")}{mk(16,"left:600px;top:141px")}'''
    lg = legend("Товари й склад", "Не три числа складу, а відповідь «на скільки вистачить».", [
        (15, "Залишок смужкою і «на скільки днів»", "Одне число, смужка до звичного запасу й прогноз за продажами 30 днів. Жовте й червоне — кнопка «Закупити» в рядку. Резерв і доступно — на наведенні."),
        (16, "Ціна з маржею в одній клітинці", "Ціна великим, маржа % кольором під нею; збиткові видно одразу й є фільтр «Збиткові»."),
    ])
    return shot("prod", body, lg)


# ============================================================ 6. Покупці
def customers():
    G = "minmax(220px,1.4fr) 150px 120px 120px 140px 120px"
    rows = f'<div class="tr h one" style="grid-template-columns:{G}"><span>Покупець</span><span>Сегмент</span><span>Викуп</span><span>Замовлень · сума</span><span>Останнє</span><span>Зв\'язок</span></div>'
    for k, (n, seg, sc, b, bc, o, s, last) in enumerate([("Олена Коваль", "Постійна", "#16A34A", 0.92, "#16A34A", 7, "12 480 ₴", "сьогодні"), ("Андрій Мельник", "Новий", "#2E6BE6", 0, "#C9C8C3", 1, "2 000 ₴", "сьогодні"),
                                                         ("Світлана Олійник", "Ризик", "#DC2626", 0.33, "#DC2626", 3, "4 197 ₴", "учора"), ("Микола Бондаренко", "VIP", "#A16207", 1.0, "#16A34A", 14, "41 300 ₴", "16:37"),
                                                         ("Інна Ковальчук", "Постійна", "#16A34A", 0.8, "#16A34A", 5, "7 245 ₴", "28.10"), ("Віктор Поліщук", "Ризик", "#DC2626", 0.5, "#D97706", 2, "898 ₴", "28.10"),
                                                         ("Ганна Лисенко", "Повторна", "#7C3AED", 1.0, "#16A34A", 2, "598 ₴", "27.10"), ("Роман Кравченко", "Повторна", "#7C3AED", 0.67, "#D97706", 3, "1 794 ₴", "27.10")]):
        rows += f'''<div class="tr one" style="grid-template-columns:{G};min-height:56px"><span class="row" style="gap:10px"><span class="av" style="width:34px;height:34px;font-size:12px">{initials(n)}</span><b class="ell" style="font-weight:500">{n}</b></span>
<span><span class="st" style="--c:{sc}"><i></i>{seg}</span></span><span class="row" style="gap:8px">{ring(f"{int(b*100)}" if b else "—", "", b or 0.001, bc, 34, 3.5, 10.5)}<small class="mut">{"%" if b else "ще немає"}</small></span>
<span class="col"><b class="num">{o}</b><small class="mut num">{s}</small></span><span class="mut">{last}</span><span class="row" style="gap:5px"><span class="ib">{ic("phone",13)}</span><span class="ib v">{ic("message-circle",13)}</span><span class="ib on">{ic("send",13)}</span></span></div>'''
    body = f'''{head("Покупці", "<b>1 284</b> покупці · <b>312</b> постійних · <b>41</b> з ризиком відмови", SEARCH + FILT)}
<div class="row" style="gap:6px;margin-bottom:12px">{"".join(f'<span class="chip{" on" if on else ""}"><i class="dt" style="background:{c}"></i>{n}</span>' for n, c, on in [("Усі", "#1F1F1C", True), ("VIP", "#A16207", False), ("Постійні", "#16A34A", False), ("Повторні", "#7C3AED", False), ("Нові", "#2E6BE6", False), ("Ризик відмови", "#DC2626", False)])}</div>
<div class="tb" style="flex:1;margin-bottom:16px">{rows}</div>{mk(17,"left:528px;top:141px")}{mk(18,"left:1112px;top:150px")}'''
    lg = legend("Покупці", "Замість шести колонок цифр — хто це для бізнесу і як з ним зв'язатись.", [
        (17, "Сегмент і викуп кільцем", "Автоматичні сегменти: новий, повторний, постійний, VIP, ризик відмови (за викупом і відмовами). Кільце викупу читається швидше за «7 / 6 / 1»."),
        (18, "Зв'язок значками", "Дзвінок, Viber, Telegram — як у замовленнях; номер на наведенні. Колонки телефону й email прибрано."),
    ])
    return shot("cust", body, lg)


# ============================================================ 7. Оплати
def payments():
    groups = [("Реєстр НП №1234 · 02.11", "надійшло 12 640 ₴", "ok", [("№37", "Олег Бондаренко", "1 999", "ok"), ("№36", "Інна Ковальчук", "1 649", "ok"), ("№34", "Ганна Лисенко", "299", "ok")], "і ще 9"),
              ("Очікуються · у дорозі й на пошті", "23 490 ₴", "wait", [("№40", "Тарас Ткаченко", "5 499", "wait"), ("№38", "Денис Мельник", "2 398", "late"), ("№32", "Юлія Марченко", "649", "wait")], "і ще 11"),
              ("Розбіжності", "2", "bad", [("№35", "Віктор Поліщук", "449 → 0", "bad"), ("№29", "Ярослав Бойко", "5 499 → 5 400", "bad")], "")]
    body_g = ""
    for t, total, kind, items, more in groups:
        c = {"ok": "#16A34A", "wait": "#D97706", "bad": "#DC2626"}[kind]
        rws = "".join(f'''<div class="row" style="gap:12px;padding:9px 16px;border-top:1px solid #F2F2F0"><span class="num" style="font:600 12px JB;width:40px;color:#57564F">{n}</span><span style="flex:1" class="ell">{who}</span>
<span class="mut" style="font-size:12.5px">{ {"ok": "надійшло 02.11", "wait": "чекаємо", "late": "лежить 5 днів", "bad": "сума не збігається"}[s] }</span><b class="num" style="width:120px;text-align:right">{sm} ₴</b></div>''' for n, who, sm, s in items)
        body_g += f'''<div class="c" style="padding:0;overflow:hidden;margin-bottom:10px"><div class="row" style="gap:10px;padding:12px 16px"><i class="dt" style="background:{c};width:9px;height:9px"></i><b>{t}</b><span style="flex:1"></span><b style="color:{c}">{total}</b></div>{rws}{f'<div class="mut" style="padding:8px 16px;font-size:12.5px;border-top:1px solid #F2F2F0">{more}</div>' if more else ""}</div>'''
    tiles = "".join(f'<div class="c row" style="flex:1;gap:12px">{sq(i,t,False,17)}<div class="col"><small class="mut">{l}</small><b style="font-size:22px">{v}</b></div></div>'
                    for i, t, l, v in [("banknote", "orange", "Післяплата чекає", "23 490 ₴"), ("circle-check", "green", "Надійшло за тиждень", "64 210 ₴"), ("triangle-alert", "red", "Розбіжності", "2"), ("receipt", "blue", "Чеки не пробито", "3")])
    body = f'''{head("Оплати", "листопад · післяплата НП і передоплати", SEARCH + FILT)}
<div class="row" style="gap:10px;margin-bottom:14px">{tiles}{mk(19)}</div>{body_g}'''
    lg = legend("Оплати", "Замість довгої таблиці платежів — три питання: що надійшло, що чекаємо, де розбіжність.", [
        (19, "Зведення й групи за реєстрами НП", "Чотири плитки зверху й групи: «реєстр №… надійшло», «очікуються» (з тими, що лежать понад 4 дні), «розбіжності» — сума НП не збіглась із замовленням. Клік по рядку — замовлення."),
    ])
    return shot("pay", body, lg)


# ============================================================ 8. Пошук і дії Ctrl K
def palette():
    bg = orders_table_bg()
    pal = f'''<div style="position:absolute;inset:0;background:rgba(31,31,28,.28);z-index:7"></div>
<div class="pop" style="left:330px;top:90px;width:640px;padding:0;z-index:9">{mk(20,"top:-9px;left:-9px")}
<div class="row" style="gap:10px;height:56px;padding:0 18px;border-bottom:1px solid #EFEFED;font-size:16px">{ic("search",18)}<span>44</span><span style="width:1.5px;height:20px;background:var(--acc)"></span><span style="flex:1"></span><span class="kb">Esc</span></div>
<div style="padding:8px">
<div class="mut" style="font-size:11.5px;padding:6px 10px">Замовлення</div>
<div class="row" style="gap:10px;padding:9px 10px;border-radius:10px;background:#F2F3F5"><span class="num" style="font:600 12px JB">№44</span><b style="font-weight:500">Олена Коваль</b><span class="mut">Бездротовий мікрофон · 1 899 ₴</span><span style="flex:1"></span>{st("uns")}</div>
<div class="mut" style="font-size:11.5px;padding:10px 10px 6px">Дії з №44</div>
{"".join(f'<div class="row" style="gap:10px;padding:8px 10px;border-radius:10px">{sq(i,t,True,14)}<span style="flex:1">{a}</span><span class="kb">{k}</span></div>' for i, t, a, k in [("check", "blue", "Прийняти замовлення", "Enter"), ("truck", "blue", "Створити ТТН", "Ctrl ⏎"), ("printer", "gray", "Друк бланка", "P"), ("phone", "green", "Подзвонити +380 67 111 22 33", "C")])}
<div class="mut" style="font-size:11.5px;padding:10px 10px 6px">Налаштування й розділи</div>
{"".join(f'<div class="row" style="gap:10px;padding:8px 10px;border-radius:10px">{sq(i,"gray",True,14)}<span style="flex:1">{a}</span><span class="fa" style="font-size:12px">{b}</span></div>' for i, a, b in [("settings", "Налаштування › SMS › шаблон «Посилка на пошті»", "розділ"), ("package", "Товар: Мікрофон петличний MIC-44", "товар")])}
</div></div>'''
    lg = legend("Пошук і дії — Ctrl K", "Один рядок замість пошуку по сторінках і меню.", [
        (20, "Палітра з діями", "Знаходить замовлення, покупця, товар і пункт налаштувань, а для знайденого замовлення одразу пропонує дії: прийняти, ТТН, друк, дзвінок — без відкриття картки. Стрілки й Enter — з клавіатури."),
    ])
    return shot("orders", bg + pal, lg)


def orders_table_bg():
    return orders_body(False)


SCREENS = [("1-zamovlennia", "1 · Замовлення: телефон і доставка значками, А–Б і 1–5", orders_table), ("2-kartka", "2 · Картка замовлення, 6–9", card),
           ("3-golovna", "3 · Головна, 10–12", home), ("4-lidy", "4 · Ліди, 13–14", leads), ("5-tovary", "5 · Товари, 15–16", products),
           ("6-pokuptsi", "6 · Покупці, 17–18", customers), ("7-oplaty", "7 · Оплати, 19", payments), ("8-poshuk", "8 · Ctrl K, 20", palette)]


def build():
    return page("Простір і поля — 20 покращень", CSS, [(k, n, f(), 1820, 900) for k, n, f in SCREENS], cols=1, gap=48)
