"""Версія для ПК v2 — покращення наявних сторінок у мові мобільної v2: сірий фон, білі картки 18 px без рамок,
кольорові квадрати-іконки, кільця, статус кольором, менше колонок і ліній, панель перегляду праворуч замість одразу вікна."""
from common import *

BLUE = "#2E6BE6"
CSS = """
.d{--ink:#1F1F1C;--mut:#6F6E69;--faint:#A3A29D;--bg:#F1F2F4;--acc:#2E6BE6;--acc2:#EAF1FD;--acc3:#C9DBFA;--ok:#16A34A;--warn:#D97706;--bad:#DC2626;
  width:1440px;height:900px;background:var(--bg);font:400 13.5px/1.4 'Onest',sans-serif;color:var(--ink);display:grid;grid-template-columns:232px 1fr;overflow:hidden;position:relative}
.d b{font-weight:600}
/* бокова панель */
.sb{padding:18px 12px 14px;display:flex;flex-direction:column;gap:12px}
.logo{display:flex;align-items:center;gap:9px;padding:2px 8px}.logo i{width:30px;height:30px;border-radius:10px;background:var(--acc);color:#fff;display:grid;place-items:center;font:600 16px Onest;font-style:normal}
.logo b{font-size:16px}.logo s{margin-left:auto;width:8px;height:8px;border-radius:50%;background:var(--ok);box-shadow:0 0 0 3px #E9F6EE}
.off{display:flex;align-items:center;gap:8px;height:36px;padding:0 12px;border-radius:12px;background:#fff;font-size:13px;color:#3D3C38}.off .cv{margin-left:auto;color:var(--faint)}
.grp{display:flex;flex-direction:column;gap:1px}.gt{font-size:11.5px;color:var(--mut);padding:6px 10px 3px}
.it{display:flex;align-items:center;gap:10px;height:34px;padding:0 10px;border-radius:11px;font-size:13.5px;color:#3D3C38}.it svg{color:#8A8984}
.it.on{background:#fff;color:var(--ink);font-weight:500}.it.on svg{color:var(--acc)}
.it em{margin-left:auto;font-style:normal;font-size:11px;font-weight:600;min-width:20px;height:18px;border-radius:99px;display:grid;place-items:center;padding:0 6px;background:var(--acc);color:#fff}
.it em.n{background:none;color:var(--faint);font-weight:500}
.me{margin-top:auto;display:flex;align-items:center;gap:10px;padding:9px 10px;background:#fff;border-radius:14px}.me .av{width:32px;height:32px;font-size:12px}
.me small{display:block;font-size:11.5px;color:var(--mut)}
/* робоча область */
.mn{padding:16px 24px 0 8px;display:flex;flex-direction:column;min-width:0;min-height:0}
.hd{display:flex;align-items:center;gap:10px;min-height:56px;margin-bottom:12px}
.hd h1{font-size:28px;font-weight:600;letter-spacing:-.02em;line-height:1.1}.hd .sub{font-size:13px;color:var(--mut);margin-top:3px}.hd .sub b{color:var(--ink)}
.hd .sp{flex:1}
.srch{display:flex;align-items:center;gap:8px;height:42px;width:300px;padding:0 14px;border-radius:14px;background:#fff;color:var(--faint);font-size:13.5px}.srch kbd{margin-left:auto;font:500 11px 'JB',monospace;color:var(--mut);background:#F2F3F5;border-radius:6px;padding:2px 6px}
.rb{width:42px;height:42px;border-radius:50%;background:#fff;display:grid;place-items:center;flex:none;position:relative;color:var(--ink)}
.rb .dot{position:absolute;top:9px;right:10px;width:8px;height:8px;border-radius:50%;background:var(--acc);box-shadow:0 0 0 2px #fff}
.rb em{position:absolute;top:-3px;right:-3px;min-width:18px;height:18px;border-radius:99px;background:var(--acc);color:#fff;font:600 10.5px/18px Onest;font-style:normal;text-align:center;padding:0 5px;box-shadow:0 0 0 2px var(--bg)}
.btn{height:42px;padding:0 18px;border-radius:14px;display:inline-flex;align-items:center;justify-content:center;gap:8px;font-weight:600;font-size:14px;background:#fff;color:var(--ink);white-space:nowrap;flex:none}
.btn.p{background:var(--acc);color:#fff;box-shadow:0 8px 18px -8px rgba(46,107,230,.7)}.btn.s{background:var(--acc2);color:var(--acc)}.btn.g{background:#F2F3F5}
.btn.sm{height:34px;padding:0 12px;border-radius:11px;font-size:13px;font-weight:500}
.c{background:#fff;border-radius:18px;padding:16px 18px;min-width:0}
.c h3{display:flex;align-items:center;gap:9px;font-size:15.5px;font-weight:600;margin-bottom:10px}.c h3 small{font-weight:400;color:var(--faint);font-size:12.5px}.c h3 .r{margin-left:auto;font-size:13px;font-weight:500;color:var(--acc)}
.sq{width:34px;height:34px;border-radius:11px;display:grid;place-items:center;flex:none;background:var(--s,#EAF1FD);color:var(--i,#2E6BE6)}.sq.sm{width:28px;height:28px;border-radius:9px}
.st{display:inline-flex;align-items:center;gap:5px;height:22px;padding:0 9px;border-radius:99px;font-size:12px;font-weight:500;white-space:nowrap;
  background:color-mix(in srgb,var(--c) 12%,white);color:color-mix(in srgb,var(--c) 75%,black)}.st i{width:6px;height:6px;border-radius:50%;background:var(--c)}
.np{background:#E5262B;color:#fff;border-radius:6px;font:700 10px/1 Onest;padding:4px 5px;flex:none}
.th{width:36px;height:36px;border-radius:10px;background:#ECEDEF;display:grid;place-items:center;color:#9C9C98;flex:none}.th.l{width:52px;height:52px;border-radius:14px}
.av{width:40px;height:40px;border-radius:50%;display:grid;place-items:center;flex:none;font-weight:600;background:#E3E9F7;color:#3557A8}.av.l{width:52px;height:52px;font-size:17px}
.mut{color:var(--mut)}.fa{color:var(--faint)}.ok{color:var(--ok)}.wr{color:var(--warn)}.bd{color:var(--bad)}.ac{color:var(--acc)}
.row{display:flex;align-items:center;gap:10px;min-width:0}.col{display:flex;flex-direction:column;min-width:0}
.ell{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}
.sep{height:1px;background:#EFEFED;margin:10px 0}
.kv{display:flex;justify-content:space-between;gap:12px;padding:3px 0;font-size:13.5px}.kv span{color:var(--mut)}
.chip{height:32px;padding:0 12px;border-radius:99px;display:inline-flex;align-items:center;gap:6px;font-size:13px;font-weight:500;background:#fff;color:var(--ink);white-space:nowrap;flex:none}
.chip.on{background:var(--acc2);color:#1F4FB8}.chip.dash{background:none;border:1px dashed #CFCEC9;color:var(--mut)}
.tabs{display:flex;gap:6px;align-items:center}
.tab{height:34px;padding:0 14px;border-radius:99px;display:inline-flex;align-items:center;gap:6px;font-size:13.5px;font-weight:500;white-space:nowrap;flex:none;
  background:color-mix(in srgb,var(--c,#7C7B76) 12%,white);color:color-mix(in srgb,var(--c,#7C7B76) 72%,black)}
.tab em{font-style:normal;opacity:.6;font-weight:500}.tab.on{background:var(--c,#1F1F1C);color:#fff}.tab.on em{opacity:.8}
.tab em.h{opacity:1;background:var(--acc);color:#fff;border-radius:99px;min-width:18px;height:18px;display:inline-grid;place-items:center;font-size:11px;padding:0 5px}
.seg{display:inline-flex;background:#E6E7EA;border-radius:13px;padding:3px;gap:2px}.seg span{height:34px;padding:0 14px;border-radius:10px;display:inline-flex;align-items:center;gap:6px;font-size:13px;font-weight:500;color:var(--mut)}
.seg span.on{background:#fff;color:var(--ink);box-shadow:0 1px 2px rgba(0,0,0,.06)}
.ring{position:relative;display:grid;place-items:center;text-align:center;font-weight:600;line-height:1.05;flex:none}.ring svg{position:absolute;inset:0}.ring small{display:block;font-size:10px;font-weight:500}
.tgl{width:42px;height:26px;border-radius:99px;background:#D9D8D3;position:relative;flex:none}.tgl::after{content:"";position:absolute;left:3px;top:3px;width:20px;height:20px;border-radius:50%;background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.2)}
.tgl.on{background:var(--acc)}.tgl.on::after{left:19px}
.inp{height:40px;border-radius:12px;background:#F6F7F8;display:flex;align-items:center;gap:8px;padding:0 12px;font-size:13.5px;color:var(--ink)}.inp.e{color:var(--faint)}
.lab{font-size:12px;color:var(--mut);margin:0 0 5px 2px}
.msg{display:flex;gap:6px}.msg span{flex:1;height:38px;border-radius:12px;background:#F2F3F5;display:grid;place-items:center;color:#3D3C38}.msg span.p{background:var(--acc);color:#fff}
/* таблиця-список: два рядки в клітинці, без вертикальних ліній */
.tb{background:#fff;border-radius:18px;overflow:hidden}
.tr{display:grid;align-items:center;column-gap:12px;padding:0 16px;min-height:56px;border-top:1px solid #F2F2F0;font-size:13.5px}
.tr.h{min-height:40px;border-top:0;font-size:12px;color:var(--mut)}.tr.sel{background:#F5F9FF;box-shadow:inset 3px 0 0 var(--acc)}
.tr .two{display:flex;flex-direction:column;line-height:1.3;min-width:0}.tr .two small{color:var(--mut);font-size:12px}
.cb{width:18px;height:18px;border-radius:6px;border:1.5px solid #CFCEC9;background:#fff;display:grid;place-items:center}.cb.on{background:var(--acc);border-color:var(--acc);color:#fff}
.num{font-variant-numeric:tabular-nums}
.bar{height:6px;border-radius:99px;background:#EFEFED;overflow:hidden}.bar i{display:block;height:100%;border-radius:99px}
.note{position:absolute;left:252px;bottom:14px;background:#1F1F1C;color:#fff;font-size:12.5px;border-radius:12px;padding:8px 12px;opacity:.9}
"""

SC = {"uns": ("Несортований", "#7C7B76"), "acc": ("Прийнятий", "#2E6BE6"), "sent": ("Відправлений", "#6D5BD0"), "wait": ("Очікує на пошті", "#D97706"),
      "done": ("Завершений", "#16A34A"), "ref": ("Відмова", "#DC2626"), "new": ("Новий", "#2E6BE6"), "no": ("Недодзвон", "#D97706"), "cb": ("Передзвонити", "#7C3AED")}
TINT = {"blue": ("#EAF1FD", "#2E6BE6"), "green": ("#E9F6EE", "#16A34A"), "orange": ("#FDF1E3", "#D97706"), "purple": ("#F1ECFB", "#7C3AED"),
        "red": ("#FDECEC", "#DC2626"), "gray": ("#F0F0EE", "#57564F"), "teal": ("#E6F6F4", "#0E9488")}


def st(k):
    n, c = SC[k]
    return f'<span class="st" style="--c:{c}"><i></i>{n}</span>'


def sq(icon, t="blue", sm=False, size=16):
    s, i = TINT[t]
    return f'<span class="sq{" sm" if sm else ""}" style="--s:{s};--i:{i}">{ic(icon, size)}</span>'


def ring(v, unit, frac, color, size=52, sw=4.5, fs=13):
    r = size / 2 - sw
    L = 2 * 3.14159 * r
    return (f'<span class="ring" style="width:{size}px;height:{size}px;color:{color};font-size:{fs}px"><svg width="{size}" height="{size}">'
            f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="#EEEEEA" stroke-width="{sw}"/>'
            f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-dasharray="{L*frac:.1f} {L:.1f}" transform="rotate(-90 {size/2} {size/2})"/></svg>'
            f'<span>{v}{f"<small>{unit}</small>" if unit else ""}</span></span>')


NAV = [("Продажі", [("home", "house", "Головна", ""), ("leads", "inbox", "Ліди", "4"), ("orders", "receipt-text", "Замовлення", "16"), ("inv", "file-text", "Видаткові накладні", ""),
                    ("board", "square-kanban", "Дошка", ""), ("cust", "contact", "Покупці", "")]),
       ("Склад", [("prod", "package", "Товари", "n13"), ("stock", "boxes", "Склад", ""), ("buy", "shopping-cart", "Закупівлі", "")]),
       ("Гроші й аналітика", [("pay", "wallet", "Оплати", ""), ("stats", "chart-column-stacked", "Статистика", ""), ("rep", "chart-bar", "Звіти", "")]),
       ("Керування", [("audit", "clock-fading", "Журнал дій", ""), ("set", "settings", "Налаштування", ""), ("sys", "activity", "Система", "")])]


def sidebar(active):
    g = ""
    for t, items in NAV:
        rows = "".join(f'<div class="it{" on" if k == active else ""}">{ic(i, 17)}{n}{f"<em class={chr(34)}n{chr(34)}>{c[1:]}</em>" if c.startswith("n") else f"<em>{c}</em>" if c else ""}</div>'
                       for k, i, n, c in items)
        g += f'<div class="grp"><div class="gt">{t}</div>{rows}</div>'
    return f'''<aside class="sb"><div class="logo"><i>m</i><b>mdmy</b><s></s></div><div class="off">{ic("building",15)}Відділ: усі<span class="cv">{ic("chevron-down",14)}</span></div>
{g}<div class="me"><span class="av">ОЛ</span><div><b style="font-weight:500">Олена Литвин</b><small>Менеджер</small></div></div></aside>'''


def frame(active, body, extra=""):
    return f'<div class="d">{sidebar(active)}<main class="mn">{body}</main>{extra}</div>'


def head(title, sub="", right=""):
    return f'<div class="hd"><div><h1>{title}</h1>{f"<div class=sub>{sub}</div>" if sub else ""}</div><span class="sp"></span>{right}</div>'


SEARCH = f'<span class="srch">{ic("search",16)}Пошук по CRM<kbd>Ctrl K</kbd></span>'
BELL = f'<span class="rb">{ic("bell",19)}<em>2</em></span>'


# ============================================================ 1. Головна
def home():
    pills = "".join(f'<div class="c row" style="padding:10px 14px;gap:10px;border-radius:16px">{sq(i,t,True,15)}<div class="col" style="line-height:1.15"><b style="font-size:17px">{n}</b><small class="mut" style="font-size:12px">{l}</small></div>{ic("chevron-right",15)}</div>'
                    for i, t, n, l in [("inbox", "red", "4", "нові ліди"), ("clock", "orange", "16", "несортовані"), ("package", "blue", "3", "до відправки"),
                                       ("map-pin", "purple", "5", "на пошті"), ("bell", "red", "2", "нагадування"), ("boxes", "gray", "1", "закінчується")])
    bars = [42, 55, 30, 48, 22, 18, 61, 37, 50, 44, 26, 20, 58, 74]
    bh = "".join(f'<div class="col" style="align-items:center;gap:6px;flex:1"><span style="width:100%;height:{h}px;border-radius:6px;background:{"#5B8EF0" if k == 13 else "#3A3A3F"}"></span><small style="font-size:10px;color:#8D8D92">{17 + k if 17 + k <= 31 else k - 14}</small></div>' for k, h in enumerate(bars))
    tile = lambda icon, t, d, dc, v, l: f'''<div class="c" style="padding:14px 16px"><div class="row" style="justify-content:space-between">{sq(icon,t,True,15)}<span class="st" style="--c:{dc}">{d}</span></div>
<div style="font-size:24px;font-weight:600;letter-spacing:-.02em;margin-top:10px">{v}</div><div class="mut" style="font-size:12.5px">{l}</div></div>'''
    pts = [(0, 40), (1, 30), (2, 52), (3, 24), (4, 34), (5, 14), (6, 46), (7, 36), (8, 20), (9, 41), (10, 8), (11, 28), (12, 18), (13, 2)]
    days = "".join(f'<rect x="{18 + k*50}" y="{170 - h}" width="30" height="{h}" rx="5" fill="{"#2E6BE6" if k == 13 else "#C9DBFA"}"/>' for k, h in enumerate([84, 115, 62, 98, 48, 39, 129, 78, 106, 92, 56, 42, 123, 154]))
    prev = " ".join(f"{33 + x*50},{y + 60}" for x, y in pts)
    top = "".join(f'<div class="row" style="padding:8px 0;{"border-top:1px solid #F0F0EE" if k else ""}"><span class="th">{ic("package",15)}</span><div class="col" style="flex:1;line-height:1.25"><span class="ell" style="font-weight:500">{n}</span><small class="mut">{q} шт</small></div><div class="bar" style="width:70px"><i style="width:{w}%;background:#C9DBFA"></i></div><b class="num" style="width:84px;text-align:right">{s} ₴</b></div>'
                  for k, (n, q, s, w) in enumerate([("Павербанк Volt 20 000", 142, "227 058", 100), ("Чохол MagSafe", 118, "52 982", 83), ("Бездротовий мікрофон", 64, "121 536", 45), ("Кільцева лампа 26 см", 51, "45 849", 36), ("Екшн-камера 4К", 22, "120 978", 15), ("Штатив-монопод", 19, "53 143", 13)]))
    body = f'''<div class="hd"><span class="av l" style="margin-right:4px">ОЛ</span><div><div class="sub" style="margin:0 0 2px">Пʼятниця, 30 жовтня</div><h1 style="font-size:26px">Привіт, Олено</h1></div><span class="sp"></span>
<span class="seg"><span class="on">Жовтень</span><span>Вересень</span><span>{ic("calendar",14)}Свій період</span></span>{SEARCH}{BELL}</div>
<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:12px">{pills}</div>
<div style="display:grid;grid-template-columns:440px 1fr 1fr;grid-template-rows:auto auto;gap:12px">
<div style="grid-row:span 2;background:#1E1E22;border-radius:20px;padding:18px 20px;color:#fff;display:flex;flex-direction:column">
<div class="row" style="justify-content:space-between"><span style="color:#B7B7BC;font-size:13px">Продано сьогодні · 5 замовлень</span><span class="st" style="--c:#16A34A;background:#1E3A2A;color:#4ADE80">{ic("arrow-up-right",12)}11% до вчора</span></div>
<div style="font-size:46px;font-weight:600;letter-spacing:-.03em;line-height:1.1;margin:8px 0 2px">18 896 <span style="font-size:26px;color:#9E9EA3">₴</span></div>
<div style="color:#9E9EA3;font-size:12.5px">учора 17 020 ₴ · сер. чек 3 779 ₴</div><span style="flex:1"></span>
<div style="display:flex;align-items:flex-end;gap:6px;height:100px">{bh}</div></div>
{tile("calendar","blue","+9%","#16A34A","130 020 ₴","за жовтень · 39 замовлень")}{tile("wallet","green","+4%","#16A34A","3 334 ₴","середній чек")}
<div class="c row" style="gap:14px;padding:14px 16px">{ring("72%","",.72,"#2E6BE6",58,5,14)}<div class="col"><b style="font-size:15px">Апрув</b><span class="st" style="--c:#16A34A;margin-top:4px;width:max-content">+3 п.</span><small class="mut" style="margin-top:4px">28 з 39 підтверджено</small></div></div>
<div class="c row" style="gap:14px;padding:14px 16px">{ring("78%","",.78,"#16A34A",58,5,14)}<div class="col"><b style="font-size:15px">Викуп</b><span class="st" style="--c:#DC2626;margin-top:4px;width:max-content">−2 п.</span><small class="mut" style="margin-top:4px">21 отримано · 6 відмов</small></div></div>
</div>
<div style="display:grid;grid-template-columns:1fr 420px;gap:12px;margin-top:12px;flex:1;min-height:0;padding-bottom:16px">
<div class="c"><h3>Продажі по днях<small>пунктир — вересень</small><span class="r" style="color:var(--mut);font-weight:400">сума, ₴</span></h3>
<div class="row" style="gap:28px;margin-bottom:4px">{"".join(f'<div class="col"><small class="mut">{l}</small><b style="font-size:19px">{v}</b></div>' for l, v in [("Жовтень", "130 020 ₴"), ("Вересень", "119 400 ₴"), ("Найкращий день", "30.10 · 18 896 ₴"), ("Середнє за день", "4 334 ₴")])}</div>
<svg width="100%" height="300" viewBox="0 0 720 190" preserveAspectRatio="none"><line x1="0" x2="720" y1="170" y2="170" stroke="#EFEFED"/><line x1="0" x2="720" y1="110" y2="110" stroke="#F4F4F2"/><line x1="0" x2="720" y1="50" y2="50" stroke="#F4F4F2"/>
{days}<polyline points="{prev}" fill="none" stroke="#7C7B76" stroke-width="1.6" stroke-dasharray="4 4"/></svg></div>
<div class="c"><h3>Топ товарів<small>жовтень</small><span class="r">Статистика →</span></h3>{top}</div></div>'''
    return frame("home", body)


# ============================================================ 2. Замовлення + панель перегляду
ORD = [("uns", "44", "17:10", "Олена Коваль", "+380 67 111 22 33", "Бездротовий мікрофон", "", "НП", "Київ, №12", "1 899", True, "warn"),
       ("uns", "43", "17:00", "Андрій Мельник", "+380 93 455 10 07", "Набір капсул 50 шт", "+1", "", "без доставки", "2 000", False, "cmt"),
       ("acc", "42", "16:37", "Микола Бондаренко", "+380 50 224 18 90", "Радіосистема DJI Mic 2", "", "НП", "Львів, №5", "3 899", False, ""),
       ("acc", "41", "15:58", "Ірина Савчук", "+380 97 300 44 21", "Кільцева лампа 26 см", "+2", "НП", "Вінниця, №2", "1 297", False, ""),
       ("sent", "40", "15:50", "Тарас Ткаченко", "+380 66 811 03 52", "Екшн-камера 4К", "", "НП", "Одеса, №31", "5 499", False, ""),
       ("sent", "39", "14:12", "Світлана Олійник", "+380 68 905 12 44", "Штатив-монопод", "", "Укрпошта", "Тульчин", "2 797", False, "bl"),
       ("wait", "38", "учора", "Денис Мельник", "+380 63 118 90 05", "Смарт-годинник Fit 3", "", "НП", "Тульчин, №1", "2 398", False, ""),
       ("done", "37", "учора", "Олег Бондаренко", "+380 99 220 41 77", "Павербанк Volt 20 000", "+1", "НП", "Харків, №44", "1 999", False, ""),
       ("done", "36", "28.10", "Інна Ковальчук", "+380 95 664 82 10", "Навушники TWS Pro", "", "НП", "Дніпро, №9", "1 649", False, ""),
       ("ref", "35", "28.10", "Віктор Поліщук", "+380 67 801 55 12", "Чохол MagSafe", "", "НП", "Київ, №120", "449", False, "")]
GRID = "18px 58px minmax(140px,1.2fr) minmax(120px,1.1fr) 124px 118px 74px"


def order_rows(sel="44"):
    out = f'<div class="tr h" style="grid-template-columns:{GRID}"><span class="cb"></span><span>№ · коли</span><span>Покупець</span><span>Товар</span><span>Статус</span><span>Доставка</span><span style="text-align:right">Сума</span></div>'
    for s, no, t, n, ph, g, more, dl, city, sm, warn, flag in ORD:
        fl = (f' <span style="color:var(--warn)">{ic("circle-alert",13)}</span>' if flag == "warn" else
              f' <span style="color:var(--acc)">{ic("message-square",13)}</span>' if flag == "cmt" else
              ' <span class="st" style="--c:#DC2626;height:18px;font-size:10.5px">ЧС</span>' if flag == "bl" else "")
        dlv = f'<span class="np">НП</span><span class="ell mut">{city}</span>' if dl == "НП" else f'<span class="ell mut">{dl + " · " if dl else ""}{city}</span>'
        out += f'''<div class="tr{" sel" if no == sel else ""}" style="grid-template-columns:{GRID}"><span class="cb{" on" if no == sel else ""}">{ic("check",12,3) if no == sel else ""}</span>
<span class="two"><b class="num" style="font:600 12.5px 'JB',monospace">№{no}</b><small>{t}</small></span>
<span class="two"><span class="ell" style="font-weight:500">{n}{fl}</span><small class="num">{ph}</small></span>
<span class="row" style="gap:9px"><span class="th" style="width:30px;height:30px;border-radius:9px">{ic("package",13)}</span><span class="ell">{g}</span>{f'<span class="fa" style="flex:none">{more}</span>' if more else ""}</span>
<span>{st(s)}</span><span class="row" style="gap:7px">{dlv}</span><b class="num" style="text-align:right">{sm} ₴</b></div>'''
    return out


def orders():
    tabs = "".join(f'<span class="tab{" on" if on else ""}" style="--c:{c}">{n} <em{" class=h" if h else ""}>{k}</em></span>' for n, k, c, on, h in
                   [("Несортовані", 16, "#7C7B76", False, True), ("Прийняті", 3, "#2E6BE6", False, False), ("Відправлені", 13, "#6D5BD0", False, False),
                    ("Очікує на пошті", 5, "#D97706", False, False), ("Завершені", 68, "#16A34A", False, False), ("Відмова", 7, "#DC2626", False, False), ("Усі", 126, "#1F1F1C", True, False)])
    panel = f'''<aside class="c" style="width:372px;flex:none;display:flex;flex-direction:column;padding:16px 18px;gap:12px">
<div class="row"><b style="font:600 13px 'JB',monospace">№44</b><span class="mut" style="font-size:12.5px">сьогодні 17:10 · лендинг</span><span class="sp" style="flex:1"></span><span class="rb" style="width:34px;height:34px;background:#F2F3F5">{ic("arrow-up-right",16)}</span><span class="rb" style="width:34px;height:34px;background:#F2F3F5">{ic("x",16)}</span></div>
<div class="row"><span class="av l">ОК</span><div class="col" style="flex:1"><b style="font-size:17px">Олена Коваль</b><span class="mut num">+380 67 111 22 33</span></div><div class="col" style="align-items:flex-end"><b style="font-size:19px">1 899 ₴</b><small class="mut">післяплата</small></div></div>
<div class="msg"><span class="p">{ic("phone",17)}</span><span>{ic("message-circle",17)}</span><span>{ic("send",17)}</span><span>{ic("message-square",17)}</span></div>
<div style="height:44px;border-radius:14px;background:#7C7B76;color:#fff;display:flex;align-items:center;gap:10px;padding:0 14px"><i style="width:8px;height:8px;border-radius:50%;background:#fff"></i><b>Несортований</b><span style="margin-left:auto;font-size:12.5px;opacity:.85" class="row">змінити{ic("chevron-down",14)}</span></div>
<div style="background:#FDF1E3;border-radius:12px;padding:8px 12px;font-size:12.5px;color:#A85A04" class="row">{ic("circle-alert",14)}Можливий дубль №31 — той самий номер і товар</div>
<div><div class="lab">Товари</div><div class="row"><span class="th">{ic("package",15)}</span><div class="col" style="flex:1"><span style="font-weight:500">Бездротовий мікрофон</span><small class="mut">1 шт · на складі 3</small></div><b>1 899 ₴</b></div></div>
<div class="sep" style="margin:0"></div>
<div class="kv"><span>Оплата</span><b style="font-weight:500">Післяплата · контроль оплати</b></div>
<div class="kv"><span>Доставка</span><span class="row" style="gap:6px;font-weight:500"><span class="np">НП</span>Київ, відділення №12</span></div>
<div class="kv"><span>Менеджер</span><b style="font-weight:500">не призначено</b></div>
<div class="row" style="background:#F6F7F8;border-radius:14px;padding:10px 12px;gap:12px">{ring("1/4","",.25,"#16A34A",42,4,11)}<div class="col"><b>Що лишилось</b><small class="mut">прийняти · ТТН · оплата</small></div></div>
<span style="flex:1"></span>
<div class="row" style="gap:8px"><span class="btn g" style="flex:1">Відкрити картку</span><span class="btn p" style="flex:1.4">{ic("check",17)}Прийняти</span></div></aside>'''
    body = f'''{head("Замовлення", "<b>16</b> несортованих · <b>3</b> чекають відправки · <b>13</b> у дорозі",
        f'<span class="srch" style="width:260px">{ic("search",16)}Пошук у списку<kbd>/</kbd></span><span class="rb">{ic("list-filter",19)}<span class="dot"></span></span><span class="seg"><span class="on">{ic("list",14)}Стрічка</span><span>{ic("square-kanban",14)}Дошка</span></span><span class="btn p">{ic("plus",17)}Замовлення</span>')}
<div class="row" style="justify-content:space-between;margin-bottom:12px"><div class="tabs">{tabs}</div>
<div class="row" style="gap:6px"><span class="chip on">{ic("calendar",13)}Сьогодні й учора{ic("x",12)}</span><span class="chip on">Нова Пошта{ic("x",12)}</span></div></div>
<div class="row" style="align-items:stretch;gap:12px;flex:1;min-height:0;padding-bottom:16px"><div class="tb" style="flex:1">{order_rows()}</div>{panel}</div>'''
    return frame("orders", body)


# ============================================================ 3. Картка замовлення
def card():
    track = "".join(f'{"<i style=\'width:12px;height:1px;background:#D6D6D3;flex:none\'></i>" if k else ""}<span class="chip" style="height:32px;padding:0 11px;font-size:12.5px;{st_}">{ic("check",13,2.6) if k < 2 else ""}{n}</span>'
                    for k, (n, st_) in enumerate([("Несортований", "background:#F0F0EE;color:var(--mut)"), ("Прийнятий", "background:#2E6BE6;color:#fff"), ("Відправлений", "background:#F6F7F8"), ("На пошті", "background:#F6F7F8"), ("Завершений", "background:#F6F7F8")]))
    offers = "".join(f'<div style="flex:1;background:#F6F7F8;border-radius:14px;padding:8px" class="row"><span class="th" style="background:#fff">{ic("package",14)}</span><div class="col" style="flex:1;line-height:1.25"><span class="ell" style="font-size:12.5px;font-weight:500">{n}</span><b style="font-size:12.5px">{p} ₴</b></div><span class="sq sm" style="--s:#2E6BE6;--i:#fff;border-radius:50%;width:26px;height:26px">{ic("plus",14,2.4)}</span></div>'
                     for n, p in [("Адаптер USB-C", "349"), ("Карта пам'яті 64 ГБ", "399"), ("Чохол для мікрофона", "299")])
    todo = "".join(f'<div class="row" style="padding:5px 0"><span class="cb{" on" if d else ""}" style="border-radius:50%">{ic("check",11,3) if d else ""}</span><span style="flex:1;{"color:var(--faint);text-decoration:line-through" if d else ""}">{t}</span>{f"<span class=ac style=font-size:12.5px>{a}</span>" if a and not d else ""}</div>'
                   for t, d, a in [("Прийняти замовлення", True, ""), ("Товар зарезервовано", True, ""), ("Створити ТТН", False, "Створити"), ("Чек передоплати", False, "Пробити"), ("Видаткова накладна", False, "Видати")])
    hist = "".join(f'<div class="row" style="align-items:flex-start;padding:6px 0;gap:10px">{sq(i,t,True,13)}<div class="col" style="flex:1;line-height:1.3"><span>{a}</span><small class="fa">{w}</small></div></div>'
                   for i, t, a, w in [("check", "blue", "Статус «Прийнятий» · Олена", "сьогодні 17:22"), ("landmark", "green", "Передоплата 200 ₴ надійшла", "сьогодні 14:50")])
    win = f'''<div style="position:absolute;inset:0;background:rgba(24,24,22,.36)"></div>
<div style="position:absolute;left:24px;right:24px;top:20px;bottom:20px;background:var(--bg);border-radius:22px;display:flex;flex-direction:column;overflow:hidden">
<div class="row" style="padding:14px 18px;gap:12px;background:#fff"><span class="rb" style="background:#F2F3F5">{ic("chevron-left",19)}</span><div class="col" style="flex:none;white-space:nowrap"><b style="font-size:17px">Замовлення №27</b><small class="mut">30.10, 13:50 · лендинг</small></div>
<div class="row" style="margin-left:14px;gap:2px;flex:none">{track}<span class="chip" style="margin-left:6px;height:34px;background:#F2F3F5">{ic("ellipsis",15)}</span></div><span style="flex:1"></span>
<span class="ok" title="Збережено">{ic("circle-check-big",18)}</span><span class="rb" style="background:#F2F3F5">{ic("printer",18)}</span><span class="rb" style="background:#F2F3F5">{ic("receipt",18)}</span><span class="rb" style="background:#F2F3F5">{ic("bell",18)}</span><span class="rb" style="background:#F2F3F5">{ic("clock-fading",18)}<em>6</em></span>
<span class="btn p">{ic("truck",17)}Створити ТТН</span></div>
<div style="display:grid;grid-template-columns:350px 1fr 330px;gap:12px;padding:12px;flex:1;min-height:0">
<div class="col" style="gap:12px">
<div class="c"><div class="row"><span class="av l">ОК</span><div class="col" style="flex:1"><b style="font-size:17px">Коваленко Олена</b><span class="mut num">+380 67 111 22 33</span></div><span class="rb" style="width:32px;height:32px;background:#F2F3F5">{ic("pencil",14)}</span></div>
<div class="msg" style="margin:12px 0"><span class="p">{ic("phone",17)}</span><span>{ic("message-circle",17)}</span><span>{ic("send",17)}</span><span>{ic("message-square",17)}</span></div>
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px">{"".join(f'<div style="background:#F6F7F8;border-radius:12px;padding:8px 9px;line-height:1.2"><b style="font-size:15px">{v}</b><br><small class="mut" style="font-size:11px">{l}</small></div>' for v, l in [("4", "замовл."), ("75%", "викуп"), ("1", "відмова"), ("5,8к", "сума ₴")])}</div>
<div class="sep"></div><div class="kv"><span>Юрособа</span><b style="font-weight:500">ФОП Максимчук О. В.</b></div><div class="kv"><span>Email</span><span class="ac">+ додати</span></div></div>
<div class="c"><h3>{sq("list","gray",True,14)}Деталі</h3><div class="kv"><span>Джерело</span><b style="font-weight:500">Лендинг</b></div><div class="kv"><span>Менеджер</span><b style="font-weight:500">Олена Литвин</b></div>
<div class="lab" style="margin-top:8px">Коментар</div><div class="inp" style="height:56px;align-items:flex-start;padding-top:9px">Дзвонити після 18:00</div>
<div class="row" style="gap:14px;margin-top:10px;font-size:13px"><span class="ac row" style="gap:3px">Поля 1–4{ic("chevron-down",13)}</span><span class="ac row" style="gap:3px">UTM і сайт{ic("chevron-down",13)}</span></div></div>
<div class="c" style="flex:1"><h3>{sq("receipt-text","blue",True,14)}Інші замовлення<small>3</small><span class="r">+ Нове</span></h3>
{"".join(f'<div class="row" style="padding:7px 0;{"border-top:1px solid #F0F0EE" if k else ""}"><b style="font:600 12.5px JB;color:var(--acc);width:40px">{no}</b><span class="ell" style="flex:1">{g}</span>{st(x)}</div>' for k, (no, g, x) in enumerate([(1431, "Павербанк Volt", "done"), (1388, "Чохол MagSafe", "done"), (1302, "Навушники TWS", "ref")]))}</div></div>
<div class="col" style="gap:12px;min-width:0">
<div class="c"><h3>{sq("package","purple",True,14)}Товари<small>2 позиції</small><span class="r" style="display:flex;gap:6px"><span class="btn sm g">{ic("plus",14)}Товар</span><span class="btn sm g">{ic("plus",14)}Допродаж</span></span></h3>
<div class="row" style="padding:6px 0"><span class="th l">{ic("package",20)}</span><div class="col" style="flex:1"><b style="font-weight:500;font-size:15px">Кавоварка Delonghi</b><small class="mut">ART-001 · на складі 12</small></div>
<span class="row" style="gap:12px;height:32px;border-radius:99px;background:#F6F7F8;padding:0 12px"><span class="fa">−</span><b>1</b><span class="fa">+</span></span><b style="width:90px;text-align:right;font-size:15px">2 499 ₴</b></div>
<div class="row" style="padding:6px 0 6px 26px"><span class="th" style="width:40px;height:40px">{ic("link",15)}</span><div class="col" style="flex:1"><span class="st" style="--c:#7C3AED;width:max-content;height:19px;font-size:11px">допродаж</span><span style="font-weight:500">Набір капсул 50 шт</span></div><b style="width:90px;text-align:right">349 ₴</b></div>
<div class="lab" style="margin-top:10px">Часто беруть разом</div><div class="row" style="gap:8px">{offers}</div>
<div class="sep"></div><div class="row" style="gap:24px;font-size:13.5px"><span><span class="mut">Знижка</span> <b>0 ₴</b></span><span><span class="mut">Собівартість</span> <b>1 800 ₴</b></span><span><span class="mut">Прибуток</span> <b class="ok">1 048 ₴</b></span><span style="margin-left:auto"><span class="mut">Разом</span> <b style="font-size:18px">2 848 ₴</b></span></div></div>
<div class="c"><h3>{sq("wallet","green",True,14)}Оплата<span class="r">+ Оплата</span></h3>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px"><div><div class="lab">Вид оплати</div><div class="inp">{ic("credit-card",15)}Передоплата частково<span style="margin-left:auto" class="fa">{ic("chevron-down",14)}</span></div></div>
<div><div class="lab">У ТТН піде</div><div class="inp" style="background:#EAF1FD;color:#1F4FB8">контроль оплати · <b>2 648 ₴</b></div></div></div>
<div class="row" style="margin-top:10px;background:#F6F7F8;border-radius:12px;padding:9px 12px">{sq("landmark","green",True,13)}<span style="flex:1"><b style="font-weight:500">200 ₴ · Monobank · ФОП Максимчук</b> <span class="ok">надійшла 30.10, 14:50</span></span><span class="st" style="--c:#16A34A">чек пробито</span></div></div>
<div class="c" style="flex:1"><h3>{sq("clock-fading","gray",True,14)}Історія й коментарі<span class="r">Усе</span></h3>{hist}<div class="inp e" style="margin-top:8px">Коментар для колег…</div></div></div>
<div class="col" style="gap:12px">
<div class="c"><h3>{sq("truck","blue",True,14)}Доставка</h3><div class="row" style="background:#F6F7F8;border-radius:14px;padding:10px 12px"><span class="np" style="padding:6px">НП</span><div class="col" style="flex:1"><b style="font-weight:500">Тульчин · №3</b><small class="mut">вул. Шевченка, 12 · платить одержувач</small></div>{ic("chevron-right",16)}</div>
<div class="row" style="gap:8px;margin-top:10px"><span class="btn s" style="flex:1">{ic("truck",16)}Створити ТТН</span><span class="btn g" style="width:42px;padding:0">{ic("ellipsis",16)}</span></div></div>
<div class="c" style="flex:1"><div class="row" style="gap:12px;margin-bottom:6px">{ring("2/5","",.4,"#16A34A",48,4.5,12)}<div class="col"><b style="font-size:15px">Що лишилось</b><small class="mut">3 кроки до відправки</small></div></div>{todo}</div>
</div></div></div>'''
    return frame("orders", f'{head("Замовлення")}', win)


# ============================================================ 4. Ліди
LEADS = [("1", "дн", 1, "#DC2626", "no", "Петренко Іван", "Кавоварка Delonghi", "2 299", "Instagram · спроба 2"),
         ("6", "год", .9, "#DC2626", "new", "Коваленко Олена", "Кавоварка Delonghi", "2 499", "Лендинг"),
         ("54", "хв", .6, "#D97706", "no", "Дмитро Савчук", "Екшн-камера 4К", "5 499", "TikTok · спроба 1"),
         ("12", "хв", .35, "#16A34A", "new", "Оксана Кравець", "Штатив-монопод", "2 797", "Лендинг"),
         ("8", "хв", .25, "#16A34A", "new", "Віктор Поліщук", "Кільцева лампа 26 см", "899", "Instagram"),
         ("3", "хв", .1, "#16A34A", "new", "Марія Ткаченко", "Навушники TWS Pro", "1 649", "Facebook")]


def leads():
    cards = "".join(f'''<div class="c row" style="gap:14px;padding:14px">{ring(v,u,f,c,56)}<div class="col" style="flex:1;align-items:flex-start;gap:3px">{st(s)}<b style="font-size:16.5px" class="ell">{n}</b><small class="mut ell" style="max-width:100%">{g} · <b style="color:var(--ink)">{p} ₴</b></small><small class="fa">{src}</small></div>
<span class="btn {"p" if k == 0 else "s"}" style="width:50px;height:50px;padding:0;border-radius:16px">{ic("phone",20)}</span></div>''' for k, (v, u, f, c, s, n, g, p, src) in enumerate(LEADS))
    tabs = "".join(f'<span class="tab{" on" if on else ""}" style="--c:{c}">{n} <em{" class=h" if h else ""}>{k}</em></span>' for n, k, c, on, h in
                   [("Відкриті", 9, "#1F1F1C", True, False), ("Нові", 4, "#2E6BE6", False, True), ("Недодзвон", 3, "#D97706", False, False), ("Передзвонити", 2, "#7C3AED", False, False), ("Дублі", 1, "#7C7B76", False, False), ("Замовлення", 14, "#16A34A", False, False)])
    cbs = "".join(f'<div class="row" style="padding:9px 0;align-items:flex-start;{"border-top:1px solid #F0F0EE" if k else ""}"><b class="num" style="width:46px;font-size:13px;color:{c}">{t}</b><div class="col" style="flex:1;line-height:1.3"><span style="font-weight:500">{n}</span><small class="mut">{g}</small></div><span class="rb" style="width:34px;height:34px;background:var(--acc2);color:var(--acc)">{ic("phone",15)}</span></div>'
                  for k, (t, n, g, c) in enumerate([("15:30", "Сергій Гончаренко", "Сироватка з вітаміном C", "#DC2626"), ("16:00", "Анна Захарченко", "Маска для обличчя", "#7C3AED"), ("18:00", "Олена Коваль", "просила після 18:00", "#7C3AED"), ("завтра", "Тарас Шевченко", "Павербанк Volt", "var(--mut)")]))
    body = f'''{head("Ліди", "<b>9</b> чекають дзвінка · найдовше чекає <b class=bd>1 дн</b> · сьогодні створено <b>6</b> замовлень",
        f'<span class="srch" style="width:240px">{ic("search",16)}Пошук у лідах</span><span class="rb">{ic("list-filter",19)}</span><span class="seg"><span class="on">Картки</span><span>Дошка</span><span>Передзвони</span></span><span class="rb">{ic("plus",19)}</span>')}
<div style="display:grid;grid-template-columns:1fr 340px;gap:12px;flex:1;min-height:0;padding-bottom:16px">
<div class="col" style="gap:12px">
<div class="row" style="background:linear-gradient(135deg,#2E6BE6,#2457C5);border-radius:20px;color:#fff;padding:16px 20px;gap:18px">
<div><b style="font-size:34px;line-height:1">9</b></div><div class="col"><b style="font-size:15px">чекають дзвінка</b><small style="opacity:.85">черга від найдовшого очікування · F1 недодзвон · F2 передзвонити · F3 відмова</small></div><span style="flex:1"></span>
<span class="btn" style="color:var(--acc);border-radius:99px;height:46px">{ic("phone",18)}Почати дзвонити</span></div>
<div class="row" style="justify-content:space-between"><div class="tabs">{tabs}</div><div class="row" style="gap:6px"><span class="chip on">Мої й нічиї{ic("x",12)}</span><span class="chip dash">{ic("plus",13)}Джерело</span></div></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">{cards}</div></div>
<div class="col" style="gap:12px"><div class="c"><h3>{sq("clock","purple",True,14)}Передзвонити сьогодні<small>4</small></h3>{cbs}</div>
<div class="c"><h3>{sq("chart-bar","blue",True,14)}Сьогодні<small>Олена</small></h3><div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;text-align:center">{"".join(f'<div style="background:#F6F7F8;border-radius:12px;padding:9px"><b style="font-size:18px;{c}">{v}</b><br><small class="mut">{l}</small></div>' for v, l, c in [("23", "дзвінків", ""), ("6", "замовлень", "color:var(--ok)"), ("26%", "конверсія", "")])}</div></div></div></div>'''
    return frame("leads", body)


# ============================================================ 5. Лід: дзвінок
def lead():
    q = "".join(f'<div class="row" style="padding:9px 10px;border-radius:14px;gap:10px;{"background:#fff;box-shadow:0 0 0 1.5px var(--acc3)" if k == 0 else ""}">{ring(v,u,f,c,40,3.5,11)}<div class="col" style="flex:1;line-height:1.25"><b class="ell" style="font-weight:{600 if k == 0 else 500}">{n}</b><small class="mut ell">{g}</small></div></div>'
                for k, (v, u, f, c, s, n, g, p, src) in enumerate(LEADS))
    win = f'''<div style="position:absolute;inset:0;background:rgba(24,24,22,.36)"></div>
<div style="position:absolute;left:24px;right:24px;top:20px;bottom:20px;background:var(--bg);border-radius:22px;display:grid;grid-template-columns:280px 1fr;overflow:hidden">
<aside style="padding:16px 12px;display:flex;flex-direction:column;gap:4px;border-right:1px solid #E6E7E9"><div class="row" style="padding:0 6px 8px"><b style="font-size:15px">Черга дзвінків</b><span class="st" style="--c:#2E6BE6;margin-left:auto">9</span></div>{q}</aside>
<div class="col" style="min-width:0">
<div class="row" style="padding:14px 18px;gap:12px;background:#fff"><span class="rb" style="background:#F2F3F5">{ic("chevron-left",19)}</span><div class="col"><b style="font-size:17px">Лід Л-2047</b><small class="mut">Instagram · 30.10, 09:12</small></div><span style="flex:1"></span><span class="st" style="--c:#D97706">можливий дубль №1431</span><span class="rb" style="background:#F2F3F5">{ic("ellipsis",18)}</span><span class="rb" style="background:#F2F3F5">{ic("x",18)}</span></div>
<div style="display:grid;grid-template-columns:1.1fr 1fr;gap:12px;padding:12px;flex:1;min-height:0">
<div class="col" style="gap:12px">
<div class="c" style="padding:18px 20px"><div class="row" style="gap:16px">{ring("1","дн",1,"#DC2626",68,5.5,17)}<div class="col" style="align-items:flex-start;gap:4px">{st("no")}<b style="font-size:24px;letter-spacing:-.01em">Петренко Іван</b><span class="mut num" style="font-size:15px">+380 67 555 12 40 · спроба 2</span></div></div>
<div class="row" style="gap:8px;margin-top:16px"><span class="btn p" style="flex:2.2;height:50px;font-size:15px">{ic("phone",19)}Подзвонити</span><span class="btn g" style="flex:1;height:50px">{ic("message-circle",19)}Viber</span><span class="btn g" style="flex:1;height:50px">{ic("send",19)}Telegram</span></div>
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:14px">{"".join(f'<div style="background:#F6F7F8;border-radius:12px;padding:8px 10px;line-height:1.2"><b style="font-size:16px">{v}</b><br><small class="mut">{l}</small></div>' for v, l in [("2", "замовлення"), ("50%", "викуп"), ("1", "відмова"), ("2 299 ₴", "сума")])}</div></div>
<div class="c" style="flex:1"><h3>{sq("clock","orange",True,14)}Дзвінки<small>2 спроби</small></h3>
{"".join(f'<div class="row" style="padding:8px 0;{"border-top:1px solid #F0F0EE" if k else ""}">{sq(i,t,True,13)}<span style="flex:1">{a}</span><small class="fa">{w}</small></div>' for k, (i, t, a, w) in enumerate([("phone", "orange", "Недодзвон · SMS «Ми вам дзвонили» надіслано", "сьогодні 12:10 · Олена"), ("phone", "gray", "Не відповів", "учора 18:40 · Олена"), ("inbox", "blue", "Заявка з форми", "учора 09:12")]))}
<div class="lab" style="margin-top:12px">Коментар до дзвінка</div><div class="inp e" style="height:52px;align-items:flex-start;padding-top:9px">Що сказав покупець…</div></div></div>
<div class="col" style="gap:12px">
<div class="c"><h3>{sq("inbox","blue",True,14)}Запит<small>з форми · beauty-landing</small></h3>
<div class="row"><span class="th l">{ic("package",20)}</span><div class="col" style="flex:1"><b style="font-weight:500;font-size:15px">Кавоварка Delonghi</b><small class="mut">1 шт · ціна з лендингу</small></div><b style="font-size:16px">2 299 ₴</b></div>
<div class="sep"></div><div class="kv"><span>Відповіді форми</span><b style="font-weight:500">Чи є чорний колір?</b></div><div class="kv"><span>UTM</span><b style="font-weight:500">instagram · stories · october</b></div><div class="kv"><span>Надійшов</span><b style="font-weight:500">учора, 09:12</b></div></div>
<div class="c" style="border:1.5px dashed var(--acc3);background:#F7FAFF" ><div class="row" style="gap:12px">{sq("plus","blue")}<div class="col"><b style="color:var(--acc);font-size:15px">Створити замовлення тут</b><small class="mut">блоки «Товари · Оплата · Доставка» розгорнуться в цьому вікні</small></div></div></div>
<div class="c" style="flex:1"><h3>{sq("receipt-text","blue",True,14)}Раніше купував<small>2 замовлення</small></h3>
{"".join(f'<div class="row" style="padding:8px 0;{"border-top:1px solid #F0F0EE" if k else ""}"><b style="font:600 12.5px JB;color:var(--acc);width:40px">{no}</b><div class="col" style="flex:1"><span class="ell">{g}</span><small class="fa">{d}</small></div>{st(x)}</div>' for k, (no, g, d, x) in enumerate([(1431, "Павербанк Volt 20 000", "14.09 · 1 599 ₴", "done"), (1302, "Навушники TWS Pro", "02.08 · 1 649 ₴", "ref")]))}
<div class="row" style="margin-top:10px;background:#FDF1E3;border-radius:12px;padding:8px 12px;color:#A85A04;font-size:12.5px">{ic("circle-alert",14)}Одна відмова на пошті — варто уточнити адресу</div></div></div></div>
<div class="row" style="padding:12px 16px;gap:8px;background:#fff">
<span class="btn g">{ic("phone",16)}Недодзвон <span class="fa" style="font:500 11px JB">F1</span></span><span class="btn g">{ic("clock",16)}Передзвонити <span class="fa" style="font:500 11px JB">F2</span></span><span class="btn g" style="color:var(--bad)">{ic("x",16)}Відмова <span class="fa" style="font:500 11px JB">F3</span></span><span class="btn g">{ic("copy",16)}Дубль</span>
<span style="flex:1"></span><span class="btn p" style="height:48px;padding:0 24px;font-size:15px">{ic("check",18)}Створити замовлення <span style="font:500 11px JB;opacity:.7">Ctrl ⏎</span></span></div></div></div>'''
    return frame("leads", head("Ліди"), win)


# ============================================================ 6. Товари + картка товару праворуч
def products():
    rows = [("у продажу", "#16A34A", "Кавоварка Delonghi", "ART-001 · Кавоварки", "2 499", 36, 12, 14, True), ("закінчується", "#D97706", "Бездротовий мікрофон", "MIC-01 · Аудіо", "1 899", 34, 3, 20, False),
            ("у продажу", "#16A34A", "Екшн-камера 4К", "CAM-4K · Камери", "5 499", 22, 100, 100, False), ("допродаж", "#7C3AED", "Набір капсул 50 шт", "CAP-50 · Кавоварки", "349", 48, 30, 60, False),
            ("у продажу", "#16A34A", "Кільцева лампа 26 см", "LAMP-26 · Світло", "899", 41, 100, 100, False), ("немає", "#DC2626", "Штатив-монопод", "TRI-02 · Аксесуари", "2 797", 30, 0, 0, False),
            ("у продажу", "#16A34A", "Павербанк Volt 20 000", "PB-20 · Живлення", "1 599", 28, 64, 80, False), ("архів", "#7C7B76", "Чохол MagSafe старий", "CASE-01 · Аксесуари", "449", 52, 2, 5, False)]
    G = "52px minmax(180px,1.6fr) 110px 80px 150px 110px"
    tr = f'<div class="tr h" style="grid-template-columns:{G}"><span></span><span>Товар</span><span style="text-align:right">Ціна</span><span style="text-align:right">Маржа</span><span>Доступно</span><span>Стан</span></div>'
    for s, c, n, sku, p, m, a, w, sel in rows:
        col = "#DC2626" if a <= 3 else "#D97706" if a < 20 else "#16A34A"
        tr += f'''<div class="tr{" sel" if sel else ""}" style="grid-template-columns:{G};min-height:62px"><span class="th l" style="width:44px;height:44px;border-radius:12px">{ic("package",17)}</span><span class="two"><b class="ell" style="font-weight:500;font-size:14px">{n}</b><small>{sku}</small></span>
<b class="num" style="text-align:right">{p} ₴</b><span class="num" style="text-align:right">{m}%</span><span class="row" style="gap:10px"><b class="num" style="width:30px">{a}</b><span class="bar" style="flex:1"><i style="width:{w}%;background:{col}"></i></span></span><span><span class="st" style="--c:{c}">{"" if s in ("допродаж", "архів") else "<i></i>"}{s}</span></span></div>'''
    vr = "".join(f'<div class="row" style="padding:7px 0;{"border-top:1px solid #F0F0EE" if k else ""}"><i style="width:14px;height:14px;border-radius:5px;background:{c};box-shadow:inset 0 0 0 1px rgba(0,0,0,.15)"></i><span style="flex:1">{n}</span><span class="{cl}" style="width:46px;text-align:right">{q} шт</span><span class="tgl{" on" if on else ""}" style="transform:scale(.8)"></span></div>'
                 for k, (n, c, q, cl, on) in enumerate([("Чорний", "#151515", 8, "", True), ("Білий", "#F4F4F2", 3, "wr", True), ("Червоний", "#C62828", 0, "bd", False)]))
    panel = f'''<aside class="c col" style="width:380px;flex:none;gap:12px">
<div class="row"><span class="st" style="--c:#16A34A"><i></i>у продажу</span><span style="flex:1"></span><span class="rb" style="width:34px;height:34px;background:#F2F3F5">{ic("copy",15)}</span><span class="rb" style="width:34px;height:34px;background:#F2F3F5">{ic("x",15)}</span></div>
<div class="row" style="align-items:stretch;gap:12px"><div class="th" style="width:104px;height:104px;border-radius:16px">{ic("image",28)}</div><div class="col" style="flex:1;gap:3px"><b style="font-size:18px;line-height:1.25">Кавоварка Delonghi</b><small class="mut">ART-001 · Кавоварки · Delonghi</small>
<div class="row" style="gap:6px;margin-top:auto">{"".join(f'<span class="th" style="width:32px;height:32px;border-radius:9px">{ic("image",13)}</span>' for _ in range(3))}<span class="th" style="width:32px;height:32px;border-radius:9px;background:#fff;border:1.5px dashed #D6D6D3">{ic("plus",13)}</span></div></div></div>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px">{"".join(f'<div style="background:#F6F7F8;border-radius:12px;padding:8px 10px"><small class="mut">{l}</small><br><b style="font-size:16px;{c}">{v}</b></div>' for l, v, c in [("Ціна", "2 499 ₴", ""), ("Собівартість", "1 600 ₴", ""), ("Маржа", "36%", "color:var(--ok)")])}</div>
<div><div class="lab">Склад</div><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px;text-align:center">{"".join(f'<div style="background:#F6F7F8;border-radius:12px;padding:7px"><b style="font-size:16px;{c}">{v}</b><br><small class="mut">{l}</small></div>' for l, v, c in [("на складі", "14", ""), ("резерв", "2", ""), ("доступно", "12", "color:var(--ok)")])}</div></div>
<div><div class="row lab" style="margin-bottom:2px">Варіанти · колір<span style="margin-left:auto" class="ac">+ Варіант</span></div>{vr}</div>
<div class="row" style="background:#F6F7F8;border-radius:14px;padding:10px 12px">{sq("chart-bar","blue",True,14)}<div class="col" style="flex:1"><b>142 шт · 227 058 ₴</b><small class="mut">продано за 30 днів · викуп 81%</small></div></div>
<span style="flex:1"></span><div class="row" style="gap:8px"><span class="btn g" style="flex:1">Відкрити повністю</span><span class="btn p" style="flex:1">{ic("check",16)}Зберегти</span></div></aside>'''
    utabs = "".join(f'<span style="padding:6px 0 11px;font-size:15px;{"font-weight:600;box-shadow:inset 0 -2.5px 0 var(--ink)" if on else "color:var(--mut);font-weight:500"}">{n}</span>' for n, on in [("Товари 13", True), ("Категорії", False), ("Виробники", False), ("Атрибути", False)])
    body = f'''{head("Товари", "13 товарів · 3 закінчуються · вартість залишку 312 400 ₴", f'<span class="rb">{ic("scan-barcode",19)}</span><span class="btn p">{ic("plus",17)}Товар</span>')}
<div class="row" style="gap:24px;border-bottom:1px solid #E3E3E0;margin-bottom:12px">{utabs}<span style="flex:1"></span><span class="srch" style="width:250px;height:36px;margin-bottom:8px">{ic("search",15)}Назва або артикул</span>
<span class="chip" style="margin-bottom:8px">Усі категорії{ic("chevron-down",13)}</span><span class="chip" style="margin-bottom:8px">Залишок{ic("chevron-down",13)}</span><span class="chip on" style="margin-bottom:8px">Активні{ic("x",12)}</span></div>
<div class="row" style="align-items:stretch;gap:12px;flex:1;min-height:0;padding-bottom:16px"><div class="tb" style="flex:1">{tr}</div>{panel}</div>'''
    return frame("prod", body)


# ============================================================ 7. Покупці + картка праворуч
def customers():
    data = [("ТШ", "#3557A8", "Шевченко Тарас", "+380 67 123 45 67", ("VIP", "#D97706"), 4, "75%", "ok", "5 840", "сьогодні", False),
            ("МД", "#6A4BA8", "Мельник Денис", "+380 63 118 90 05", ("Повторний", "#2E6BE6"), 9, "89%", "ok", "21 450", "учора", True),
            ("ОС", "#DC2626", "Олійник Світлана", "+380 68 905 12 44", ("ЧС", "#DC2626"), 2, "0%", "bd", "0", "28.10", False),
            ("ІК", "#2D7046", "Коваленко Ірина", "+380 93 552 10 08", ("Новий", "#7C7B76"), 1, "—", "fa", "649", "27.10", False),
            ("ОБ", "#3557A8", "Бондаренко Олег", "+380 99 220 41 77", ("Оптовик", "#0E9488"), 14, "93%", "ok", "48 900", "26.10", False),
            ("ВП", "#B45309", "Поліщук Віктор", "+380 67 801 55 12", ("Новий", "#7C7B76"), 1, "0%", "bd", "0", "25.10", False),
            ("АЗ", "#6A4BA8", "Захарченко Анна", "+380 67 327 60 65", ("Повторний", "#2E6BE6"), 3, "67%", "wr", "3 120", "24.10", False),
            ("СГ", "#2D7046", "Гончаренко Сергій", "+380 67 574 32 27", ("Новий", "#7C7B76"), 1, "—", "fa", "649", "23.10", False)]
    G = "minmax(220px,1.6fr) 110px 70px 70px 100px 90px"
    tr = f'<div class="tr h" style="grid-template-columns:{G}"><span>Покупець</span><span>Група</span><span style="text-align:right">Замовл.</span><span style="text-align:right">Викуп</span><span style="text-align:right">Сума</span><span style="text-align:right">Останнє</span></div>'
    for i, c, n, ph, (g, gc), o, b, bc, s, last, sel in data:
        tr += f'''<div class="tr{" sel" if sel else ""}" style="grid-template-columns:{G};min-height:60px"><span class="row"><span class="av" style="background:color-mix(in srgb,{c} 13%,white);color:{c}">{i}</span><span class="two"><b class="ell" style="font-weight:500">{n}</b><small class="num">{ph}</small></span></span>
<span><span class="st" style="--c:{gc}">{g}</span></span><b class="num" style="text-align:right">{o}</b><b class="num {bc}" style="text-align:right">{b}</b><b class="num" style="text-align:right">{s} ₴</b><span class="mut" style="text-align:right">{last}</span></div>'''
    hist = "".join(f'<div class="row" style="padding:8px 0;{"border-top:1px solid #F0F0EE" if k else ""}"><b style="font:600 12.5px JB;color:var(--acc);width:42px">{no}</b><span class="ell" style="flex:1">{g}</span>{st(s)}</div>'
                   for k, (no, g, s) in enumerate([(1476, "Смарт-годинник Fit 3", "wait"), (1431, "Павербанк Volt", "done"), (1388, "Чохол MagSafe", "done"), (1302, "Навушники TWS Pro", "ref")]))
    panel = f'''<aside class="c col" style="width:380px;flex:none;gap:12px">
<div class="row"><span class="av l" style="background:#EEE8F8;color:#6A4BA8">МД</span><div class="col" style="flex:1"><b style="font-size:18px">Мельник Денис</b><span class="mut num">+380 63 118 90 05</span></div><span class="st" style="--c:#2E6BE6">Повторний</span></div>
<div class="msg"><span class="p">{ic("phone",17)}</span><span>{ic("message-circle",17)}</span><span>{ic("send",17)}</span><span>{ic("message-square",17)}</span></div>
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px">{"".join(f'<div style="background:#F6F7F8;border-radius:12px;padding:8px 9px;line-height:1.2"><b style="font-size:16px">{v}</b><br><small class="mut" style="font-size:11.5px">{l}</small></div>' for v, l in [("9", "замовл."), ("89%", "викуп"), ("1", "відмова"), ("21,4к", "сума ₴")])}</div>
<div><div class="row lab">Замовлення<span style="margin-left:auto" class="ac">Усі 9</span></div>{hist}</div>
<div><div class="lab">Адреси</div><div class="row" style="background:#F6F7F8;border-radius:12px;padding:9px 12px"><span class="np">НП</span><span style="flex:1">Тульчин, відділення №1</span><small class="fa">6 разів</small></div></div>
<div class="inp" style="height:auto;padding:10px 12px;line-height:1.4;color:var(--mut)">«Дзвонити після 18:00. Любить подарункове пакування.»</div>
<span style="flex:1"></span><div class="row" style="gap:8px"><span class="btn g" style="width:42px;padding:0;color:var(--bad)">{ic("lock-open",17)}</span><span class="btn g" style="flex:1">Відкрити</span><span class="btn p" style="flex:1.4">{ic("plus",16)}Нове замовлення</span></div></aside>'''
    tabs = "".join(f'<span class="tab{" on" if on else ""}" style="--c:{c}">{n} <em>{k}</em></span>' for n, k, c, on in
                   [("Усі", "3 412", "#1F1F1C", True), ("VIP", 42, "#D97706", False), ("Повторні", 920, "#2E6BE6", False), ("Оптовики", 18, "#0E9488", False), ("Чорний список", 14, "#DC2626", False)])
    body = f'''{head("Покупці", "3 412 покупців · 28 нових за тиждень · повторні 27%", f'<span class="srch" style="width:280px">{ic("search",16)}Ім\'я, телефон або email</span><span class="chip" style="height:42px;border-radius:14px">Останнє замовлення{ic("chevron-down",14)}</span><span class="btn p">{ic("plus",17)}Покупець</span>')}
<div class="tabs" style="margin-bottom:12px">{tabs}</div>
<div class="row" style="align-items:stretch;gap:12px;flex:1;min-height:0;padding-bottom:16px"><div class="tb" style="flex:1">{tr}</div>{panel}</div>'''
    return frame("cust", body)


# ============================================================ 8. Склад
def stock():
    rows = [("Бездротовий мікрофон", "Чорний · MIC-01", 5, 2, 3, 1.2, "через 2 дні", "#DC2626", True), ("Кавоварка Delonghi", "ART-001", 14, 2, 12, 1.9, "через 6 днів", "#D97706", True),
            ("Штатив-монопод", "TRI-02", 0, 0, 0, 0.8, "закінчились", "#DC2626", True), ("Екшн-камера 4К", "CAM-4K", 104, 4, 100, 2.4, "через 41 день", "#16A34A", False),
            ("Кільцева лампа 26 см", "LAMP-26", 100, 0, 100, 0.6, "понад рік", "#16A34A", False), ("Павербанк Volt 20 000", "PB-20", 68, 4, 64, 4.7, "через 13 днів", "#16A34A", False),
            ("Набір капсул 50 шт", "CAP-50", 30, 0, 30, 0, "не продається", "#7C7B76", False)]
    G = "minmax(160px,1.7fr) 64px 56px 70px 60px 140px 96px"
    tr = f'<div class="tr h" style="grid-template-columns:{G}"><span>Товар · варіант</span><span style="text-align:right">Залишок</span><span style="text-align:right">Резерв</span><span style="text-align:right">Доступно</span><span style="text-align:right">Шт/день</span><span>Прогноз</span><span></span></div>'
    for n, s, a, r, av, d, f, c, buy in rows:
        tr += f'''<div class="tr" style="grid-template-columns:{G}"><span class="two"><b class="ell" style="font-weight:500">{n}</b><small>{s}</small></span><span class="num" style="text-align:right">{a}</span><span class="num mut" style="text-align:right">{r}</span>
<b class="num" style="text-align:right;{"color:var(--bad)" if av <= 0 else ""}">{av}</b><span class="num mut" style="text-align:right">{d or "—"}</span><span><span class="st" style="--c:{c}">{ic("clock",12)}{f}</span></span><span style="text-align:right">{'<span class="btn sm s">Закупити</span>' if buy else ""}</span></div>'''
    mv = "".join(f'<div class="row" style="padding:8px 0;align-items:flex-start;{"border-top:1px solid #F0F0EE" if k else ""}"><b class="num" style="width:44px;color:{c}">{d}</b><div class="col" style="flex:1;line-height:1.3"><span>{a}</span><small class="mut">{p}</small></div><small class="fa num">{t}</small></div>'
                 for k, (d, c, a, p, t) in enumerate([("+50", "var(--ok)", "Закупівля №12", "Павербанк Volt 20 000", "16:10"), ("−1", "var(--ink)", "Відправка · №142", "Маска для обличчя", "15:57"),
                                                      ("рез 1", "var(--acc)", "Резерв · №144", "Крем для рук", "15:40"), ("−2", "var(--ink)", "Відправка · №141", "Мило ручної роботи", "14:12"), ("−1", "var(--bad)", "Списання · брак", "Чохол MagSafe", "11:05")]))
    tile = lambda icon, t, v, l, sub, bg="": f'<div class="c" style="padding:14px 16px;{bg}"><div class="row">{sq(icon,t,True,15)}<span class="mut" style="font-size:13px">{l}</span></div><div style="font-size:24px;font-weight:600;margin-top:8px">{v}</div><small class="mut">{sub}</small></div>'
    tabs = "".join(f'<span class="tab{" on" if on else ""}" style="--c:{c}">{n} <em>{k}</em></span>' for n, k, c, on in [("Усі", 214, "#1F1F1C", True), ("Закінчуються", 12, "#D97706", False), ("Немає", 5, "#DC2626", False), ("Неліквід", 3, "#7C7B76", False)])
    body = f'''{head("Склад", "Основний склад · оновлено щойно", f'<span class="srch" style="width:240px">{ic("search",16)}Товар або артикул</span><span class="btn">{ic("list-checks",16)}Інвентаризація</span><span class="btn p">{ic("package-plus",17)}Прийняти товар</span>')}
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:12px">{tile("banknote","green","312 400 ₴","Вартість залишку","за собівартістю · 978 шт")}{tile("lock-open","blue","23 шт","У резерві","18 640 ₴ у прийнятих замовленнях")}
{tile("circle-alert","orange","12","Закінчуються за тиждень","закупити на ≈ 48 300 ₴","background:#FDF1E3")}{tile("x","red","5","Немає в наявності","3 з них є в нових замовленнях")}</div>
<div class="row" style="margin-bottom:12px"><div class="tabs">{tabs}</div></div>
<div style="display:grid;grid-template-columns:1fr 340px;gap:12px;flex:1;min-height:0;padding-bottom:16px"><div class="tb">{tr}</div><div class="c"><h3>{sq("clock-fading","gray",True,14)}Рухи сьогодні<span class="r">Усі рухи</span></h3>{mv}</div></div>'''
    return frame("stock", body)


# ============================================================ 9. Статистика
def stats():
    import random
    random.seed(5)
    cols = ["#16A34A", "#6D5BD0", "#D97706", "#DC2626"]
    bars = ""
    for d in range(29):
        y = 230
        for c, sh in zip(cols, (.6, .18, .1, .12)):
            h = (40 + random.randint(0, 60)) * sh * 1.6
            y -= h
            bars += f'<rect x="{10 + d * 24}" y="{y:.1f}" width="15" height="{h:.1f}" rx="2" fill="{c}"/>'
    line = " ".join(f"{17 + d*24},{70 + (d * 37 % 50)}" for d in range(29))
    leg = "".join(f'<div class="row" style="padding:7px 0;{"border-top:1px solid #F0F0EE" if k else ""}"><i style="width:10px;height:10px;border-radius:3px;background:{c}"></i><span style="flex:1">{n}</span><b>{p}</b><span class="fa num" style="width:38px;text-align:right">{q}</span></div>'
                  for k, (c, p, q, n) in enumerate([("#1F1F1C", "100%", 742, "Усі"), ("#16A34A", "61%", 452, "Завершений"), ("#6D5BD0", "8%", 59, "Відправлений"), ("#D97706", "3%", 22, "Очікує"), ("#DC2626", "13%", 96, "Відмова"), ("#7C7B76", "15%", 113, "Інші")]))
    tile = lambda l, v, d, dc, s1, s2: f'<div class="c" style="padding:14px 16px"><div class="row" style="justify-content:space-between"><span class="mut">{l}</span><span class="st" style="--c:{dc}">{d}</span></div><div style="font-size:26px;font-weight:600;margin:6px 0 4px;letter-spacing:-.02em">{v}</div><div class="kv" style="font-size:12.5px"><span>{s1[0]}</span><b>{s1[1]}</b></div><div class="kv" style="font-size:12.5px"><span>{s2[0]}</span><b>{s2[1]}</b></div></div>'
    kp = "".join(f'<div style="flex:1;padding:4px 16px;{"border-left:1px solid #F0F0EE" if k else ""}"><small class="mut">{l}</small><div class="row" style="gap:6px"><b style="font-size:18px">{v}</b><small class="{c}">{d}</small></div><small class="fa">{s}</small></div>'
                 for k, (l, v, d, c, s) in enumerate([("Апрув", "72%", "+3 п.", "ok", "534 підтверджено"), ("Викуп", "78%", "−2 п.", "bd", "452 отримано"), ("Відправлено", "614", "+40", "ok", "83% від замовлень"),
                                                       ("Підтвердження", "14 хв", "−4", "ok", "від заявки до апруву"), ("Допродаж", "31%", "+2 п.", "ok", "231 замовлення"), ("Повернення", "6%", "0", "fa", "41 повернення")]))
    body = f'''{head("Статистика", "1–29 жовтня порівняно з 1–29 вересня", f'<span class="chip" style="height:42px;border-radius:14px">{ic("calendar",14)}За датою: додане{ic("chevron-down",13)}</span><span class="chip" style="height:42px;border-radius:14px">1–29 жовтня{ic("chevron-down",13)}</span><span class="seg"><span class="on">Авто</span><span>Дні</span><span>Тижні</span><span>Місяці</span></span><span class="btn">{ic("send",16)}Поділитися</span>')}
<div class="row" style="gap:6px;margin-bottom:12px"><span class="chip on">Instagram{ic("x",12)}</span><span class="chip on">Олена{ic("x",12)}</span><span class="chip dash">{ic("plus",13)}Товар</span><span class="chip dash">{ic("plus",13)}Доставка</span><span class="chip dash">{ic("plus",13)}Оплата</span><span class="chip dash">{ic("plus",13)}Відділ</span><span class="ac" style="margin-left:6px;font-weight:500">Ще 8 фільтрів і пошук</span></div>
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:12px">{tile("Замовлення","742","+12%","#16A34A",("основні","511"),("з допродажем","231"))}{tile("Сума","1 084 300 ₴","+9%","#16A34A",("основна","961 700 ₴"),("допродаж","122 600 ₴"))}
{tile("Маржа","389 600 ₴","+7%","#16A34A",("основна","342 100 ₴"),("середня","525 ₴"))}{tile("Середній чек","1 461 ₴","−3%","#DC2626",("маржа в чеку","525 ₴"),("товарів у чеку","1,4"))}</div>
<div class="c row" style="padding:12px 4px;margin-bottom:12px">{kp}</div>
<div class="c" style="flex:1;margin-bottom:16px"><h3>Статуси по днях<small>стовпці — статуси, лінія — усі замовлення</small><span class="r" style="display:flex;gap:6px"><span class="tab on" style="--c:#1F1F1C;height:30px">Статуси</span><span class="tab" style="height:30px">Товари</span><span class="tab" style="height:30px">Менеджери</span><span class="tab" style="height:30px">Джерела</span></span></h3>
<div style="display:grid;grid-template-columns:1fr 240px;gap:20px;align-items:start"><svg width="100%" height="390" viewBox="0 0 710 240" preserveAspectRatio="none"><line x1="0" x2="710" y1="230" y2="230" stroke="#EFEFED"/>{bars}<polyline points="{line}" fill="none" stroke="#1F1F1C" stroke-width="1.6"/></svg><div>{leg}</div></div></div>'''
    return frame("stats", body)


# ============================================================ 10. Налаштування
def settings():
    grp = lambda t, rows: f'<div class="gt" style="margin:8px 4px 6px">{t}</div><div class="c" style="padding:4px 8px">{rows}</div>'
    r = lambda items: "".join(f'<div class="row" style="padding:7px 8px;border-radius:12px;{"background:#F2F6FE" if on else ""}">{sq(i,t,True,14)}<span style="flex:1;{"font-weight:600" if on else ""}">{l}</span>{x}</div>' for i, t, l, x, on in items)
    left = f'''<div style="width:300px;flex:none;overflow:hidden"><span class="srch" style="width:100%;margin-bottom:6px">{ic("search",16)}Знайти налаштування</span>
{grp("Робота", r([("sliders-horizontal","gray","Загальні","",True),("list-checks","purple","Статуси","",False),("layers","blue","Довідники","",False),("key-round","purple","Користувачі",'<span class="fa">4</span>',False)]))}
{grp("Гроші й доставка", r([("landmark","green","Юрособи",'<span class="fa">2</span>',False),("truck","red","Нова Пошта",'<span class="st" style="--c:#16A34A">2 ключі</span>',False),("receipt","teal","Checkbox",'<span class="st" style="--c:#D97706">зміна закрита</span>',False),("store","orange","Маркетплейси","",False)]))}
{grp("Зв'язок і документи", r([("inbox","blue","Прийом заявок","",False),("message-square","blue","SMS і Viber","",False),("send","blue","Telegram","",False),("file-text","gray","Документи","",False)]))}</div>'''
    fld = lambda l, v, w="1fr": f'<div><div class="lab">{l}</div><div class="inp">{v}</div></div>'
    right = f'''<div class="col" style="flex:1;gap:12px;min-width:0">
<div class="c" style="box-shadow:0 0 0 1.5px var(--acc3)"><div class="row" style="gap:12px">{sq("inbox","blue")}<div class="col" style="flex:1"><b style="font-size:15.5px">Розділ «Ліди»</b><small class="mut">Заявки з форм спершу йдуть у «Ліди»: заявка → дзвінок → «Створити замовлення». Вимкніть, якщо замовлення приходять готовими.</small></div><span class="tgl on"></span></div>
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:14px">{fld("Чекає — помаранчевим після, хв","5")}{fld("Чекає — червоним після, хв","15")}{fld("Нагадати після недодзвону, хв","30")}{fld("Замовлення з ліда отримує статус",'<span class="st" style="--c:#2E6BE6"><i></i>Прийнятий</span><span style="margin-left:auto" class="fa">'+ic("chevron-down",14)+'</span>')}</div></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
<div class="c"><h3>{sq("building","gray",True,14)}Компанія</h3><div class="col" style="gap:10px">{fld("Назва в CRM і SMS","Моя CRM")}{fld("Часовий пояс","Київ (UTC+2)")}{fld("Відділ за замовчуванням","Роздріб")}</div></div>
<div class="c"><h3>{sq("receipt-text","blue",True,14)}Замовлення</h3><div class="col" style="gap:10px">{fld("Наступний номер замовлення","1 482")}{fld("Коли резервувати товар",'Статус «Прийнятий»<span style="margin-left:auto" class="fa">'+ic("chevron-down",14)+'</span>')}
<div class="row" style="justify-content:space-between;padding-top:4px"><span>Відкривати наступне після збереження</span><span class="tgl"></span></div></div></div></div>
<div class="c"><h3>{sq("copy","orange",True,14)}Дублі й розподіл</h3><div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px">{fld("Дубль — якщо збігаються","номер · товар · сума")}{fld("Шукати дублі за останні, днів","7")}{fld("Нові заявки розподіляти",'по черзі між менеджерами<span style="margin-left:auto" class="fa">'+ic("chevron-down",14)+'</span>')}</div></div>
<span style="flex:1"></span>
<div class="row" style="background:#fff;border-radius:18px;padding:12px 16px;gap:10px;margin-bottom:16px"><span class="row wr" style="gap:6px;font-weight:500">{ic("circle-alert",15)}Є незбережені зміни · 2 поля</span><span style="flex:1"></span><span class="btn g">Скасувати</span><span class="btn p">{ic("check",16)}Зберегти зміни <span style="font:500 11px JB;opacity:.75">Ctrl S</span></span></div></div>'''
    body = f'''{head("Налаштування", "Загальні — як працює CRM для всієї команди", SEARCH)}<div class="row" style="align-items:stretch;gap:16px;flex:1;min-height:0">{left}{right}</div>'''
    return frame("set", body)


SCREENS = [("01-home", "1 · Головна", home), ("02-orders", "2 · Замовлення + панель перегляду", orders), ("03-card", "3 · Картка замовлення", card),
           ("04-leads", "4 · Ліди", leads), ("05-lead", "5 · Лід: дзвінок", lead), ("06-products", "6 · Товари + картка праворуч", products),
           ("07-customers", "7 · Покупці + картка праворуч", customers), ("08-stock", "8 · Склад", stock), ("09-stats", "9 · Статистика", stats), ("10-settings", "10 · Налаштування", settings)]


def build():
    return page("ПК v2 — 10 сторінок", CSS, [(k, n, f(), 1440, 900) for k, n, f in SCREENS], cols=2, gap=48)
