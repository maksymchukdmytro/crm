"""v27 — мобільна версія після оновлень: «зараз» (справжній скриншот) → «стане» (макет) і 18 покращень."""
import base64
from pathlib import Path
from common import *
from v17_mobile import CSS as MCSS, st, sq, ring, bar, head, rb, tabs, scr

SHOTS = Path("/tmp/claude-0/walk")

CSS = MCSS + """
.fr{display:flex;gap:28px;padding:26px;background:#fff;height:100%;align-items:flex-start}
.ph{display:flex;flex-direction:column;gap:10px;flex:none}
.ph .cap{font:600 14px 'Onest';color:#6F6E69;display:flex;align-items:center;gap:8px}
.ph .cap.new{color:#1F1F1C}
.ph .cap i{width:8px;height:8px;border-radius:50%;background:#C9C8C3}.ph .cap.new i{background:#DB2777}
.ph img,.ph .m{border-radius:28px;box-shadow:0 20px 40px -24px rgba(0,0,0,.35),0 0 0 1px rgba(0,0,0,.06)}
.lg{width:330px;flex:none;display:flex;flex-direction:column;gap:13px;font:400 13px/1.45 'Onest',sans-serif;color:#1F1F1C;padding-top:30px}
.lg h2{font-size:20px;font-weight:600;letter-spacing:-.01em;line-height:1.2}
.lg .lead{font-size:12.5px;color:#6F6E69;margin-top:-6px}
.lg .li{display:flex;gap:10px;align-items:flex-start}.lg .li b{display:block;font-size:13.5px;font-weight:600;margin-bottom:2px}.lg .li p{font-size:12.5px;color:#57564F}
.mk{display:inline-grid;place-items:center;min-width:22px;height:22px;padding:0 6px;border-radius:99px;background:#DB2777;color:#fff;font:700 11.5px/1 'Onest';flex:none;box-shadow:0 0 0 2px #fff;font-style:normal}
.mk.a{position:absolute;z-index:20}
.m .bad-note{position:absolute;z-index:20}
.go{flex:1;height:34px;border-radius:11px;display:flex;align-items:center;justify-content:center;gap:6px;font-size:13px;font-weight:600;background:#F2F2F0;color:#3D3C38}
.go.p{background:var(--acc);color:#fff}.go.s{background:var(--acc2);color:var(--acc)}.go.g{background:#E9F6EE;color:#15803D}.go.v{background:#F1ECFB;color:#7C3AED}
.ibx{width:44px;height:44px;border-radius:13px;display:grid;place-items:center;background:#F2F2F0;color:#3D3C38;flex:none}
.bar2{height:6px;border-radius:99px;background:#EFEFED;overflow:hidden}.bar2 i{display:block;height:100%;border-radius:99px}
"""


def mk(n, style=""):
    return f'<span class="mk{" a" if style else ""}" style="{style}">{n}</span>'


def shot(name):
    b = base64.b64encode((SHOTS / name).read_bytes()).decode()
    return f'<img src="data:image/png;base64,{b}" width="390" height="844" alt="">'


def frame(title, lead, befores, afters, items):
    ph = "".join(f'<div class="ph"><div class="cap"><i></i>Зараз</div>{shot(b)}</div>' for b in befores)
    ph += "".join(f'<div class="ph"><div class="cap new"><i></i>{cap}</div>{html}</div>' for cap, html in afters)
    rows = "".join(f'<div class="li">{mk(n)}<div><b>{t}</b><p>{d}</p></div></div>' for n, t, d in items)
    return f'<div class="fr">{ph}<aside class="lg"><h2>{title}</h2><div class="lead">{lead}</div>{rows}</aside></div>'


# ---------------------------------------------------------------- 1–2. Головна
def home():
    todo = "".join(f'''<div style="flex:none;width:132px;background:#fff;border-radius:18px;padding:11px 12px;display:flex;flex-direction:column;gap:6px">
<div class="row" style="justify-content:space-between">{sq(i,t,True,15)}<span class="fa">{ic("chevron-right",15)}</span></div><b style="font-size:24px;letter-spacing:-.02em;line-height:1">{n}</b><span class="mut" style="font-size:12px;line-height:1.25">{l}</span></div>'''
                   for i, t, n, l in [("circle-dot", "gray", "16", "несортованих · найдовше 2 год"), ("truck", "blue", "3", "прийняті без ТТН"), ("alarm-clock", "red", "2", "нагадування настали"), ("package", "orange", "4", "на пошті > 3 дн")])
    rem = "".join(f'<div class="row" style="padding:9px 0;border-top:1px solid #F0F0EE"><b style="width:44px;font-size:14px;{"color:#B91C1C" if late else ""}">{t}</b><span style="flex:1;min-width:0;line-height:1.25"><b style="font-weight:500">{n}</b><br><small class="mut">{a}</small></span><span class="ibx" style="width:40px;height:40px">{ic("phone",17)}</span></div>'
                  for t, n, a, late in [("11:30", "Ірина Савчук", "№41 · уточнити колір", True), ("14:00", "Денис Мельник", "№38 · посилка на пошті", False), ("18:00", "Андрій Мельник", "№43 · після роботи", False)])
    body = f'''<div class="hd" style="padding-bottom:8px"><span class="rb" style="background:#E3E9F7;color:#3557A8;font-weight:600">А</span><div style="margin-right:auto;line-height:1.2"><small class="mut" style="font-size:12.5px">Вівторок, 3 листопада</small><br><b style="font-size:17px">Привіт, Олено</b></div>{rb("search")}{rb("bell","",'<em>2</em>')}</div>
<div class="row" style="padding:0 18px 8px;gap:8px"><b style="font-size:16px">Що зробити зараз</b>{mk(1)}</div>
<div style="display:flex;gap:8px;padding:0 14px 12px;overflow:hidden">{todo}</div>
<div style="margin:0 14px 10px;background:#1E1E22;border-radius:20px;padding:13px 16px;color:#fff;display:flex;align-items:center;gap:12px">
<div style="flex:1"><span style="color:#B7B7BC;font-size:12.5px">Продано сьогодні · 5 замовлень</span><div style="font-size:28px;font-weight:600;letter-spacing:-.03em;line-height:1.2">18 896 <span style="font-size:18px;color:#9E9EA3">₴</span></div></div>
<svg width="96" height="34"><path d="M2,26 L16,22 L30,25 L44,16 L58,19 L72,10 L94,5" fill="none" stroke="#4ADE80" stroke-width="2.4" stroke-linecap="round"/></svg></div>
<div class="c"><h3>{sq("alarm-clock","red",True,15)}Мої нагадування{mk(2)}<span class="r">усі</span></h3>{rem}</div>{bar("home")}'''
    return scr(body)


# ---------------------------------------------------------------- 3–5. Замовлення
def order_c(s, no, t, nm, sm, g, more, dl, act, swiped=False):
    acts = {"p": f'<span class="go p">{ic("check",15)}Прийняти</span>', "s": f'<span class="go s">{ic("truck",15)}ТТН</span>', "o": f'<span class="go">{ic("eye",15)}Відкрити</span>'}[act]
    card = f'''<div class="c" style="padding:11px 13px;margin:0;position:relative;{"transform:translateX(96px)" if swiped else ""}"><div class="row" style="gap:7px">{st(s)}<span class="fa" style="margin-left:auto;font-size:12.5px">№{no} · {t}</span></div>
<div class="row" style="margin-top:6px;justify-content:space-between"><b style="font-size:16px">{nm}</b><b style="font-size:16px">{sm} ₴</b></div>
<div class="row" style="margin-top:4px;font-size:13px;gap:6px"><span class="mut" style="flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{g} <span class="fa">{more}</span></span>{dl}</div>
<div class="row" style="gap:6px;margin-top:9px"><span class="go" style="flex:0 0 44px">{ic("phone",15)}</span>{acts}</div></div>'''
    if swiped:
        return f'<div style="position:relative;margin:0 14px 8px;border-radius:20px;background:#16A34A;overflow:hidden"><div style="position:absolute;left:0;top:0;bottom:0;width:96px;display:grid;place-items:center;color:#fff;font-weight:600;font-size:13px;text-align:center">{ic("check",22,2.4)}<br>Прийняти</div>{card}</div>'
    return f'<div style="margin:0 14px 8px">{card}</div>'


NP = lambda c: f'<span class="np">НП</span><span class="mut" style="font-size:12.5px">{c}</span>'


def orders():
    body = f'''{head("Замовлення", rb("search") + rb("list-filter", "", '<span class="dot"></span>'))}
<div class="row" style="padding:0 18px 10px;gap:8px;margin-top:-4px"><span class="chip" style="height:40px;padding:0 14px;font-size:14.5px;background:#7C7B76;color:#fff;border:0">Несортовані <b style="opacity:.8">16</b>{ic("chevron-down",15)}</span>{mk(3)}
<span class="mut" style="font-size:12.5px;margin-left:auto">3 до відправки · 13 у дорозі</span></div>
{order_c("uns","44","17:10","Олена Коваль","1 899","Бездротовий мікрофон","",NP("Київ, №12"),"p", True)}
{order_c("uns","43","17:00","Андрій Мельник","2 000","Набір капсул 50 шт","+1",'<span class="fa" style="font-size:12.5px">без доставки</span>',"p")}
{order_c("acc","42","16:37","Микола Бондаренко","3 899","Радіосистема DJI Mic 2","",NP("Львів, №5"),"s")}
{order_c("sent","40","15:50","Тарас Ткаченко","5 499","Екшн-камера 4К","",NP("Одеса, №31"),"o")}
{mk(4,"left:340px;top:330px")}{mk(5,"left:8px;top:150px")}{bar("orders")}'''
    return scr(body)


CHK = f"<span style=color:var(--acc);margin-left:10px>{ic('check',18)}</span>"


def status_sheet():
    rows = "".join(f'<div class="row" style="height:52px;padding:0 4px;border-top:{"0" if k == 0 else "1px solid #ECECE9"}"><span class="st" style="--c:{c};height:28px;font-size:14px"><i></i>{n}</span><b style="margin-left:auto;font-size:15px">{q}</b>{CHK if on else "<span style=width:28px></span>"}</div>'
                   for k, (n, q, c, on) in enumerate([("Несортовані", 16, "#7C7B76", True), ("Прийняті", 3, "#2E6BE6", False), ("Відправлені", 13, "#6D5BD0", False), ("Очікує на пошті", 5, "#D97706", False),
                                                       ("Завершені", 68, "#16A34A", False), ("Відмова", 7, "#DC2626", False), ("Усі", 126, "#1F1F1C", False)]))
    body = f'''{head("Замовлення", rb("search") + rb("list-filter"))}<div class="dim"></div>
<div class="sheet"><div class="grab"></div><h2>Статус<span class="x fa">{ic("x",20)}</span></h2><div style="background:#fff;border-radius:18px;padding:2px 12px">{rows}</div></div>'''
    return scr(body)


# ---------------------------------------------------------------- 6–8. Картка замовлення
def card():
    body = f'''<div class="row" style="padding:18px 14px 10px"><span class="rb">{ic("chevron-left",20)}</span><div style="flex:1;text-align:center;line-height:1.2"><b style="font-size:16px">Замовлення №44</b><br><small class="mut">сьогодні 17:10 · лендинг</small></div><span class="rb">{ic("ellipsis",20)}</span></div>
<div class="c" style="padding:12px 14px"><h3 style="margin-bottom:6px">{sq("package","blue",True,15)}Товари <small>2 · 2 198 ₴</small></h3>
{"".join(f'<div class="row" style="padding:8px 0;border-top:1px solid #F0F0EE;gap:10px"><span class="thumb" style="width:44px;height:44px">{ic("package",17)}</span><div style="flex:1;min-width:0;line-height:1.25"><b style="font-weight:500;font-size:14px">{n}</b><br><small class="mut"><span style="color:{sc}">●</span> {s} · {p} ₴</small></div><span class="row" style="gap:0;background:#F2F2F0;border-radius:13px"><span class="ibx" style="background:none">−</span><b style="width:18px;text-align:center">1</b><span class="ibx" style="background:none">+</span></span></div>' for n, s, sc, p in [("Бездротовий мікрофон", "142 шт", "#16A34A", "1 899"), ("Вітрозахист", "3 шт", "#D97706", "299")])}
<div class="mut" style="font-size:12px;margin-top:4px">Свайп ліворуч по товару — прибрати</div>{mk(7,"left:330px;top:120px")}</div>
<div class="c" style="padding:12px 14px">{mk(6,"left:330px;top:330px")}
<div class="row">{sq("credit-card","purple",False,16)}<div style="flex:1;line-height:1.3"><small class="mut">Оплата</small><br><b>Контроль оплати НП</b><br><small class="ok">{ic("check",12)} 2 198 ₴ при отриманні</small></div><span class="fa">{ic("pencil",17)}</span></div>
<div class="sep"></div>
<div class="row">{sq("truck","red",False,16)}<div style="flex:1;line-height:1.3"><small class="mut">Доставка</small><br><b>НП · Київ, №12</b><br><small class="mut">ТТН ще немає · ≈ 85 ₴, завтра</small></div><span class="fa">{ic("pencil",17)}</span></div></div>
<div class="c" style="padding:12px 14px"><h3 style="margin-bottom:8px">Деталі{mk(8)}<span class="r">змінити</span></h3>
<div class="row" style="gap:6px;flex-wrap:wrap">{"".join(f'<span class="chip" style="height:30px;background:#F2F2F0;border:0">{a}</span>' for a in ["Лендинг", "Олена Литвин", "Відділ Київ", "ФОП Петренко"])}</div>
<div class="inp b" style="margin-top:10px;height:44px">Коментар до замовлення</div></div>
<div class="sticky"><span class="btn" style="width:54px;flex:none">{ic("phone",20)}</span><span class="btn p" style="flex:1">{ic("check",18)}Прийняти замовлення</span></div>'''
    return scr(body)


# ---------------------------------------------------------------- 9–10. Ліди
def leads():
    def lc(n, g, w, wc, tries, s, open_=False):
        dots = "".join(f'<i style="width:8px;height:8px;border-radius:50%;background:{"#D97706" if j < tries else "#E3E3DF"};display:inline-block"></i>' for j in range(3))
        res = f'<div class="row" style="gap:6px;margin-top:10px"><span class="go">{ic("phone-missed",15)}Не відповів</span><span class="go v" style="flex:0 0 44px">{ic("clock",16)}</span><span class="go g" style="flex:0 0 44px">{ic("check",16)}</span></div>' if open_ else ""
        return f'''<div class="c" style="padding:12px 14px;margin:0 14px 8px"><div class="row" style="gap:12px">{ring(w[0],w[1],min(1,w[2]),wc,52,4.5,14)}
<div style="flex:1;min-width:0;line-height:1.3">{st(s)}<br><b style="font-size:16px">{n}</b><br><small class="mut">{g}</small> <span style="margin-left:4px">{dots}</span></div><span class="ibx" style="background:var(--acc);color:#fff;width:48px;height:48px;border-radius:15px">{ic("phone",20)}</span></div>{res}</div>'''
    body = f'''{head("Ліди", rb("search") + rb("plus"))}
{tabs([("Нові", 5, "#2E6BE6", True), ("Недодзвон", 3, "#D97706", False), ("Передзвонити", 2, "#7C3AED", False)])}
{lc("Олена Шевчук","Мультиварка Redmond",("22","хв",.6),"#D97706",1,"new",True)}
{lc("Петренко Іван","Кавоварка Delonghi",("4","хв",.2),"#16A34A",0,"new")}
{lc("Сергій Коваль","Пилосос Xiaomi G10",("1","год",1),"#DC2626",2,"no")}
{lc("Марія Ткач","Блендер Philips",("3","год",1),"#DC2626",3,"no")}
{mk(9,"left:340px;top:250px")}{bar("leads")}'''
    return scr(body)


def new_lead():
    body = f'''{head("Ліди", rb("search") + rb("plus"))}<div class="dim"></div>
<div class="sheet"><div class="grab"></div><h2>Новий лід{mk(10)}<span class="x fa">{ic("x",20)}</span></h2>
<div class="lab">Телефон</div><div class="inp" style="border:1.5px solid var(--acc)"><span>🇺🇦</span><b>+380 67 ___ __ __</b></div>
<div class="lab" style="margin-top:12px">Ім'я</div><div class="inp">Як звати покупця</div>
<div class="lab" style="margin-top:12px">Джерело</div><div class="row" style="flex-wrap:wrap;gap:7px">{"".join(f'<span class="chip" style="height:40px;padding:0 14px;font-size:14px">{a}</span>' for a in ["Маркетплейси", "Сайти", "Соцмережі", "Інше"])}</div>
<span class="btn p" style="margin-top:16px;height:54px">{ic("plus",18)}Додати лід</span></div>'''
    return scr(body)


# ---------------------------------------------------------------- 11. Покупці
def customers():
    def cc(n, seg, sc, b, bc, o, s, last):
        return f'''<div class="c" style="padding:11px 13px;margin:0 14px 8px"><div class="row" style="gap:11px">{ring(f"{b}" if b else "—","",(b or 0)/100 or .001,bc,46,4,12)}
<div style="flex:1;min-width:0;line-height:1.3"><b style="font-size:15.5px">{n}</b><br><span class="st" style="--c:{sc};height:22px;font-size:12px"><i></i>{seg}</span> <small class="mut">{o} замовл. · {s}</small></div>
<span class="ibx" style="width:42px;height:42px">{ic("phone",17)}</span></div></div>'''
    body = f'''{head("Покупці", rb("search") + rb("plus","p"), "1 284 · 312 постійних · 41 ризик")}
<div class="row" style="padding:0 18px 12px;gap:7px;overflow:hidden;white-space:nowrap">{"".join(f'<span class="chip{" on" if on else ""}" style="height:36px"><i style="width:7px;height:7px;border-radius:50%;background:{c};display:inline-block"></i>{n}</span>' for n, c, on in [("Усі", "#1F1F1C", True), ("VIP", "#A16207", False), ("Постійні", "#16A34A", False), ("Ризик", "#DC2626", False), ("Нові", "#2E6BE6", False)])}{mk(11)}</div>
{cc("Олена Коваль","Постійна","#16A34A",92,"#16A34A",7,"12 480 ₴","сьогодні")}{cc("Микола Бондаренко","VIP","#A16207",100,"#16A34A",14,"41 300 ₴","16:37")}
{cc("Світлана Олійник","Ризик відмови","#DC2626",33,"#DC2626",3,"4 197 ₴","учора")}{cc("Андрій Мельник","Новий","#2E6BE6",0,"#C9C8C3",1,"2 000 ₴","сьогодні")}
{cc("Роман Кравченко","Повторний","#7C3AED",67,"#D97706",3,"1 794 ₴","27.10")}{bar("more")}'''
    return scr(body)


# ---------------------------------------------------------------- 12. Товари
def products():
    def pc(n, p, m, mc, have, days, dc, w):
        return f'''<div class="row" style="padding:10px 0;border-top:1px solid #F0F0EE;gap:11px"><span class="thumb" style="width:46px;height:46px">{ic("package",18)}</span>
<div style="flex:1;min-width:0;line-height:1.3"><b style="font-weight:500;font-size:14.5px">{n}</b><br><small><b>{p} ₴</b> · <span style="color:{mc}">маржа {m}</span></small>
<div class="row" style="gap:8px;margin-top:5px"><div class="bar2" style="flex:1"><i style="width:{w}%;background:{dc}"></i></div><small style="color:{dc};font-weight:500;white-space:nowrap">{have} · {days}</small></div></div></div>'''
    body = f'''{head("Товари", rb("plus","p"))}
<div class="row" style="padding:0 14px 10px;gap:8px"><div class="inp" style="flex:1">{ic("search",17)}Назва, артикул або модель</div><span class="rb" style="width:46px;height:46px;border-radius:14px">{ic("list-filter",19)}<span class="dot"></span></span>{mk(12)}</div>
<div class="row" style="padding:0 14px 10px;gap:7px">{"".join(f'<span class="chip{" on" if on else ""}">{n}</span>' for n, on in [("Усі 13", True), ("Закінчуються 3", False), ("Немає 1", False)])}</div>
<div class="c" style="padding:4px 14px">{pc("Бездротовий мікрофон","1 899","42%","#15803D","142 шт","≈ 2 міс","#16A34A",70)}{pc("Кільцева лампа 26 см","899","51%","#15803D","18 шт","≈ 6 днів","#D97706",12)}
{pc("Штатив-монопод","699","18%","#A85A04","3 шт","≈ 1 день","#DC2626",3)}{pc("Чохол MagSafe","449","62%","#15803D","9 шт","≈ 4 дні","#D97706",8)}{pc("Павербанк Volt 20 000","1 999","31%","#15803D","77 шт","≈ 3 тиж","#16A34A",38)}</div>{bar("more")}'''
    return scr(body)


# ---------------------------------------------------------------- 13. Оплати
def payments():
    rows = "".join(f'<div class="row" style="height:56px;border-top:1px solid #F0F0EE;gap:12px"><span class="cb{" on" if on else ""}" style="width:26px;height:26px;border-radius:8px">{ic("check",15,2.6) if on else ""}</span><div style="flex:1;min-width:0;line-height:1.25"><b style="font-weight:500">{n}</b><br><small class="mut">№{no} · оплачено 30.10</small></div><b>{s} ₴</b></div>'
                   for n, no, s, on in [("Гончаренко Сергій", 137, "649", True), ("Захарченко Анна", 135, "649", True), ("Бондаренко Ігор", 116, "649", False), ("Руденко Василь", 66, "649", False), ("Савченко Ірина", 62, "399", False)])
    body = f'''{head("Оплати", rb("search") + rb("upload"))}
<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:0 14px 10px">{"".join(f'<div class="c" style="margin:0;padding:11px 13px">{sq(i,t,True,15)}<div style="font-size:20px;font-weight:600;margin-top:6px;letter-spacing:-.02em">{v}</div><small class="mut">{l}</small></div>' for i, t, v, l in [("hand-coins","orange","23 490 ₴","у дорозі"), ("banknote","blue","5 469 ₴","оплатили клієнти")])}</div>
<div class="c" style="padding:4px 14px 6px"><div class="row" style="height:46px"><b>Оплатили клієнти</b><span class="mut">10</span><span style="margin-left:auto" class="ac">вибрати всі</span></div>{rows}</div>
<div class="sticky" style="bottom:0">{mk(13,"left:8px;top:-8px")}<span class="btn p" style="flex:1">{ic("check",18)}Гроші отримано · 2 на 1 298 ₴</span></div>'''
    return scr(body)


# ---------------------------------------------------------------- 14. Дошка
def board():
    cards = "".join(f'<div class="c" style="margin:0 0 8px;padding:11px 13px"><div class="row" style="justify-content:space-between"><b style="font:600 12.5px JB">№{no}</b><small class="fa">{t}</small></div><b style="font-size:15px">{n}</b><br><small class="mut">{g}</small><div class="row" style="justify-content:space-between;margin-top:6px"><b>{s} ₴</b><span class="np">НП</span></div></div>'
                    for no, t, n, g, s in [("44", "щойно", "Олена Коваль", "Бездротовий мікрофон", "1 899"), ("43", "16 хв", "Андрій Мельник", "Набір капсул 50 шт", "2 000"), ("39", "1 год", "Світлана Олійник", "Штатив-монопод", "2 797"), ("37", "2 год", "Олег Бондаренко", "Павербанк", "1 999")])
    body = f'''{head("Дошка", rb("search"))}
<div class="row" style="padding:0 18px 10px;gap:7px;white-space:nowrap;overflow:hidden">{"".join(f'<span class="st" style="--c:{c};height:34px;font-size:13.5px;padding:0 12px;{"background:"+c+";color:#fff" if on else ""}"><i style="{"background:#fff" if on else ""}"></i>{n} {q}</span>' for n, q, c, on in [("Несортовані", 16, "#7C7B76", True), ("Прийняті", 3, "#2E6BE6", False), ("Відправлені", 13, "#6D5BD0", False)])}{mk(14)}</div>
<div style="padding:0 14px">{cards}</div>
<div class="row" style="justify-content:center;gap:5px;position:absolute;left:0;right:0;bottom:92px">{"".join(f'<i style="width:{18 if k == 0 else 6}px;height:6px;border-radius:99px;background:{"#1F1F1C" if k == 0 else "#CFCEC9"}"></i>' for k in range(6))}</div>
{bar("more")}'''
    return scr(body)


# ---------------------------------------------------------------- 15. Статистика
def stats():
    t = lambda l, v, d, up, sub: f'<div class="c" style="margin:0;padding:12px 13px"><div class="row" style="justify-content:space-between"><small class="mut">{l}</small><span class="st" style="--c:{"#16A34A" if up else "#DC2626"};height:22px;font-size:11.5px">{d}</span></div><div style="font-size:22px;font-weight:600;letter-spacing:-.02em;margin-top:4px">{v}</div><small class="mut">{sub}</small></div>'
    body = f'''{head("Статистика", rb("search"))}
<div class="row" style="padding:0 14px 10px;gap:7px"><span class="chip on">{ic("calendar",13)}30 днів</span><span class="chip">{ic("list-filter",13)}Фільтри</span>{mk(15)}</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:0 14px 10px">{t("Замовлення","1 752","↑ 92%",True,"без допродажів 1 709")}{t("Сума","3 809 589 ₴","↑ 87%",True,"сер. чек 2 174 ₴")}
{t("Апрув","41.6%","↑ 0.4 п.",True,"723 підтверджено")}{t("Викуп","87.7%","↑ 26 п.",True,"57 отримано · 8 відмов")}{t("Відправлено","419","↑ 134%",True,"24% від замовлень")}{t("Маржа","2 148 609 ₴","↑ 87%",True,"допродажі 2 767 ₴")}</div>{bar("more")}'''
    return scr(body)


# ---------------------------------------------------------------- 16. Налаштування: статуси і користувачі — список → шторка
def settings_list():
    rows = "".join(f'<div class="row" style="height:54px;border-top:{"0" if k == 0 else "1px solid #F0F0EE"}"><i style="width:12px;height:12px;border-radius:4px;background:{c};display:inline-block"></i><div style="flex:1;line-height:1.25"><b style="font-weight:500">{n}</b><br><small class="mut">{s}</small></div><span class="fa">{ic("chevron-right",17)}</span></div>'
                   for k, (n, s, c) in enumerate([("Новий", "ліди · без дії", "#2E6BE6"), ("Недодзвон", "ліди · без дії", "#D97706"), ("Несортований", "замовлення · без дії", "#7C7B76"), ("Прийнятий", "замовлення · резерв", "#2E6BE6"),
                                                   ("Відправлений", "замовлення · списання", "#6D5BD0"), ("Завершений", "замовлення · фінальний", "#16A34A"), ("Відмова", "замовлення · повернення", "#DC2626")]))
    body = f'''<div class="row" style="padding:18px 14px 10px"><span class="rb">{ic("chevron-left",20)}</span><div style="flex:1;line-height:1.2;margin-left:4px"><b style="font-size:20px">Статуси</b><br><small class="mut">торкніться, щоб змінити</small></div><span class="rb p">{ic("plus",20)}</span>{mk(16)}</div>
<div class="c" style="padding:2px 14px">{rows}</div>'''
    return scr(body)


def settings_sheet():
    body = f'''<div class="row" style="padding:18px 14px 10px"><span class="rb">{ic("chevron-left",20)}</span><b style="font-size:20px;margin-left:6px">Статуси</b></div><div class="dim"></div>
<div class="sheet"><div class="grab"></div><h2>Прийнятий<span class="x fa">{ic("x",20)}</span></h2>
<div class="lab">Назва</div><div class="inp"><b>Прийнятий</b></div>
<div class="lab" style="margin-top:12px">Колір</div><div class="row" style="gap:8px">{"".join(f'<i style="width:36px;height:36px;border-radius:11px;background:{c};display:inline-block;{"box-shadow:0 0 0 3px #fff,0 0 0 5px "+c if k == 0 else ""}"></i>' for k, c in enumerate(["#2E6BE6", "#16A34A", "#D97706", "#7C3AED", "#DC2626", "#7C7B76"]))}</div>
<div class="lab" style="margin-top:12px">Що робити зі складом</div><div class="seg"><span>Нічого</span><span class="on">Резерв</span><span>Списати</span></div>
<div class="row" style="margin-top:14px;justify-content:space-between"><span>Активний</span><span class="tgl on"></span></div>
<span class="btn p" style="margin-top:16px;height:54px">{ic("check",18)}Зберегти</span></div>'''
    return scr(body)


# ---------------------------------------------------------------- 17–18. Журнал і закупівлі
def journal():
    ev = "".join(f'<div class="row" style="padding:10px 0;border-top:{"0" if k == 0 else "1px solid #F0F0EE"};align-items:flex-start;gap:11px">{sq(i,t,True,14)}<div style="flex:1;line-height:1.3"><b style="font-weight:500">{a}</b><br><small class="mut">{b}</small></div><small class="fa">{c}</small></div>'
                 for k, (i, t, a, b, c) in enumerate([("check", "blue", "№2695 → Прийнятий", "Адміністратор", "13:11"), ("user-round", "gray", "Користувач «Максим» — роль", "Адміністратор", "13:10"),
                                                       ("truck", "orange", "№2650: створено ТТН", "Олена Литвин", "12:54"), ("message-square", "purple", "№2648: коментар", "Олена Литвин", "12:53"),
                                                       ("trash", "red", "№2611 видалено", "Адміністратор", "11:28"), ("check", "blue", "№2600 → Відправлений", "Максим", "11:24")]))
    body = f'''{head("Журнал дій", rb("search") + rb("list-filter"))}
<div class="row" style="padding:0 14px 10px;gap:7px"><span class="chip on">Сьогодні</span><span class="chip">Замовлення</span><span class="chip">Налаштування</span>{mk(17)}</div>
<div class="c" style="padding:4px 14px"><small class="mut" style="display:block;padding:8px 0 2px">Сьогодні, 3 листопада</small>{ev}</div>{bar("more")}'''
    return scr(body)


def purchases():
    pc = "".join(f'<div class="c" style="padding:12px 14px;margin:0 14px 8px"><div class="row" style="justify-content:space-between"><b style="font:600 12.5px JB">№{no} · {d}</b><span class="st" style="--c:{c}"><i></i>{s}</span></div><b style="font-size:15.5px;display:block;margin-top:5px">{sup}</b><div class="row" style="justify-content:space-between;margin-top:3px"><small class="mut">{g}</small><b>{sm} ₴</b></div></div>'
                 for no, d, s, c, sup, g, sm in [("12", "02.11", "Замовлено", "#2E6BE6", "ТОВ «Електро-Опт»", "3 товари · 120 шт", "48 600"), ("11", "28.10", "Оприбутковано", "#16A34A", "ФОП Коваль", "Чохол MagSafe · 200 шт", "21 000"), ("10", "20.10", "Чернетка", "#7C7B76", "ТОВ «Лампа»", "Кільцева лампа · 50 шт", "17 500")])
    body = f'''{head("Закупівлі", rb("search") + rb("plus","p"))}
<div class="row" style="padding:0 14px 10px;gap:7px">{"".join(f'<span class="chip{" on" if on else ""}">{n}</span>' for n, on in [("Усі", True), ("Чернетки", False), ("Замовлено", False), ("Оприбутковано", False)])}{mk(18)}</div>{pc}{bar("more")}'''
    return scr(body)


F = [
    ("1-golovna", "Головна", "Перше, що бачить менеджер, — що зробити зараз, а не графік продажів.", ["mob-01-головна.png"], [("Стане", home())], [
        (1, "«Що зробити зараз» — першим", "Плитки, що гортаються вбік: несортовані (скільки чекає найстаріше), без ТТН, нагадування, посилки на пошті понад 3 дні. Зараз «Потребує уваги» — аж під топом товарів."),
        (2, "Мої нагадування на сьогодні", "За часом, прострочені — червоним, з кнопкою дзвінка. Продажі дня — компактною смугою з лінією за тиждень.")]),
    ("2-zamovlennia", "Замовлення", "Зараз вкладки статусів обрізані («а на пошті»), підсумок — у два рядки, у картці немає дії.", ["mob-02-замовлення.png"], [("Стане", orders()), ("Стане · вибір статусу", status_sheet())], [
        (3, "Статус — одна кнопка зі шторкою", "«Несортовані 16 ▾» відкриває список усіх статусів з лічильниками. Нічого не обрізається, підсумок — одним рядком."),
        (4, "Дія прямо в картці", "Як на ПК: дзвінок і головна дія за станом — «Прийняти», «ТТН», «SMS», «Відкрити»."),
        (5, "Свайп по картці", "Вправо — прийняти, вліво — подзвонити. Скасувати можна з підказки внизу.")]),
    ("3-kartka", "Картка замовлення", "Зараз оплата й доставка — повні форми навіть для оформленого замовлення; деталі — довгий список полів.", ["mob-04-картка-нижче.png"], [("Стане", card())], [
        (6, "Оплата й доставка — підсумком", "Як на ПК: два рядки зі станом (скільки при отриманні, ціна й дата доставки). Олівець — розгорнути форму."),
        (7, "Товари: кнопки 44 px і свайп", "−/+ зараз дрібні (24 px). Стануть 44 px, «прибрати» — свайпом ліворуч, із залишком кольоровою крапкою."),
        (8, "Деталі — чипами", "Джерело, менеджер, відділ, юрособа — одним рядком; «змінити» відкриває поля.")]),
    ("4-lidy", "Ліди", "Зараз після дзвінка треба відкрити лід, щоб записати результат; «Новий лід» — вікно посередині екрана.", ["mob-12-ліди.png", "mob-14-новий-лід.png"], [("Стане", leads()), ("Стане · новий лід", new_lead())], [
        (9, "Результат дзвінка в картці", "Після дзвінка картка розгортається: «Не відповів», «Передзвонити» (час), «Оформити». Спроби — крапками."),
        (10, "Новий лід — шторкою знизу", "Поля й кнопка — під великим пальцем, клавіатура не закриває кнопку «Додати лід».")]),
    ("5-pokuptsi", "Покупці", "Зараз у кожній картці «0 ₴» і група «Покупець» — шум; вгорі групи, а не сегменти.", ["mob-16-покупці.png"], [("Стане", customers())], [
        (11, "Сегменти й кільце викупу", "Як на ПК: VIP, постійні, ризик, нові; викуп — кільцем, кнопка дзвінка в картці. Типову групу не підписуємо.")]),
    ("6-tovary", "Товари", "Зараз три поля фільтрів стиснуті в один рядок («Назва,», «Будь-який …»).", ["mob-18-товари.png"], [("Стане", products())], [
        (12, "Пошук на всю ширину, фільтри — шторкою", "Поле пошуку й кнопка фільтрів; швидкі чипи «Закінчуються», «Немає». Залишок — смужкою з прогнозом «на скільки днів».")]),
    ("7-oplaty", "Оплати", "Зараз заголовок групи — у три рядки, галочки дрібні, кнопка «Гроші отримано» не видна.", ["mob-23-оплати.png"], [("Стане", payments())], [
        (13, "Великі рядки й кнопка внизу", "Рядок 56 px, галочка 26 px, кнопка «Гроші отримано · 2 на 1 298 ₴» закріплена внизу.")]),
    ("8-doshka", "Дошка", "Зараз колонки 270 px — друга обрізана, перетягувати незручно.", ["mob-15-дошка.png"], [("Стане", board())], [
        (14, "Колонка на весь екран", "Свайп між колонками, вгорі — чипи статусів з лічильниками. Перенести — довгий натиск і вибір статусу.")]),
    ("9-statystyka", "Статистика", "Зараз плитки по три в ряд — «134.1%» і «62.1%» вилазять, фільтри обрізані.", ["mob-22-статистика.png"], [("Стане", stats())], [
        (15, "Плитки по дві й фільтри шторкою", "Дві колонки, однакова висота; період і фільтри — двома чипами.")]),
    ("10-nalashtuvannia", "Налаштування", "Зараз статуси й користувачі — довгі форми підряд (порядок, колір, назва… для кожного).", ["mob-26-налаштування-statuses.png"], [("Стане", settings_list()), ("Стане · редагування", settings_sheet())], [
        (16, "Список → шторка", "Статуси, користувачі, види оплат: короткий список (колір, назва, роль), торкання відкриває шторку з полями. Порядок — перетягуванням.")]),
    ("11-zhurnal", "Журнал і закупівлі", "Зараз це таблиці: у журналі обрізаний «Об'єкт», у закупівлях видно шапку таблиці.", ["mob-40-журнал.png", "mob-20-закупівлі.png"], [("Стане", journal()), ("Стане", purchases())], [
        (17, "Журнал — стрічкою подій", "Значок дії, що змінилось, хто й коли; групи за днями, чипи-фільтри."),
        (18, "Закупівлі — картками", "Номер, дата, статус, постачальник, товари й сума — як інші списки на телефоні.")]),
]


def build():
    frames = []
    for k, title, lead, bef, aft, items in F:
        w = 26 * 2 + (len(bef) + len(aft)) * (390 + 28) + 330
        frames.append((k, f"{title}", frame(title, lead, bef, aft, items), w, 930))
    return page("Мобільна версія — 18 покращень", CSS, frames, cols=1, gap=40)
