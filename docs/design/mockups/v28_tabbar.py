"""v28 — нижня панель телефону: «Зараз» (справжній скриншот) і 4 варіанти на тому самому екрані «Замовлення»."""
import base64
from pathlib import Path
from common import *
from v17_mobile import head, rb, scr
from v27_mobile import CSS as V27, mk, order_c, NP

SHOT = Path("/tmp/claude-0/b/orders.png")

CSS = V27.replace("'Onest';", "'Onest',sans-serif;").replace("'Onest'}", "'Onest',sans-serif}") + """
.ph .m{border-radius:28px}
/* під панеллю — список; підкладка-градієнт, щоб картки не просвічували крізь панель */
.scrim{position:absolute;left:0;right:0;bottom:0;height:120px;z-index:4;background:linear-gradient(rgba(241,242,244,0),#F1F2F4 55%)}
.badge{position:absolute;top:-5px;left:calc(50% + 5px);min-width:19px;height:19px;padding:0 5px;border-radius:99px;font:700 10.5px/19px 'Onest',sans-serif;text-align:center;font-style:normal;color:#fff}
.badge.hot{background:#E0245E}.badge.blue{background:#2E6BE6}
/* A — острівець, доведений */
.ta{position:absolute;left:12px;right:12px;bottom:16px;height:68px;border-radius:26px;background:#fff;z-index:5;display:grid;grid-template-columns:1fr 1fr 76px 1fr 1fr;align-items:center;
  box-shadow:0 16px 34px -14px rgba(31,31,28,.35),0 0 0 1px rgba(31,31,28,.05)}
.ta a{position:relative;display:flex;flex-direction:column;align-items:center;gap:4px;font:500 11.5px 'Onest',sans-serif;color:#5E5D58}
.ta a.on{color:#1F4FB8;font-weight:600}.ta a .ico{position:relative;width:48px;height:30px;border-radius:99px;display:grid;place-items:center}
.ta a.on .ico{background:#E3ECFC}
.ta a .badge{box-shadow:0 0 0 2px #fff}
.ta .plus{justify-self:center;width:60px;height:60px;border-radius:50%;display:grid;place-items:center;background:#2E6BE6;color:#fff;margin-top:-26px;
  box-shadow:0 0 0 6px #F1F2F4,0 10px 20px -6px rgba(46,107,230,.75)}
/* B — пігулка з вкладками і окремий «+» */
.tb{position:absolute;left:14px;right:86px;bottom:18px;height:60px;border-radius:99px;background:#fff;z-index:5;display:flex;align-items:center;gap:2px;padding:0 6px;
  box-shadow:0 14px 30px -12px rgba(31,31,28,.35),0 0 0 1px rgba(31,31,28,.05)}
.tb a{position:relative;flex:1;height:48px;min-width:44px;border-radius:99px;display:flex;align-items:center;justify-content:center;gap:7px;color:#5E5D58;font:600 14px 'Onest',sans-serif}
.tb a.on{flex:none;background:#1F1F1C;color:#fff;padding:0 14px 0 12px;font-size:13.5px}
.tb a .badge{top:2px;left:auto;right:4px;box-shadow:0 0 0 2px #fff}
.tbp{position:absolute;right:14px;bottom:18px;width:60px;height:60px;border-radius:50%;background:#2E6BE6;color:#fff;display:grid;place-items:center;z-index:5;
  box-shadow:0 12px 24px -8px rgba(46,107,230,.8)}
/* C — на всю ширину, прилипла донизу */
.tc{position:absolute;left:0;right:0;bottom:0;height:86px;padding-bottom:22px;background:#fff;z-index:5;display:grid;grid-template-columns:repeat(5,1fr);align-items:center;
  border-top:1px solid #E6E6E3}
.tc a{position:relative;display:flex;flex-direction:column;align-items:center;gap:3px;font:500 11.5px 'Onest',sans-serif;color:#6F6E69}
.tc a.on{color:#2E6BE6;font-weight:600}.tc a.on::before{content:"";position:absolute;top:-12px;width:28px;height:3px;border-radius:0 0 3px 3px;background:#2E6BE6}
.tc a .ico{position:relative}.tc a .badge{top:-6px;left:12px;box-shadow:0 0 0 2px #fff}
.tc .plus{justify-self:center;width:56px;height:56px;border-radius:50%;display:grid;place-items:center;background:#2E6BE6;color:#fff;margin-top:-30px;
  box-shadow:0 0 0 5px #fff,0 10px 18px -8px rgba(46,107,230,.7)}
/* D — ховається при прокрутці, «+» з підписом розділу */
.td-pill{position:absolute;right:16px;bottom:22px;height:54px;padding:0 20px 0 16px;border-radius:99px;background:#2E6BE6;color:#fff;display:flex;align-items:center;gap:8px;
  font:600 15.5px 'Onest',sans-serif;z-index:5;box-shadow:0 12px 24px -8px rgba(46,107,230,.8)}
.td-up{position:absolute;left:16px;bottom:26px;width:46px;height:46px;border-radius:50%;background:#fff;display:grid;place-items:center;color:#1F1F1C;z-index:5;
  box-shadow:0 8px 20px -10px rgba(31,31,28,.4),0 0 0 1px rgba(31,31,28,.05)}
.qm{position:absolute;left:50%;transform:translateX(-50%);bottom:98px;width:236px;background:#fff;border-radius:20px;padding:6px;z-index:7;
  box-shadow:0 20px 40px -14px rgba(31,31,28,.4),0 0 0 1px rgba(31,31,28,.05)}
.qm div{display:flex;align-items:center;gap:12px;height:48px;padding:0 12px;border-radius:14px;font:500 15px 'Onest',sans-serif}
.qm div:first-child{background:#EEF3FD;color:#1F4FB8;font-weight:600}
.qm .k{margin-left:auto;font:500 11.5px 'JetBrains Mono',ui-monospace,monospace;color:#A3A29D}
.dim2{position:absolute;inset:0;background:rgba(24,24,22,.28);z-index:6}
"""


def shot():
    b = base64.b64encode(SHOT.read_bytes()).decode()
    return f'<img src="data:image/png;base64,{b}" width="390" height="844" alt="">'


def lst():
    return f'''{head("Замовлення", rb("search") + rb("list-filter", "", '<span class="dot"></span>'))}
<div class="row" style="padding:0 18px 10px;gap:10px;margin-top:-4px"><span class="chip" style="height:40px;padding:0 14px;font-size:14.5px;background:#5F5E5A;color:#fff;border:0">Несортовані <b style="opacity:.8">16</b>{ic("chevron-down",15)}</span><span class="mut" style="font-size:12.5px;line-height:1.3">3 до відправки · 13 у дорозі</span></div>
{order_c("uns","44","17:10","Олена Коваль","1 899","Бездротовий мікрофон","",NP("Київ, №12"),"p")}
{order_c("uns","43","17:00","Андрій Мельник","2 000","Набір капсул 50 шт","+1",'<span class="fa" style="font-size:12.5px">без доставки</span>',"p")}
{order_c("acc","42","16:37","Микола Бондаренко","3 899","Радіосистема DJI Mic 2","",NP("Львів, №5"),"s")}
{order_c("sent","40","15:50","Тарас Ткаченко","5 499","Екшн-камера 4К","",NP("Одеса, №31"),"o")}'''


def bd(n):
    return f'<em class="badge hot">{n}</em>' if n else ""


TABS = [("home", "house", "Головна", None), ("orders", "receipt-text", "Замовлення", "16"), ("leads", "inbox", "Ліди", "4"), ("more", "ellipsis", "Ще", None)]


def bar_a(active="orders"):
    a = lambda k, i, l, n: f'<a class="{"on" if k == active else ""}"><span class="ico">{ic(i, 21, 2 if k == active else 1.75)}{bd(n)}</span>{l}</a>'
    return f'<div class="scrim"></div><nav class="ta">{a(*TABS[0])}{a(*TABS[1])}<span class="plus">{ic("plus",28,2.4)}</span>{a(*TABS[2])}{a(*TABS[3])}</nav>'


def bar_b(active="orders"):
    a = lambda k, i, l, n: f'<a class="{"on" if k == active else ""}">{ic(i, 21, 2 if k == active else 1.75)}{l if k == active else ""}{(bd(n) if k != active else "")}</a>'
    return f'<div class="scrim"></div><nav class="tb">{"".join(a(*t) for t in TABS)}</nav><span class="tbp">{ic("plus",28,2.4)}</span>'


def bar_c(active="orders"):
    a = lambda k, i, l, n: f'<a class="{"on" if k == active else ""}"><span class="ico">{ic(i, 22, 2 if k == active else 1.75)}{bd(n)}</span>{l}</a>'
    return f'<nav class="tc">{a(*TABS[0])}{a(*TABS[1])}<span class="plus">{ic("plus",26,2.4)}</span>{a(*TABS[2])}{a(*TABS[3])}</nav>'


def v_a():
    return scr(lst() + bar_a() + mk(1, "left:10px;top:700px") + mk(2, "left:232px;top:742px") + mk(3, "left:296px;top:746px") + mk(4, "left:60px;top:746px"))


def v_b():
    return scr(lst() + bar_b() + mk(5, "left:120px;top:748px") + mk(6, "left:352px;top:744px"))


def v_c():
    return scr(lst() + bar_c() + mk(7, "left:8px;top:762px") + mk(8, "left:214px;top:738px"))


def v_d_scroll():
    body = lst().replace('<div class="row" style="padding:0 18px 10px', '<div class="row" style="display:none;padding:0 18px 10px', 1)
    return scr(body + f'<div class="scrim" style="height:90px"></div><span class="td-pill">{ic("plus",20,2.4)}Замовлення</span>' + mk(9, "left:300px;top:752px"))


def v_d_menu():
    items = [("receipt-text", "Замовлення", "N"), ("inbox", "Лід", "L"), ("user-round-plus", "Покупець", ""), ("package-plus", "Товар", "")]
    qm = "".join(f'<div>{ic(i,19)}{l}<span class="k">{k}</span></div>' for i, l, k in items)
    return scr(lst() + bar_a() + f'<div class="dim2"></div><div class="qm">{qm}</div>' + mk(10, "left:300px;top:540px"))


def frame(befores, afters, title, lead, items):
    ph = "".join(f'<div class="ph"><div class="cap"><i></i>Зараз</div>{b}</div>' for b in befores)
    ph += "".join(f'<div class="ph"><div class="cap new"><i></i>{cap}</div>{h}</div>' for cap, h in afters)
    rows = "".join(f'<div class="li">{mk(n)}<div><b>{t}</b><p>{d}</p></div></div>' for n, t, d in items)
    return f'<div class="fr">{ph}<aside class="lg"><h2>{title}</h2><div class="lead">{lead}</div>{rows}</aside></div>'


F = [
    ("1-ab", "Нижня панель · A і B",
     [shot()], [("A · острівець, доведений", v_a()), ("B · пігулка + окремий «+»", v_b())],
     "Зараз картки просвічують крізь панель (видно синю «Прийняти»), підписи 10 px сірим (контраст нижче норми), лічильники сині — як звичайні, хоч це «треба зробити».",
     [(1, "Список не залазить під панель", "Знизу м'яка підкладка кольору фону: картки плавно зникають, а не просвічують крізь кнопки."),
      (2, "«+» — круглий і трохи вище", "Піднятий над панеллю, з вирізом кольору фону: його видно одразу, і він не плутається з вкладками."),
      (3, "Лічильники — червоні", "Несортовані й нові ліди — це «треба зробити», тому червоні, як на головній. Синій лишається для активної вкладки."),
      (4, "Підписи 11,5 px, темніші", "Неактивні — #5E5D58 (контраст ≥ 4,5:1), активна — синя й жирна, з пігулкою під значком."),
      (5, "B: лише значки, активна — з підписом", "Чорна пігулка з назвою показує, де ви; решта — значки 48 px. Панель вужча — під нею менше закритого списку."),
      (6, "B: «+» окремо праворуч", "Під великим пальцем правої руки; не стоїть між вкладками, тож вкладки не «стрибають».")]),
    ("2-cd", "Нижня панель · C і D",
     [], [("C · на всю ширину", v_c()), ("D · при прокрутці вниз", v_d_scroll()), ("D · довгий натиск на «+»", v_d_menu())],
     "C — звична для iPhone і Android панель; D — панель як у A, але ховається, коли гортаєте список, і «+» знає, на якій ви сторінці.",
     [(7, "C: прилипла до низу, без «острівця»", "Біла смуга з тонкою лінією зверху. Нічого не просвічує, активна вкладка — синя риска зверху."),
      (8, "C: «+» виступає над панеллю", "Круг 56 px у білій обвідці — головна дія завжди на місці."),
      (9, "D: гортаєте вниз — панель ховається", "Лишається одна кнопка з підписом розділу: «+ Замовлення», у лідах — «+ Лід», у товарах — «+ Товар». Гортаєте вгору — панель повертається. Круглі «+» у шапці сторінок тоді не потрібні."),
      (10, "D: довгий натиск — швидке створення", "Замовлення, лід, покупець, товар — з будь-якої сторінки, з клавішами N і L на ПК.")]),
]


def build():
    frames = []
    for k, title, bef, aft, lead, items in F:
        w = 26 * 2 + (len(bef) + len(aft)) * (390 + 28) + 330
        frames.append((k, title, frame(bef, aft, title, lead, items), w, 930))
    return page("Нижня панель телефону — варіанти", CSS, frames, cols=1, gap=40)
