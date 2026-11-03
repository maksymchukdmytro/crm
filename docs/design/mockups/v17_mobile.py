"""Мобільна версія v2 — усі екрани в стилі макетів власника (картки з повітрям, кольорові іконки, кільця),
нижня панель — білий острівець із синім «+» по центру (рішення 30.10)."""
from common import *

BLUE, BLUE2, BLUE3 = "#2E6BE6", "#EAF1FD", "#C9DBFA"
CSS = """
.m{--ink:#1F1F1C;--mut:#6F6E69;--faint:#A3A29D;--line:#ECECE9;--bg:#F1F2F4;--acc:#2E6BE6;--acc2:#EAF1FD;--acc3:#C9DBFA;--ok:#16A34A;--warn:#D97706;--bad:#DC2626;
  width:390px;height:844px;background:var(--bg);font:400 14px/1.4 'Onest',sans-serif;color:var(--ink);position:relative;overflow:hidden}
.m b{font-weight:600}
.pad{padding:0 18px}
.hd{display:flex;align-items:center;gap:10px;padding:22px 18px 12px}.hd h1{font-size:29px;font-weight:600;letter-spacing:-.02em;margin-right:auto;line-height:1.1}
.rb{width:44px;height:44px;border-radius:50%;background:#fff;display:grid;place-items:center;color:var(--ink);flex:none;position:relative;box-shadow:0 1px 2px rgba(0,0,0,.04)}
.rb.p{background:var(--acc);color:#fff}.rb .dot{position:absolute;top:9px;right:10px;width:8px;height:8px;border-radius:50%;background:var(--acc);box-shadow:0 0 0 2px #fff}
.rb em{position:absolute;top:-3px;right:-3px;min-width:18px;height:18px;border-radius:99px;background:var(--acc);color:#fff;font:600 10.5px/18px 'Onest';text-align:center;padding:0 5px;font-style:normal;box-shadow:0 0 0 2px var(--bg)}
.tabs{display:flex;gap:7px;padding:0 18px 12px;white-space:nowrap;overflow:hidden}
.tabs span{height:36px;padding:0 14px;border-radius:99px;display:inline-flex;align-items:center;gap:6px;font-weight:500;font-size:14.5px;flex:none;
  background:color-mix(in srgb,var(--c,#7C7B76) 12%,white);color:color-mix(in srgb,var(--c,#7C7B76) 75%,black)}
.tabs span.on{background:var(--ink);color:#fff}.tabs em{font-style:normal;opacity:.65;font-weight:500}
.utabs{display:flex;gap:18px;white-space:nowrap;padding:0 18px;border-bottom:1px solid #E3E3E0;margin-bottom:12px}.utabs span{padding:4px 0 11px;font-size:16px;color:var(--mut);font-weight:500}
.utabs span.on{color:var(--ink);font-weight:600;box-shadow:inset 0 -2.5px 0 var(--ink)}
.c{background:#fff;border-radius:20px;padding:14px 16px;margin:0 14px 10px}
.c h3{display:flex;align-items:center;gap:9px;font-size:16px;font-weight:600;margin-bottom:10px}.c h3 small{font-weight:400;color:var(--faint);font-size:13px}
.c h3 .r{margin-left:auto;font-size:13.5px;font-weight:500;color:var(--acc)}
.sq{width:34px;height:34px;border-radius:11px;display:grid;place-items:center;flex:none;background:var(--s,#EAF1FD);color:var(--i,#2E6BE6)}
.sq.sm{width:30px;height:30px;border-radius:9px}
.st{display:inline-flex;align-items:center;gap:5px;height:24px;padding:0 9px;border-radius:99px;font-size:12.5px;font-weight:500;
  background:color-mix(in srgb,var(--c) 12%,white);color:color-mix(in srgb,var(--c) 75%,black);white-space:nowrap}
.st i{width:6px;height:6px;border-radius:50%;background:var(--c)}
.np{background:#E5262B;color:#fff;border-radius:6px;font:700 10.5px/1 'Onest';padding:4px 5px;flex:none}
.thumb{width:40px;height:40px;border-radius:12px;background:#ECEDEF;display:grid;place-items:center;color:#9C9C98;flex:none}
.thumb.l{width:58px;height:58px;border-radius:14px}
.mut{color:var(--mut)}.fa{color:var(--faint)}.ok{color:var(--ok)}.wr{color:var(--warn)}.bd{color:var(--bad)}
.row{display:flex;align-items:center;gap:10px}
.sep{height:1px;background:#EFEFED;margin:10px 0}
.kv{display:flex;justify-content:space-between;font-size:14px;padding:3px 0}.kv span{color:var(--mut)}.kv b{font-weight:600}
.btn{height:46px;border-radius:15px;display:flex;align-items:center;justify-content:center;gap:8px;font-weight:600;font-size:15px;background:#fff;color:var(--ink)}
.btn.p{background:var(--acc);color:#fff;box-shadow:0 8px 18px -8px rgba(46,107,230,.7)}.btn.s{background:var(--acc2);color:var(--acc)}
.chip{height:32px;padding:0 12px;border-radius:99px;display:inline-flex;align-items:center;gap:6px;font-size:13.5px;font-weight:500;background:#fff;color:var(--ink);border:1px solid #E6E6E3;white-space:nowrap}
.chip.on{background:var(--acc2);border-color:var(--acc3);color:#1F4FB8}.chip.dash{border-style:dashed;color:var(--mut)}
.inp{height:46px;border-radius:14px;background:#fff;display:flex;align-items:center;gap:9px;padding:0 14px;color:var(--faint);font-size:15px}
.inp.b{border:1px solid #E6E6E3}.inp b{color:var(--ink);font-weight:500}.inp .cv{margin-left:auto;color:var(--faint)}
.lab{font-size:12.5px;color:var(--mut);margin:0 0 5px 2px}
.ring{position:relative;display:grid;place-items:center;text-align:center;font-weight:600;line-height:1.05;flex:none}
.ring svg{position:absolute;inset:0}.ring small{display:block;font-size:10px;font-weight:500}
.sticky{position:absolute;left:0;right:0;bottom:0;padding:12px 14px 22px;background:linear-gradient(rgba(241,242,244,0),var(--bg) 26%);display:flex;gap:10px}
.sticky .btn{height:54px;border-radius:17px}
/* нижня панель — білий острівець */
.bar{position:absolute;left:12px;right:12px;bottom:14px;height:66px;border-radius:24px;display:grid;grid-template-columns:repeat(5,1fr);align-items:center;z-index:5;
  background:rgba(255,255,255,.9);box-shadow:0 12px 30px -10px rgba(31,31,28,.25),0 0 0 1px rgba(31,31,28,.06)}
.bar a{position:relative;display:flex;flex-direction:column;align-items:center;gap:3px;font-size:11px;font-weight:500;color:#8A8984}
.bar a .ico{width:44px;height:30px;border-radius:99px;display:grid;place-items:center}.bar a.on{color:var(--acc)}.bar a.on .ico{background:var(--acc2)}
.bar a i{position:absolute;top:-6px;left:calc(50% + 4px);min-width:18px;height:18px;border-radius:99px;font:600 10.5px/18px 'Onest';text-align:center;padding:0 5px;font-style:normal;background:var(--acc);color:#fff;box-shadow:0 0 0 2px #fff}
.bar .plus{justify-self:center;width:56px;height:56px;border-radius:18px;display:grid;place-items:center;background:var(--acc);color:#fff;box-shadow:0 8px 18px -6px rgba(46,107,230,.7)}
.dim{position:absolute;inset:0;background:rgba(24,24,22,.38);z-index:6}
.sheet{position:absolute;left:0;right:0;bottom:0;z-index:7;background:#F7F7F8;border-radius:26px 26px 0 0;padding:10px 16px 22px}
.sheet .grab{width:40px;height:5px;border-radius:99px;background:#D6D6D3;margin:0 auto 12px}
.sheet h2{font-size:21px;font-weight:600;display:flex;align-items:center;margin-bottom:12px}.sheet h2 .x{margin-left:auto}
.seg{display:flex;background:#E8E9EC;border-radius:13px;padding:3px;gap:2px}.seg span{flex:1;height:36px;border-radius:10px;display:grid;place-items:center;font-size:13.5px;font-weight:500;color:var(--mut)}
.seg span.on{background:#fff;color:var(--ink);box-shadow:0 1px 2px rgba(0,0,0,.08)}
.tgl{width:46px;height:28px;border-radius:99px;background:#D9D8D3;position:relative;flex:none}.tgl::after{content:"";position:absolute;left:3px;top:3px;width:22px;height:22px;border-radius:50%;background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.2)}
.tgl.on{background:var(--acc)}.tgl.on::after{left:21px}
.cb{width:22px;height:22px;border-radius:7px;border:1.5px solid #CFCEC9;display:grid;place-items:center;flex:none;background:#fff}.cb.on{background:var(--acc);border-color:var(--acc);color:#fff}
"""

SC = {"uns": ("Несортований", "#7C7B76"), "acc": ("Прийнятий", "#2E6BE6"), "sent": ("Відправлений", "#6D5BD0"), "wait": ("Очікує на пошті", "#D97706"),
      "done": ("Завершений", "#16A34A"), "pref": ("Відмова на пошті", "#E11D48"), "ref": ("Відмова", "#DC2626"),
      "new": ("Новий", "#2E6BE6"), "no": ("Недодзвон", "#D97706"), "cb": ("Передзвонити", "#7C3AED")}
TINT = {"blue": ("#EAF1FD", "#2E6BE6"), "green": ("#E9F6EE", "#16A34A"), "orange": ("#FDF1E3", "#D97706"), "purple": ("#F1ECFB", "#7C3AED"),
        "red": ("#FDECEC", "#DC2626"), "gray": ("#F0F0EE", "#57564F"), "teal": ("#E6F6F4", "#0E9488")}


def st(k):
    n, c = SC[k]
    return f'<span class="st" style="--c:{c}"><i></i>{n}</span>'


def sq(icon, t="blue", sm=False, size=17):
    s, i = TINT[t]
    return f'<span class="sq{" sm" if sm else ""}" style="--s:{s};--i:{i}">{ic(icon, size)}</span>'


def ring(v, unit, frac, color, size=56, sw=4.5, fs=14):
    r = size / 2 - sw
    L = 2 * 3.14159 * r
    return (f'<span class="ring" style="width:{size}px;height:{size}px;color:{color};font-size:{fs}px"><svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
            f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="#EEEEEA" stroke-width="{sw}"/>'
            f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-dasharray="{L*frac:.1f} {L:.1f}" transform="rotate(-90 {size/2} {size/2})"/></svg>'
            f'<span>{v}{f"<small>{unit}</small>" if unit else ""}</span></span>')


def bar(active):
    def it(k, icon, label, n=None):
        return f'<a class="{"on" if k == active else ""}"><span class="ico">{ic(icon, 21)}</span>{label}{f"<i>{n}</i>" if n else ""}</a>'
    return f'<nav class="bar">{it("home","house","Головна")}{it("orders","receipt-text","Замовлення",16)}<span class="plus">{ic("plus",27,2.4)}</span>{it("leads","inbox","Ліди",4)}{it("more","ellipsis","Ще")}</nav>'


def head(title, btns="", sub=""):
    return f'<div class="hd"><div style="margin-right:auto"><h1>{title}</h1>{f"<div class=mut style=font-size:13px;margin-top:2px>{sub}</div>" if sub else ""}</div>{btns}</div>'


def rb(icon, cls="", extra=""):
    return f'<span class="rb {cls}">{ic(icon, 20)}{extra}</span>'


def tabs(items):
    return '<div class="tabs">' + "".join(f'<span class="{"on" if on else ""}" style="--c:{c}">{n}{f" <em>{k}</em>" if k != "" else ""}</span>' for n, k, c, on in items) + "</div>"


def scr(inner):
    return f'<div class="m">{inner}</div>'


# ======================================================================== 1. Головна
def home():
    bars = [(22, False), (34, False), (12, False), (24, False), (8, False), (6, False), (48, True)]
    days = ["пн", "вт", "ср", "чт", "пт", "сб", "сьогодні"]
    bh = "".join(f'<div style="display:flex;flex-direction:column;align-items:center;gap:6px;flex:1"><span style="width:100%;height:{h}px;border-radius:7px;background:{"#5B8EF0" if on else "#3A3A3F"}"></span><small style="font-size:10.5px;color:#8D8D92">{d}</small></div>' for (h, on), d in zip(bars, days))
    tile = lambda icon, t, d, dc, v, l: f'''<div class="c" style="margin:0;padding:11px 13px"><div class="row" style="justify-content:space-between">{sq(icon,t,True,15)}<span class="st" style="--c:{dc};height:22px">{d}</span></div>
<div style="font-size:22px;font-weight:600;letter-spacing:-.02em;margin-top:6px">{v}</div><div class="mut" style="font-size:12.5px">{l}</div></div>'''
    pills = "".join(f'<span style="flex:1;min-width:0;background:#fff;border-radius:16px;padding:8px 12px 8px 8px;display:flex;align-items:center;gap:9px">{sq(i,t,True,15)}<span style="line-height:1.15"><b style="font-size:16px">{n}</b><br><small class="mut" style="font-size:11.5px">{l}</small></span></span>'
                    for i, t, n, l in [("inbox", "red", "4", "нові ліди"), ("clock", "orange", "16", "несортовані"), ("package", "blue", "2", "відправити")])
    top = "".join(f'<div class="row" style="padding:7px 0;{"border-top:1px solid #F0F0EE" if k else ""}"><span class="thumb">{ic("package",17)}</span><span style="flex:1;line-height:1.25"><b style="font-weight:500">{n}</b><br><small class="mut">{q} шт</small></span><b>{s} ₴</b></div>'
                  for k, (n, q, s) in enumerate([("Павербанк Volt 20 000", 142, "227 058"), ("Чохол MagSafe", 118, "52 982")]))
    body = f'''<div class="hd" style="padding-bottom:10px"><span class="rb" style="background:#E3E9F7;color:#3557A8;font-weight:600">А</span><div style="margin-right:auto;line-height:1.2"><small class="mut" style="font-size:12.5px">Пʼятниця, 30 жовтня</small><br><b style="font-size:17px">Привіт, Адміністраторе</b></div>{rb("search")}{rb("bell","",'<em>1</em>')}</div>
<div style="display:flex;gap:8px;padding:0 14px 12px;overflow:hidden">{pills}</div>
<div style="margin:0 14px 10px;background:#1E1E22;border-radius:22px;padding:16px 18px 14px;color:#fff">
<div class="row" style="justify-content:space-between"><span style="color:#B7B7BC;font-size:13px">Продано сьогодні · 5 замовлень</span><span class="st" style="--c:#16A34A;background:#1E3A2A;color:#4ADE80">{ic("arrow-up-right",12)}11%</span></div>
<div style="font-size:40px;font-weight:600;letter-spacing:-.03em;line-height:1.15;margin:2px 0 8px">18 896 <span style="font-size:24px;color:#9E9EA3">₴</span></div>
<div style="display:flex;align-items:flex-end;gap:8px;height:66px">{bh}</div></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:0 14px 10px">{tile("calendar","blue","+9%","#16A34A","130 020 ₴","за жовтень")}{tile("wallet","green","+4%","#16A34A","3 334 ₴","середній чек")}
{tile("check","purple","+3 п.","#16A34A","72%","апрув")}{tile("truck","orange","−2 п.","#DC2626","78%","викуп")}</div>
<div class="c"><h3>Топ товарів<span class="r">Усі →</span></h3>{top}</div>{bar("home")}'''
    return scr(body)


# ======================================================================== 2. Замовлення
ORD = [("uns", True, False, "44", "17:10", "Олена Коваль", "1 899", "Бездротовий мікрофон", "", True),
       ("uns", False, True, "43", "17:00", "Андрій Мельник", "2 000", "Набір капсул 50 шт", "+1", False),
       ("sent", False, False, "42", "16:37", "Микола Бондаренко", "3 899", "Радіосистема DJI Mic 2", "", True),
       ("wait", False, False, "40", "15:50", "Тарас Ткаченко", "5 499", "Екшн-камера 4К", "", True)]


def order_card(o):
    s, warn, cmt, no, t, nm, sm, g, more, np_ = o
    flags = (f'<span class="sq sm" style="--s:#FDF1E3;--i:#D97706;width:24px;height:24px;border-radius:8px">{ic("circle-alert",14)}</span>' if warn else "") + \
            (f'<span class="sq sm" style="--s:#EAF1FD;--i:#2E6BE6;width:24px;height:24px;border-radius:8px">{ic("message-square",13)}</span>' if cmt else "")
    dl = '<span class="np">НП</span>' if np_ else '<span class="fa" style="font-size:12.5px">без доставки</span>'
    return f'''<div class="c" style="padding:12px 14px"><div class="row" style="gap:7px">{st(s)}{flags}<span class="fa" style="margin-left:auto;font-size:12.5px">№{no} · {t}</span></div>
<div class="row" style="margin:7px 0 0;justify-content:space-between"><b style="font-size:17px">{nm}</b><b style="font-size:17px">{sm} <span class="fa" style="font-size:13px">₴</span></b></div>
<div class="sep" style="margin:9px 0"></div><div class="row"><span class="thumb" style="width:30px;height:30px;border-radius:9px">{ic("package",14)}</span><span style="flex:1;font-size:13.5px">{g} <span class="fa">{more}</span></span>{dl}</div></div>'''


def orders(extra="", dim=False):
    body = f'''{head("Замовлення", rb("search") + rb("list-filter", "", '<span class="dot"></span>'))}
{tabs([("Усі", 42, "#1F1F1C", True), ("Несортовані", 16, "#7C7B76", False), ("Прийняті", 2, "#2E6BE6", False), ("Відправлені", 5, "#6D5BD0", False)])}
<div class="row pad" style="gap:6px;margin:-2px 0 10px"><span class="chip on">{ic("calendar",13)}Сьогодні й учора{ic("x",12)}</span><span class="chip on">НП{ic("x",12)}</span></div>
{"".join(order_card(o) for o in ORD)}{bar("orders")}{extra}'''
    return scr(body)


# ======================================================================== 3–4. Картка замовлення
def card_top():
    acts = "".join(f'<div class="c" style="margin:0;padding:12px 0 10px;display:flex;flex-direction:column;align-items:center;gap:7px">{sq(i,t,False,18)}<span style="font-size:13px;font-weight:500">{l}</span></div>'
                   for i, t, l in [("truck", "blue", "ТТН"), ("printer", "gray", "Друк"), ("receipt", "green", "Чек"), ("bell", "orange", "Нагадати")])
    msg = "".join(f'<span class="btn {"p" if k == 0 else ""}" style="flex:1;height:44px;border-radius:14px;{"" if k else ""}background:{BLUE if k == 0 else "#F2F3F5"};color:{"#fff" if k == 0 else "#3D3C38"}">{ic(i,18)}</span>'
                  for k, i in enumerate(["phone", "message-circle", "send", "message-square"]))
    body = f'''<div class="hd" style="padding-bottom:10px">{rb("chevron-left")}<div style="flex:1;text-align:center;line-height:1.25"><b style="font-size:16.5px">Замовлення №27</b><br><small class="mut">30.10, 13:50 · лендинг</small></div>{rb("ellipsis")}</div>
<div class="c"><div class="row"><span class="rb" style="width:50px;height:50px;background:#E3E9F7;color:#3557A8;font-weight:600;font-size:16px">ОК</span>
<div style="flex:1;line-height:1.3"><b style="font-size:17.5px">Коваленко Олена</b><br><span class="mut">+380 67 111 22 33</span></div><div style="text-align:right;line-height:1.2"><b style="font-size:21px">2 499<span class="fa" style="font-size:14px"> ₴</span></b><br><small class="mut">до сплати</small></div></div>
<div class="row" style="gap:8px;margin:12px 0">{msg}</div><div class="sep" style="margin:0 0 10px"></div>
<div style="display:grid;grid-template-columns:1fr 1fr 1.3fr;font-size:12.5px" class="mut"><div><b style="font-size:16px;color:#1F1F1C">1</b><br>замовлення</div><div style="border-left:1px solid #EFEFED;padding-left:12px"><b style="font-size:16px;color:#1F1F1C">—</b><br>викуп</div>
<div style="border-left:1px solid #EFEFED;padding-left:12px"><b style="font-size:14.5px;color:#1F1F1C">Максимчук</b><br>юрособа ✓</div></div></div>
<div style="margin:0 14px 10px;height:50px;border-radius:16px;background:#7C7B76;color:#fff;display:flex;align-items:center;gap:10px;padding:0 16px"><span style="width:9px;height:9px;border-radius:50%;background:#fff"></span><b style="font-size:16px">Несортований</b><span style="margin-left:auto;font-size:13px;opacity:.85;display:flex;align-items:center;gap:4px">змінити{ic("chevron-down",15)}</span></div>
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;padding:0 14px 10px">{acts}</div>
<div class="c row" style="gap:13px">{ring("2/5","",.4,"#16A34A",50,4.5,13)}<div><b style="font-size:15.5px">Що лишилось</b><div class="row" style="gap:6px;margin-top:7px">
<span class="chip" style="height:28px;font-size:12.5px;background:#F3F4F6;border:0">Оплата</span><span class="chip" style="height:28px;font-size:12.5px;background:#F3F4F6;border:0">ТТН</span><span class="chip" style="height:28px;font-size:12.5px;background:#F3F4F6;border:0">Видаткова</span></div></div></div>
<div class="c"><h3>{sq("package","purple",True,15)}Товари <small>1</small><span class="r">+ Товар</span></h3>
<div class="row"><span class="thumb l">{ic("package",20)}</span><div style="flex:1;line-height:1.3"><b style="font-weight:500;font-size:15px">Кавоварка Delonghi</b><br><small class="mut">ART-001 · на складі 12</small></div><b style="font-size:16px">2 499 ₴</b></div></div>
<div class="sticky"><span class="btn" style="width:54px;flex:none">{ic("phone",20)}</span><span class="btn p" style="flex:1">{ic("check",19)}Прийняти замовлення</span></div>'''
    return scr(body)


def card_bottom():
    offers = "".join(f'''<div style="flex:1;min-width:0;background:#F6F7F8;border-radius:16px;padding:8px"><div class="thumb" style="width:100%;height:46px;border-radius:12px">{ic("package",18)}</div>
<div style="font-size:12.5px;font-weight:500;margin:6px 0 3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{n}</div><div class="row" style="justify-content:space-between"><b style="font-size:13.5px">{p} ₴</b><span class="sq sm" style="--s:#2E6BE6;--i:#fff;width:26px;height:26px;border-radius:50%">{ic("plus",15,2.4)}</span></div></div>'''
                     for n, p in [("Адаптер USB-C", "349"), ("Карта 64 ГБ", "399"), ("Чохол", "299")])
    body = f'''<div style="height:10px"></div>
<div class="c"><h3>{sq("package","purple",True,15)}Товари <small>2</small><span class="r">+ Товар</span></h3>
<div class="row"><span class="thumb l">{ic("package",20)}</span><div style="flex:1"><b style="font-weight:500;font-size:15px">Кавоварка Delonghi</b>
<div class="row" style="gap:12px;margin-top:6px;height:30px;border:1px solid #E6E6E3;border-radius:99px;width:max-content;padding:0 10px"><span class="fa">−</span><b>1</b><span class="fa">+</span></div></div><b style="font-size:16px">2 499 ₴</b></div>
<div class="row" style="margin:10px 0 0 22px;background:#F6F7F8;border-radius:14px;padding:8px"><span class="thumb" style="background:#fff">{ic("link",15)}</span><div style="flex:1;line-height:1.3"><span class="st" style="--c:#7C3AED;height:20px;font-size:11.5px">допродаж</span><br><b style="font-weight:500">Набір капсул 50 шт</b></div><b>349 ₴</b></div>
<div class="mut" style="font-size:13px;margin:12px 0 8px">Часто беруть разом</div><div style="display:flex;gap:8px">{offers}</div>
<div class="sep"></div><div class="kv"><span>Знижка <b style="color:#1F1F1C">0 ₴</b></span><span>Прибуток <b class="ok">1 048 ₴</b></span></div></div>
<div class="c"><h3>{sq("wallet","green",True,15)}Оплата<span class="r">+ Оплата</span></h3>
<div class="row" style="justify-content:space-between"><div style="line-height:1.3"><small class="mut">Вид оплати</small><br><b style="font-weight:500;font-size:15px">Передоплата</b></div><div style="text-align:right;line-height:1.3"><small class="mut">у ТТН · контроль оплати</small><br><b style="font-size:16px">2 648 ₴</b></div></div>
<div class="row" style="margin-top:10px;background:#F6F7F8;border-radius:14px;padding:9px 11px;gap:9px">{sq("landmark","green",True,14)}<div style="flex:1;line-height:1.25;font-size:13px"><b style="font-weight:500">200 ₴ · Monobank · ФОП Максимчук</b><br><span class="ok">надійшла 30.10, 14:50 · Олена</span></div></div></div>
<div class="c"><h3>{sq("truck","blue",True,15)}Доставка</h3>
<div class="row"><span class="np" style="padding:7px 7px;font-size:12px">НП</span><div style="flex:1;line-height:1.3"><b style="font-weight:500;font-size:15px">Тульчин · Відділення №3</b><br><small class="mut">платить одержувач · ≈ 85 ₴</small></div>{ic("chevron-right",18)}</div>
<div class="row" style="gap:8px;margin-top:12px"><span class="btn s" style="flex:1;height:44px">{ic("truck",17)}Створити ТТН</span><span class="btn" style="width:44px;height:44px;background:#F2F3F5">{ic("ellipsis",18)}</span></div></div>
<div class="sticky"><span class="btn" style="width:54px;flex:none">{ic("phone",20)}</span><span class="btn p" style="flex:1">{ic("check",19)}Прийняти замовлення</span></div>'''
    return scr(body)


# ======================================================================== 5. Ліди
LEADS = [("1", "дн", 1, "#DC2626", "new", "Петренко Іван", "Кавоварка Delonghi · 2 299 ₴", True),
         ("6", "год", .9, "#DC2626", "new", "Коваленко Олена", "Кавоварка Delonghi · 2 499 ₴", False),
         ("54", "хв", .6, "#D97706", "no", "Дмитро Савчук", "Екшн-камера 4К · 5 499 ₴", False),
         ("3", "хв", .2, "#16A34A", "new", "Оксана Кравець", "Штатив-монопод · 2 797 ₴", False)]


def leads():
    cards = "".join(f'''<div class="c row" style="gap:12px;padding:13px 13px 13px 12px">{ring(v,u,f,c)}<div style="flex:1;min-width:0">{st(s)}<div style="font-size:17px;font-weight:600;margin:3px 0 1px">{n}</div><div class="mut" style="font-size:13px">{g}</div></div>
<span class="btn {"p" if p else "s"}" style="width:52px;height:52px;border-radius:16px;flex:none">{ic("phone",20)}</span></div>''' for v, u, f, c, s, n, g, p in LEADS)
    body = f'''{head("Ліди", rb("search") + rb("list-filter"))}{tabs([("Відкриті", 6, "#1F1F1C", True), ("Нові", 4, "#2E6BE6", False), ("Недодзвон", 2, "#D97706", False), ("Передзвонити", 1, "#7C3AED", False)])}
<div style="margin:0 14px 10px;background:linear-gradient(135deg,#2E6BE6,#2457C5);border-radius:22px;color:#fff;padding:16px 18px;display:flex;align-items:center">
<div><b style="font-size:30px;display:block;line-height:1">6</b><small style="opacity:.85;font-size:13px">чекають дзвінка<br>найдовше — 1 день</small></div><span class="btn" style="margin-left:auto;color:{BLUE};border-radius:99px;padding:0 18px">{ic("phone",18)}Дзвонити</span></div>
{cards}{bar("leads")}'''
    return scr(body)


# ======================================================================== 6. Вікно ліда (дзвінок)
def lead_window():
    calls = "".join(f'<div class="row" style="padding:7px 0;{"border-top:1px solid #F0F0EE" if k else ""}">{sq(i,t,True,14)}<span style="flex:1;font-size:13.5px">{a}</span><small class="fa">{w}</small></div>'
                    for k, (i, t, a, w) in enumerate([("phone", "orange", "Недодзвон · SMS надіслано", "сьогодні 12:10"), ("phone", "gray", "Не відповів", "учора 18:40")]))
    body = f'''<div class="hd" style="padding-bottom:10px">{rb("chevron-left")}<div style="flex:1;line-height:1.25;text-align:center"><b style="font-size:16.5px">Лід Л-2047</b><br><small class="mut">Instagram · 30.10, 09:12</small></div>{rb("ellipsis")}</div>
<div class="c"><div class="row" style="gap:13px">{ring("1","дн",1,"#DC2626",56)}<div style="flex:1;line-height:1.3">{st("no")}<div style="font-size:19px;font-weight:600;margin-top:4px">Петренко Іван</div><span class="mut">+380 67 555 12 40 · спроба 2</span></div></div>
<div class="row" style="gap:8px;margin-top:13px"><span class="btn p" style="flex:2.2">{ic("phone",18)}Подзвонити</span><span class="btn" style="flex:1;background:#F2F3F5">{ic("message-circle",18)}</span><span class="btn" style="flex:1;background:#F2F3F5">{ic("send",18)}</span></div></div>
<div class="c"><h3>{sq("inbox","blue",True,15)}Запит<small>з форми</small></h3><div class="row"><span class="thumb l">{ic("package",20)}</span><div style="flex:1;line-height:1.3"><b style="font-weight:500;font-size:15px">Кавоварка Delonghi</b><br><small class="mut">1 шт · ціна з лендингу</small></div><b style="font-size:16px">2 299 ₴</b></div>
<div class="sep"></div><div class="kv"><span>UTM</span><b style="font-weight:500">instagram · stories</b></div><div class="kv"><span>Коментар</span><b style="font-weight:500">Чи є чорний колір?</b></div></div>
<div class="c"><h3>{sq("clock","orange",True,15)}Дзвінки<small>2 спроби</small></h3>{calls}</div>
<div class="sticky" style="flex-direction:column;gap:8px"><div class="row" style="gap:6px"><span class="btn" style="flex:1;height:42px;font-size:13.5px">{ic("phone",15)}Недодзвон</span><span class="btn" style="flex:1;height:42px;font-size:13.5px">{ic("clock",15)}Передзвонити</span><span class="btn" style="flex:1;height:42px;font-size:13.5px;color:{"#DC2626"}">{ic("x",15)}Відмова</span></div>
<span class="btn p">{ic("check",19)}Створити замовлення</span></div>'''
    return scr(body)


# ======================================================================== 7. Товари
PRODS = [("у продажу", "#16A34A", "Кавоварка Delonghi", "2 499", "12 шт", "маржа 36%"), ("закінчується", "#D97706", "Бездротовий мікрофон", "1 899", "3 шт", "маржа 34%"),
         ("у продажу", "#16A34A", "Екшн-камера 4К", "5 499", "100 шт", "маржа 22%"), ("допродаж", "#7C3AED", "Набір капсул 50 шт", "349", "30 шт", ""),
         ("у продажу", "#16A34A", "Кільцева лампа 26 см", "899", "100 шт", "")]


def products():
    rows = "".join(f'''<div class="row" style="padding:12px 2px;{"border-top:1px solid #F0F0EE" if k else ""}"><span class="thumb l">{ic("package",20)}</span><div style="flex:1;line-height:1.35">
<span class="st" style="--c:{c};height:22px">{"<i></i>" if s != "допродаж" else ""}{s}</span><br><b style="font-weight:500;font-size:16px">{n}</b><br><span style="font-size:13.5px"><b>{p} ₴</b> <span class="mut">· {q}{f" · {m}" if m else ""}</span></span></div>{ic("chevron-right",18)}</div>'''
                   for k, (s, c, n, p, q, m) in enumerate(PRODS))
    body = f'''{head("Товари", rb("scan-barcode") + rb("plus","p"))}<div class="utabs"><span class="on">Товари 13</span><span>Категорії</span><span>Виробники</span><span>Атрибути</span></div>
<div class="row pad" style="gap:8px;margin-bottom:10px"><span class="inp" style="flex:1;white-space:nowrap;overflow:hidden">{ic("search",17)}Назва, артикул</span><span class="inp" style="flex:none;color:#1F1F1C;font-weight:500">Залишок{ic("chevron-down",15)}</span><span class="rb" style="width:46px;height:46px;border-radius:14px">{ic("list-filter",18)}</span></div>
<div class="c" style="padding:4px 14px">{rows}</div>{bar("more")}'''
    return scr(body)


# ======================================================================== 8. Картка товару
def product_card():
    vr = "".join(f'<div class="row" style="padding:8px 0;{"border-top:1px solid #F0F0EE" if k else ""}"><i style="width:14px;height:14px;border-radius:5px;background:{c};box-shadow:inset 0 0 0 1px rgba(0,0,0,.15)"></i><span style="flex:1;font-size:14px">{n}</span><span class="{cl}" style="font-size:13.5px;width:52px;text-align:right">{s} шт</span><span class="tgl {"on" if on else ""}" style="transform:scale(.8)"></span></div>'
                 for k, (n, c, s, cl, on) in enumerate([("Чорний", "#151515", 8, "", True), ("Білий", "#F4F4F2", 3, "wr", True), ("Червоний", "#C62828", 0, "bd", False)]))
    body = f'''<div class="hd" style="padding-bottom:10px">{rb("chevron-left")}<div style="flex:1;text-align:center"><b style="font-size:16.5px">Товар</b></div>{rb("ellipsis")}</div>
<div class="c" style="padding:12px"><div class="row" style="gap:10px;align-items:stretch"><div class="thumb" style="width:120px;height:120px;border-radius:16px">{ic("image",30)}</div>
<div style="flex:1;line-height:1.3"><span class="st" style="--c:#16A34A"><i></i>у продажу</span><div style="font-size:19px;font-weight:600;margin:5px 0 2px">Кавоварка Delonghi</div><small class="mut">ART-001 · Кавоварки · Delonghi</small>
<div class="row" style="gap:6px;margin-top:9px">{"".join(f'<span class="thumb" style="width:34px;height:34px;border-radius:10px">{ic("image",14)}</span>' for _ in range(2))}<span class="thumb" style="width:34px;height:34px;border-radius:10px;background:#fff;border:1.5px dashed #D6D6D3">{ic("plus",14)}</span></div></div></div></div>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding:0 14px 10px">{"".join(f'<div class="c" style="margin:0;padding:11px 12px"><small class="mut" style="font-size:12px">{l}</small><div style="font-size:18px;font-weight:600;{c}">{v}</div></div>' for l, v, c in [("Ціна", "2 499 ₴", ""), ("Собівартість", "1 600 ₴", ""), ("Маржа", "36%", "color:#16A34A")])}</div>
<div class="c"><h3>{sq("boxes","orange",True,15)}Склад<span class="r">Рухи</span></h3><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;text-align:center">{"".join(f'<div style="background:#F6F7F8;border-radius:14px;padding:9px"><b style="font-size:18px;{c}">{v}</b><br><small class="mut">{l}</small></div>' for l, v, c in [("на складі", "14", ""), ("резерв", "2", ""), ("доступно", "12", "color:#16A34A")])}</div></div>
<div class="c"><h3>{sq("palette","purple",True,15)}Варіанти<small>колір</small><span class="r">+ Варіант</span></h3>{vr}</div>
<div class="c row" style="gap:12px">{sq("chart-bar","blue")}<div style="flex:1;line-height:1.3"><b style="font-size:15px">142 шт · 227 058 ₴</b><br><small class="mut">продано за 30 днів · викуп 81%</small></div>{ic("chevron-right",18)}</div>
<div class="sticky"><span class="btn p" style="flex:1">{ic("check",19)}Зберегти</span></div>'''
    return scr(body)


# ======================================================================== 9. Ще
def more():
    def tile(icon, t, l, n=None):
        badge = f'<span style="position:absolute;top:10px;right:10px;min-width:22px;height:22px;border-radius:99px;background:#FDF1E3;color:#B45309;font:600 12px/22px Onest;text-align:center">{n}</span>' if n else ""
        return f'<div class="c" style="margin:0;padding:13px;position:relative;height:104px;display:flex;flex-direction:column;justify-content:space-between">{sq(icon,t,False,18)}{badge}<b style="font-size:14.5px;font-weight:600;line-height:1.2">{l}</b></div>'
    grp = lambda title, tiles: f'<div class="mut" style="font-size:13.5px;font-weight:500;margin:4px 20px 8px">{title}</div><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding:0 14px 12px">{tiles}</div>'
    rows = "".join(f'<div class="row" style="padding:12px 0;{"border-top:1px solid #F0F0EE" if k else ""}">{ic(i,19)}<span style="flex:1;font-size:15px">{l}</span>{x}</div>'
                   for k, (i, l, x) in enumerate([("settings", "Налаштування", ic("chevron-right", 17)), ("clock-fading", "Журнал дій", ic("chevron-right", 17)),
                                                  ("activity", "Система", '<span style="width:22px;height:22px;border-radius:50%;background:#FDECEC;color:#DC2626;display:grid;place-items:center;font-weight:700;font-size:13px">!</span>')]))
    body = f'''<div style="height:16px"></div><div class="c row" style="gap:12px;padding:13px 14px"><span class="rb" style="width:50px;height:50px;background:#E3E9F7;color:#3557A8;font-weight:600;font-size:17px">А</span>
<div style="flex:1;line-height:1.3"><b style="font-size:17px">Адміністратор</b><br><span class="mut">Відділ: усі</span></div><span class="chip" style="background:#F2F3F5;border:0;height:36px">Змінити{ic("chevron-down",14)}</span></div>
{grp("Продажі", tile("file-text","blue","Видаткові накладні") + tile("users","purple","Покупці") + tile("square-kanban","gray","Дошка"))}
{grp("Склад", tile("package","orange","Товари") + tile("store","green","Склад","3") + tile("shopping-cart","blue","Закупівлі"))}
{grp("Гроші й аналітика", tile("wallet","green","Оплати") + tile("chart-column-stacked","purple","Статистика") + tile("chart-bar","gray","Звіти"))}
<div class="c" style="padding:2px 16px">{rows}</div>{bar("more")}'''
    return scr(body)


# ======================================================================== 10. Видаткові накладні
def invoices():
    def card(no, d, o, n, s, ent, ec, inv, flag=""):
        doc = lambda i, l, on=True: f'<span class="btn" style="flex:1;height:38px;border-radius:12px;font-size:13px;font-weight:500;{"background:#F2F3F5" if on else "background:#F7F7F8;color:#B5B4AF"}">{ic(i,15)}{l}</span>'
        fl = f'<span class="st" style="--c:#D97706;height:22px">змінилось</span>' if flag else ""
        return f'''<div class="c" style="padding:12px 14px"><div class="row" style="gap:7px"><span style="font:600 13px 'JB',monospace;color:#57564F">{no}</span>{fl}<span class="fa" style="margin-left:auto;font-size:12.5px">{d} · <span style="color:{BLUE}">№{o}</span></span></div>
<div class="row" style="margin:6px 0 2px;justify-content:space-between"><b style="font-size:16.5px">{n}</b><b style="font-size:16.5px">{s} ₴</b></div>
<div class="row" style="gap:6px;font-size:13px" class="mut"><i style="width:8px;height:8px;border-radius:3px;background:{ec}"></i><span class="mut">{ent}</span></div>
<div class="row" style="gap:6px;margin-top:10px">{doc("file-text","Накладна")}{doc("receipt-text","Рахунок",inv)}{doc("shield-check","Гарантія")}</div></div>'''
    body = f'''{head("Накладні", rb("search") + rb("list-filter"), "Жовтень · 214 накладних · 312 840 ₴")}
{tabs([("Усі юрособи", 214, "#1F1F1C", True), ("ФОП Максимчук О. В.", 168, "#2E6BE6", False), ("ФОП Д. О.", 46, "#0E9488", False)])}
{card("РН-0168","29.10",1480,"Бондаренко Олег","1 290","ФОП Максимчук О. В.","#2E6BE6",True)}{card("ДМ-0046","29.10",1476,"Мельник Денис","2 398","ФОП Максимчук Д. О.","#0E9488",False)}
{card("РН-0166","28.10",1466,"Ковальчук Інна","3 147","ФОП Максимчук О. В.","#2E6BE6",True,"x")}{bar("more")}'''
    return scr(body)


# ======================================================================== 11. Покупці
def customers():
    data = [("ТШ", "#E3E9F7", "#3557A8", "Шевченко Тарас", "+380 67 123 45 67", ("VIP", "#B45309"), "4 замовл.", "75%", "ok", "5 840 ₴", ""),
            ("МД", "#EEE8F8", "#6A4BA8", "Мельник Денис", "+380 63 118 90 05", ("Повторний", "#2E6BE6"), "9 замовл.", "89%", "ok", "21 450 ₴", ""),
            ("ОС", "#FDECEC", "#DC2626", "Олійник Світлана", "+380 68 905 12 44", ("Новий", "#7C7B76"), "2 замовл.", "0%", "bd", "0 ₴", "bl"),
            ("ІК", "#E5F2E9", "#2D7046", "Коваленко Ірина", "+380 93 552 10 08", ("Новий", "#7C7B76"), "1 замовл.", "—", "fa", "649 ₴", "")]
    cards = "".join(f'''<div class="c row" style="gap:12px;padding:13px 14px;align-items:flex-start"><span class="rb" style="width:46px;height:46px;background:{bg};color:{fg};font-weight:600">{i}</span><div style="flex:1;min-width:0;line-height:1.3">
<div class="row" style="justify-content:space-between"><b style="font-size:16px">{n}</b><b style="font-size:15px">{s}</b></div><small class="mut">{p}</small>
<div class="row" style="gap:6px;margin-top:6px;font-size:12.5px">{"" if bl else f'<span class="st" style="--c:{gc};height:21px;font-size:11.5px">{g}</span>'}{'<span class="st" style="--c:#DC2626;height:21px;font-size:11.5px">чорний список</span>' if bl else ""}<span class="mut">{o} · викуп <b class="{bc}">{b}</b></span></div></div></div>'''
                    for i, bg, fg, n, p, (g, gc), o, b, bc, s, bl in data)
    body = f'''{head("Покупці", rb("search") + rb("plus","p"), "3 412 покупців · 28 нових за тиждень")}
{tabs([("Усі", 3412, "#1F1F1C", True), ("VIP", 42, "#D97706", False), ("Повторні", 920, "#2E6BE6", False), ("Чорний список", 14, "#DC2626", False)])}
{cards}{bar("more")}'''
    return scr(body)


# ======================================================================== 12. Картка покупця
def customer_card():
    hist = "".join(f'<div class="row" style="padding:9px 0;{"border-top:1px solid #F0F0EE" if k else ""}"><span style="font:600 12.5px \'JB\',monospace;color:{BLUE};width:44px">{n}</span><span style="flex:1;font-size:13.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{g}</span>{st(s)}</div>'
                   for k, (n, g, s) in enumerate([(1476, "Смарт-годинник Fit 3", "wait"), (1431, "Павербанк Volt", "done"), (1302, "Навушники TWS Pro", "ref")]))
    msg = "".join(f'<span class="btn" style="flex:1;height:44px;border-radius:14px;background:{BLUE if k == 0 else "#F2F3F5"};color:{"#fff" if k == 0 else "#3D3C38"}">{ic(i,18)}</span>' for k, i in enumerate(["phone", "message-circle", "send", "message-square"]))
    tiles = "".join(f'<div style="background:#F6F7F8;border-radius:14px;padding:9px 10px"><b style="font-size:17px">{v}</b><br><small class="mut">{l}</small></div>' for v, l in [("9", "замовлень"), ("89%", "викуп"), ("1", "відмова"), ("21,4к", "сума, ₴")])
    body = f'''<div class="hd" style="padding-bottom:10px">{rb("chevron-left")}<div style="flex:1;text-align:center"><b style="font-size:16.5px">Покупець</b></div>{rb("ellipsis")}</div>
<div class="c"><div class="row" style="gap:12px"><span class="rb" style="width:54px;height:54px;background:#EEE8F8;color:#6A4BA8;font-weight:600;font-size:18px">МД</span><div style="flex:1;line-height:1.3"><b style="font-size:19px">Мельник Денис</b><br><span class="mut">+380 63 118 90 05</span></div><span class="st" style="--c:#D97706">VIP</span></div>
<div class="row" style="gap:8px;margin:12px 0">{msg}</div><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px">{tiles}</div></div>
<div class="c"><h3>{sq("receipt-text","blue",True,15)}Замовлення<small>9</small><span class="r">Усі</span></h3>{hist}</div>
<div class="c"><h3>{sq("map-pin","green",True,15)}Адреси й нотатки</h3><div class="row" style="font-size:14px"><span class="np">НП</span><span style="flex:1">Тульчин, відділення №1</span><small class="fa">6 разів</small></div>
<div class="sep"></div><div class="mut" style="font-size:13.5px">«Дзвонити після 18:00. Любить подарункове пакування.»</div></div>
<div class="sticky"><span class="btn" style="width:54px;flex:none;color:#DC2626">{ic("lock-open",19)}</span><span class="btn p" style="flex:1">{ic("plus",19)}Нове замовлення</span></div>'''
    return scr(body)


# ======================================================================== 13. Склад
def stock():
    rows = [("Бездротовий мікрофон", "Чорний · MIC-01", 3, 1, "через 1 день", "bd", True), ("Кавоварка Delonghi", "ART-001", 12, 2, "через 6 днів", "wr", True),
            ("Екшн-камера 4К", "CAM-4K", 100, 4, "через 41 день", "ok", False), ("Кільцева лампа 26 см", "LAMP-26", 100, 0, "понад рік", "ok", False)]
    rr = "".join(f'''<div style="padding:11px 0;{"border-top:1px solid #F0F0EE" if k else ""}"><div class="row"><div style="flex:1;line-height:1.3"><b style="font-weight:500;font-size:15px">{n}</b><br><small class="mut">{s}</small></div>
<div style="text-align:right;line-height:1.3"><b style="font-size:17px">{a - r}</b><br><small class="fa">доступно</small></div></div>
<div class="row" style="margin-top:7px;gap:8px"><span class="st" style="--c:{"#DC2626" if c == "bd" else "#D97706" if c == "wr" else "#16A34A"};height:22px">{ic("clock",12)}{f}</span><small class="fa">резерв {r}</small>{f'<span class="chip" style="margin-left:auto;height:30px;font-size:12.5px;background:{BLUE2};border:0;color:{BLUE}">Закупити</span>' if buy else ""}</div></div>'''
                 for k, (n, s, a, r, f, c, buy) in enumerate(rows))
    tile = lambda icon, t, v, l, warn=False: f'<div class="c" style="margin:0;padding:12px 13px;{"background:#FDF1E3" if warn else ""}">{sq(icon,t,True,15)}<div style="font-size:20px;font-weight:600;margin-top:8px;{"color:#B45309" if warn else ""}">{v}</div><small class="mut">{l}</small></div>'
    body = f'''{head("Склад", rb("scan-barcode") + rb("package-plus","p"), "Основний склад · оновлено щойно")}
<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:0 14px 10px">{tile("banknote","green","312 400 ₴","вартість залишку")}{tile("lock-open","blue","23 шт","у резерві")}
{tile("circle-alert","orange","12","закінчуються за тиждень",True)}{tile("x","red","5","немає в наявності")}</div>
{tabs([("Усі", 214, "#1F1F1C", True), ("Закінчуються", 12, "#D97706", False), ("Немає", 5, "#DC2626", False), ("Неліквід", 3, "#7C7B76", False)])}
<div class="c" style="padding:2px 16px">{rr}</div>{bar("more")}'''
    return scr(body)


# ======================================================================== 14. Статистика
def stats():
    import random
    random.seed(3)
    cols = ["#16A34A", "#6D5BD0", "#D97706", "#DC2626"]
    bars = ""
    for d in range(14):
        y = 118
        for c, share in zip(cols, (.6, .18, .1, .12)):
            h = (20 + random.randint(0, 34)) * share * 1.4
            y -= h
            bars += f'<rect x="{6 + d * 23}" y="{y:.1f}" width="15" height="{h:.1f}" rx="2" fill="{c}"/>'
    leg = "".join(f'<span class="row" style="gap:5px;font-size:12px"><i style="width:8px;height:8px;border-radius:3px;background:{c}"></i><b style="font-weight:600">{p}</b><span class="mut">{n}</span></span>'
                  for c, p, n in [("#16A34A", "61%", "Завершений"), ("#6D5BD0", "8%", "Відправлений"), ("#D97706", "3%", "Очікує"), ("#DC2626", "13%", "Відмова")])
    tile = lambda l, v, d, dc, s: f'<div class="c" style="margin:0;padding:12px 13px"><div class="row" style="justify-content:space-between"><small class="mut">{l}</small><span class="st" style="--c:{dc};height:20px;font-size:11.5px">{d}</span></div><div style="font-size:20px;font-weight:600;margin:4px 0 2px">{v}</div><small class="fa" style="font-size:11.5px">{s}</small></div>'
    kp = "".join(f'<div style="flex:1;padding:0 6px;{"border-left:1px solid #F0F0EE" if k else ""}"><small class="mut" style="font-size:11.5px">{l}</small><br><b style="font-size:16px">{v}</b> <small class="{c}" style="font-size:11px">{d}</small></div>'
                 for k, (l, v, d, c) in enumerate([("Апрув", "72%", "+3 п.", "ok"), ("Викуп", "78%", "−2 п.", "bd"), ("Підтв.", "14 хв", "−4", "ok")]))
    body = f'''{head("Статистика", rb("list-filter","",'<span class="dot"></span>'))}
<div class="row pad" style="gap:6px;margin:-2px 0 10px"><span class="chip">{ic("calendar",13)}Додане{ic("chevron-down",12)}</span><span class="chip">1–29 жовтня{ic("chevron-down",12)}</span><span class="chip on">Instagram{ic("x",12)}</span></div>
<div class="pad" style="margin-bottom:10px"><div class="seg"><span class="on">Авто</span><span>Дні</span><span>Тижні</span><span>Місяці</span></div></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:0 14px 10px">{tile("Замовлення","742","+12%","#16A34A","основні 511 · допродаж 231")}{tile("Сума","1 084 300 ₴","+9%","#16A34A","допродаж 122 600 ₴")}
{tile("Маржа","389 600 ₴","+7%","#16A34A","середня 525 ₴")}{tile("Сер. чек","1 461 ₴","−3%","#DC2626","маржа 525 ₴")}</div>
<div class="c row" style="padding:11px 8px">{kp}</div>
<div class="c"><h3>Статуси по днях<small>лінія — усі</small></h3><svg width="100%" height="122" viewBox="0 0 330 122">{bars}<polyline points="{" ".join(f"{13 + d*23},{44 - d*1.4 + (8 if d % 3 == 1 else 0):.0f}" for d in range(14))}" fill="none" stroke="#1F1F1C" stroke-width="1.5"/></svg>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 14px;margin-top:6px">{leg}</div></div>{bar("more")}'''
    return scr(body)


# ======================================================================== 15. Фільтри (панель знизу)
def filters():
    grp = lambda t, chips: f'<div class="lab" style="margin-top:12px">{t}</div><div style="display:flex;flex-wrap:wrap;gap:6px">{chips}</div>'
    ch = lambda items: "".join(f'<span class="chip {"on" if on else ""}">{n}</span>' for n, on in items)
    stc = "".join(f'<span class="st" style="--c:{c};height:32px;padding:0 12px;font-size:13.5px;{"background:" + c + ";color:#fff" if on else ""}">{ic("check",13,2.6) if on else "<i></i>"}{n}</span>' for n, c, on in
                  [("Несортований", "#7C7B76", True), ("Прийнятий", "#2E6BE6", True), ("Відправлений", "#6D5BD0", False), ("Очікує на пошті", "#D97706", False), ("Завершений", "#16A34A", False)])
    sheet = f'''<div class="sheet"><div class="grab"></div><h2>Фільтри<span class="x rb" style="width:36px;height:36px;background:#ECEDEF">{ic("x",17)}</span></h2>
{grp("Період", ch([("Сьогодні", False), ("Сьогодні й учора", True), ("Тиждень", False), ("Місяць", False), ("Свій…", False)]))}
<div class="lab" style="margin-top:12px">Статус</div><div style="display:flex;flex-wrap:wrap;gap:6px">{stc}</div>
{grp("Менеджер", ch([("Мої", True), ("Олена", False), ("Андрій", False), ("Без менеджера", False)]))}
{grp("Доставка", ch([("Нова Пошта", True), ("Укрпошта", False), ("Самовивіз", False), ("Rozetka", False)]))}
{grp("Оплата", ch([("Післяплата", False), ("Контроль оплати", False), ("Передоплата", False), ("Оплачено", False)]))}
{grp("Джерело", ch([("Instagram", False), ("Лендинг", False), ("Rozetka", False), ("Prom", False)]))}
<div class="row" style="gap:10px;margin-top:18px"><span class="btn" style="flex:1;background:#ECEDEF">Скинути</span><span class="btn p" style="flex:2">Показати 18</span></div></div>'''
    return orders(extra='<div class="dim"></div>' + sheet)


# ======================================================================== 16. Створення ТТН (панель знизу)
def ttn():
    sheet = f'''<div class="sheet"><div class="grab"></div><h2>Нова ТТН<span class="np" style="margin-left:8px">НП</span><span class="x rb" style="width:36px;height:36px;background:#ECEDEF">{ic("x",17)}</span></h2>
<div class="lab">Спосіб доставки</div><div class="seg" style="margin-bottom:10px"><span class="on">Відділення</span><span>Поштомат</span><span>Кур'єр</span></div>
<div class="lab">Місто</div><div class="inp b" style="margin-bottom:8px">{ic("map-pin",17)}<b>Тульчин</b><small class="fa">Вінницька обл.</small></div>
<div class="lab">Відділення</div><div class="inp b" style="margin-bottom:10px;border-color:{BLUE};box-shadow:0 0 0 3px {BLUE2}">{ic("store",17)}<b>Відділення №3 · вул. Шевченка, 12</b></div>
<div class="lab">Хто платить</div><div class="seg" style="margin-bottom:10px"><span class="on">Отримувач</span><span>Відправник</span></div>
<div class="row" style="gap:8px;margin-bottom:10px"><div style="flex:1"><div class="lab">Вага, кг</div><div class="inp b"><b>0,8</b></div></div><div style="flex:1.4"><div class="lab">Розміри, см</div><div class="inp b"><b>30 × 20 × 15</b></div></div></div>
<div class="row" style="background:{BLUE2};border-radius:16px;padding:12px 14px;gap:10px;margin-bottom:12px"><div style="flex:1;line-height:1.3"><small class="mut">Контроль оплати · з оплати</small><br><b style="font-size:16px">2 648 ₴</b></div>
<div style="text-align:right;line-height:1.3"><small class="mut">доставка</small><br><b style="font-size:16px;color:{BLUE}">≈ 85 ₴</b></div></div>
<div class="row" style="gap:16px;font-size:13.5px;margin-bottom:14px"><span class="row" style="gap:7px"><span class="cb on">{ic("check",13,3)}</span>Наклейка</span><span class="row" style="gap:7px"><span class="cb on">{ic("check",13,3)}</span>Реєстр</span><span class="row" style="gap:7px"><span class="cb on">{ic("check",13,3)}</span>SMS</span></div>
<span class="btn p">{ic("truck",19)}Створити ТТН</span></div>'''
    return card_top().replace('<div class="sticky">', '<div class="dim"></div>' + sheet + '<div class="sticky" style="display:none">')


# ======================================================================== 17. Нове замовлення
def new_order():
    step = lambda n, done, t: f'<span style="width:24px;height:24px;border-radius:50%;display:grid;place-items:center;font-size:12px;font-weight:600;{"background:#16A34A;color:#fff" if done else "background:#ECEDEF;color:#57564F"}">{ic("check",13,3) if done else n}</span><b style="font-size:16px">{t}</b>'
    body = f'''<div class="hd" style="padding-bottom:10px">{rb("x")}<div style="flex:1;text-align:center"><b style="font-size:16.5px">Нове замовлення</b></div><span style="width:44px"></span></div>
<div class="c"><div class="row" style="gap:9px;margin-bottom:10px">{step(1,True,"Покупець")}</div><div class="inp" style="background:#F6F7F8;margin-bottom:8px;color:#1F1F1C">Коваленко Олена</div>
<div class="inp" style="background:#F6F7F8;color:#1F1F1C;gap:6px"><span style="width:20px;height:14px;border-radius:3px;background:linear-gradient(#2E6BE6 50%,#F5C518 50%);flex:none"></span><span class="mut">+380</span><b>67 111 22 33</b></div><small class="ok" style="display:block;margin-top:6px;font-size:12.5px">покупець знайдений · 1 замовлення, викуп —</small></div>
<div class="c"><div class="row" style="gap:9px;margin-bottom:10px">{step(2,True,"Товари")}<span style="margin-left:auto;color:{BLUE};font-size:13.5px;font-weight:500">+ Допродаж</span></div>
<div class="row"><span class="thumb">{ic("package",17)}</span><div style="flex:1;line-height:1.3"><b style="font-weight:500">Кавоварка Delonghi</b><br><small class="mut">1 шт · на складі 12</small></div><b>2 499 ₴</b></div>
<div class="inp b" style="margin-top:10px;height:42px">{ic("search",16)}Додати товар або штрихкод</div></div>
<div class="c"><div class="row" style="gap:9px;margin-bottom:10px">{step(3,False,"Оплата")}</div><div class="inp b" style="color:#1F1F1C">{ic("credit-card",17)}Післяплата<span class="cv">{ic("chevron-down",16)}</span></div></div>
<div class="c"><div class="row" style="gap:9px;margin-bottom:10px">{step(4,False,"Доставка")}</div><div class="inp b" style="color:#1F1F1C"><span class="np">НП</span>Нова Пошта · ФОП Максимчук<span class="cv">{ic("chevron-down",16)}</span></div>
<small class="fa" style="display:block;margin-top:6px">Місто й відділення — у вікні ТТН</small></div>
<div class="sticky"><span class="btn s" style="flex:1">{ic("truck",18)}ТТН</span><span class="btn p" style="flex:2">{ic("check",19)}Створити · 2 499 ₴</span></div>'''
    return scr(body)


# ======================================================================== 18. Налаштування
def settings():
    grp = lambda t, rows: f'<div class="mut" style="font-size:13.5px;font-weight:500;margin:2px 20px 6px">{t}</div><div class="c" style="padding:2px 16px">{rows}</div>'
    r = lambda items: "".join(f'<div class="row" style="padding:7px 0;{"border-top:1px solid #F0F0EE" if k else ""}">{sq(i,t,True,15)}<span style="flex:1;font-size:15px">{l}</span>{x or ic("chevron-right",17)}</div>' for k, (i, t, l, x) in enumerate(items))
    body = f'''{head("Налаштування", rb("search"))}
{grp("Робота", r([("inbox","blue","Розділ «Ліди»",'<span class="tgl on"></span>'),("sliders-horizontal","gray","Загальні",""),("list-checks","purple","Статуси",""),("layers","blue","Довідники",""),("key-round","purple","Користувачі","")]))}
{grp("Гроші й доставка", r([("landmark","green","Юрособи",""),("truck","red","Нова Пошта",'<span class="st" style="--c:#16A34A;height:22px">2 ключі</span>'),("receipt","teal","Checkbox",'<span class="st" style="--c:#D97706;height:22px">зміна закрита</span>'),("store","orange","Маркетплейси","")]))}
{grp("Зв'язок і документи", r([("message-square","blue","SMS і Viber",""),("send","blue","Telegram",""),("file-text","gray","Документи","")]))}{bar("more")}'''
    return scr(body)


SCREENS = [("01-home", "1 · Головна", home), ("02-orders", "2 · Замовлення", orders), ("03-card", "3 · Картка замовлення", card_top), ("04-card2", "4 · Картка — прокрутка вниз", card_bottom),
           ("05-new", "5 · Нове замовлення", new_order), ("06-ttn", "6 · Створення ТТН", ttn), ("07-filters", "7 · Фільтри", filters), ("08-leads", "8 · Ліди", leads),
           ("09-lead", "9 · Лід: дзвінок", lead_window), ("10-products", "10 · Товари", products), ("11-product", "11 · Картка товару", product_card), ("12-stock", "12 · Склад", stock),
           ("13-customers", "13 · Покупці", customers), ("14-customer", "14 · Картка покупця", customer_card), ("15-invoices", "15 · Видаткові накладні", invoices),
           ("16-stats", "16 · Статистика", stats), ("17-more", "17 · Ще", more), ("18-settings", "18 · Налаштування", settings)]


def build():
    return page("Мобільна v2 — усі екрани", CSS, [(k, n, f(), 390, 844) for k, n, f in SCREENS], cols=6, gap=36)
