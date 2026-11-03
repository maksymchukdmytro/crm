"""Картка існуючого замовлення — 5 варіантів за правилами власника (31.10): сірий фон, білі картки без рамок, кольорові квадрати,
статус своїм кольором, одна синя дія («що далі»), без окремого «Зберегти» (зберігається само), товари — найбільший блок,
рядок товару низький, деталі: Джерело | Менеджер, Відділ | Юрособа, коментар на всю ширину; «Поля 1–4» і UTM згорнуто; телефон — першим."""
from common import *
from v18_desktop import CSS as BASE, frame, head, sq, st, ring

CSS = BASE + """
.w{position:absolute;left:24px;right:24px;top:20px;bottom:20px;background:var(--bg);border-radius:22px;display:flex;flex-direction:column;overflow:hidden}
.dim{position:absolute;inset:0;background:rgba(24,24,22,.36)}
.wh{display:flex;align-items:center;gap:12px;padding:12px 16px;background:#fff;flex:none}
.wb{flex:1;min-height:0;padding:12px;display:grid;gap:12px}
.gr{display:grid;grid-template-columns:30px minmax(0,1fr) auto 112px 86px 18px;align-items:center;gap:10px;height:44px;padding:0 10px;border-radius:12px;background:#F6F7F8}
.gr .nm{display:flex;align-items:center;gap:8px;min-width:0;white-space:nowrap}.gr .nm b{font-weight:500;overflow:hidden;text-overflow:ellipsis}
.gr.up{margin-left:26px;background:#FAFAFB}
.gr .t{width:30px;height:30px;border-radius:9px;background:#fff;display:grid;place-items:center;color:#9C9C98}
.vp{display:inline-flex;align-items:center;gap:5px;height:21px;padding:0 8px;border-radius:99px;background:var(--acc2);color:#1F4FB8;font-size:11.5px;font-weight:500;flex:none}.vp i{width:8px;height:8px;border-radius:3px;background:#151515}
.qty{display:flex;align-items:center;justify-content:space-between;height:28px;border-radius:99px;background:#fff;padding:0 10px;color:var(--faint)}.qty b{color:var(--ink)}
.gs{display:flex;align-items:center;gap:8px;height:40px;padding:0 14px;border-radius:12px;background:#F6F7F8;color:var(--faint);margin-top:8px}
.off2{display:flex;align-items:center;gap:8px;height:38px;padding:0 6px 0 12px;border-radius:12px;border:1px dashed #D6D6D3;color:var(--mut);margin-top:8px;font-size:12.5px}
.off2 b{color:var(--ink);font-weight:500}.off2 .add{margin-left:auto;height:28px;padding:0 10px;border-radius:99px;background:var(--acc2);color:var(--acc);display:flex;align-items:center;gap:4px;font-weight:500}
.dt.n{grid-template-columns:72px 1fr}.dt.n .cm{grid-column:2/-1}
.dt{display:grid;grid-template-columns:72px 1fr 72px 1fr;align-items:center;gap:8px 10px;font-size:13px}.dt>span{color:var(--mut)}
.dt .v{height:34px;border-radius:10px;background:#F6F7F8;display:flex;align-items:center;justify-content:space-between;padding:0 10px}
.dt .cm{grid-column:2/-1;height:48px;align-items:flex-start;padding-top:8px;color:var(--faint)}
.fold{display:flex;gap:16px;font-size:12.5px;color:var(--acc);margin-top:8px}.fold span{display:flex;align-items:center;gap:3px}
.sum{background:#EAF1FD;border-radius:18px;padding:16px 18px;display:flex;flex-direction:column}
.sum .big{font-size:32px;font-weight:600;letter-spacing:-.02em;color:#1F4FB8;line-height:1.1}.sum .kv span{color:#4B5B7C}
.trk{display:flex;align-items:center;gap:2px}
.tp{height:32px;padding:0 11px;border-radius:99px;display:inline-flex;align-items:center;gap:5px;font-size:12.5px;font-weight:500;background:#F6F7F8;color:#57564F;white-space:nowrap}
.tp.done{background:#F0F0EE;color:var(--mut)}.tp.cur{background:var(--c,#2E6BE6);color:#fff}
.tl{width:12px;height:1px;background:#D6D6D3;flex:none}
.sv{display:inline-flex;align-items:center;gap:5px;font-size:12.5px;color:var(--ok)}
.tile{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:7px;height:84px;border-radius:16px;background:#fff;font-size:13px;font-weight:500}
.band{display:flex;align-items:center;gap:10px;height:48px;padding:0 16px;border-radius:16px;color:#fff;font-weight:600;font-size:15px}
.band small{margin-left:auto;font-weight:500;opacity:.85;font-size:13px;display:flex;align-items:center;gap:4px}
.nx{background:#fff;border-radius:18px;padding:16px;display:flex;flex-direction:column;gap:10px;box-shadow:inset 0 0 0 2px var(--acc3)}
.ck{display:flex;align-items:center;gap:10px;padding:6px 0;font-size:13.5px}.ck .o{width:20px;height:20px;border-radius:50%;border:1.5px solid #CFCEC9;display:grid;place-items:center;flex:none}
.ck .o.on{background:var(--ok);border-color:var(--ok);color:#fff}.ck.dn span{color:var(--faint);text-decoration:line-through}.ck a{margin-left:auto;color:var(--acc);font-size:12.5px;font-weight:500}
.pill{display:flex;align-items:center;gap:8px;height:40px;border-radius:12px;background:#F6F7F8;padding:0 12px;font-size:13.5px}
.stp{width:24px;height:24px;border-radius:50%;display:grid;place-items:center;background:#16A34A;color:#fff;flex:none}
"""

ST_ORDER = [("Несортований", "#7C7B76"), ("Прийнятий", "#2E6BE6"), ("Відправлений", "#6D5BD0"), ("На пошті", "#D97706"), ("Завершений", "#16A34A")]


def track(cur=1):
    out = []
    for k, (n, c) in enumerate(ST_ORDER):
        cls = "done" if k < cur else "cur" if k == cur else ""
        out.append(f'{"<i class=tl></i>" if k else ""}<span class="tp {cls}" style="--c:{c}">{ic("check",13,2.6) if k <= cur else ""}{n}</span>')
    return f'<div class="trk">{"".join(out)}<span class="tp" style="margin-left:6px">{ic("ellipsis",15)}</span></div>'


def topbar(primary=("truck", "Створити ТТН"), cur=1, extra=""):
    return f'''<div class="wh"><span class="rb" style="background:#F2F3F5">{ic("chevron-left",19)}</span>
<div class="col" style="flex:none;white-space:nowrap;line-height:1.25"><b style="font-size:17px">Замовлення №46</b><small class="mut">30.10, 22:33 · Prom Antony Store</small></div>
<div style="margin-left:14px">{track(cur)}</div><span style="flex:1"></span>{extra}
<span class="sv">{ic("circle-check-big",15)}Збережено</span>
<span class="rb" style="background:#F2F3F5">{ic("printer",18)}</span><span class="rb" style="background:#F2F3F5">{ic("receipt",18)}</span><span class="rb" style="background:#F2F3F5">{ic("bell",18)}</span><span class="rb" style="background:#F2F3F5">{ic("clock-fading",18)}<em>5</em></span>
{f'<span class="btn p">{ic(primary[0],17)}{primary[1]}</span>' if primary else ""}</div>'''


def goods(title=True, h3=True):
    rows = f'''<div class="gr"><span class="t">{ic("package",15)}</span><span class="nm"><b>Тест · Бездротовий мікрофон</b><span class="vp"><i></i>Чорний{ic("chevron-down",11)}</span></span><span class="fa mono" style="font-size:12px">TEST-01 · 99 шт</span>
<span class="qty"><span>−</span><b>1</b><span>+</span></span><b class="num" style="text-align:right">1 899 ₴</b><span class="fa">{ic("x",14)}</span></div>
<div class="gr up" style="margin-top:6px"><span class="t">{ic("link",14)}</span><span class="nm"><span class="st" style="--c:#7C3AED;height:19px;font-size:11px">допродаж</span><b>Чохол для мікрофона</b></span><span></span>
<span class="qty"><span>−</span><b>1</b><span>+</span></span><b class="num" style="text-align:right">199 ₴</b><span class="fa">{ic("x",14)}</span></div>
<div class="gs">{ic("search",15)}Додати товар: назва, артикул або штрихкод</div>
<div class="off2">{ic("sparkles",14)}Часто беруть разом: <b>Адаптер Lightning</b> · 349 ₴ · <b>Карта пам'яті 64 ГБ</b> · 399 ₴<span class="add">{ic("plus",13)}Додати</span></div>'''
    hdr = f'<h3>{sq("package","purple",True,14)}Товари<small>2 позиції</small><span class="r" style="display:flex;gap:6px"><span class="btn sm g">{ic("plus",14)}Товар</span><span class="btn sm g">{ic("plus",14)}Допродаж</span></span></h3>' if h3 else ""
    foot = '<div class="sep"></div><div class="row" style="gap:22px;font-size:13px"><span><span class="mut">Знижка</span> <b>0 ₴</b></span><span><span class="mut">Собівартість · прибуток</span> <b>1 250 ₴ · <span class="ok">848 ₴</span></b></span><span style="margin-left:auto"><span class="mut">Разом</span> <b style="font-size:18px">2 098 ₴</b></span></div>'
    return hdr + rows + foot


def customer(stats=True):
    s = f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:12px">{"".join(f"<div style=background:#F6F7F8;border-radius:12px;padding:8px 9px;line-height:1.2><b style=font-size:15px>{v}</b><br><small class=mut style=font-size:11px>{l}</small></div>" for v, l in [("4", "замовл."), ("—", "викуп"), ("0", "відмов"), ("0 ₴", "сума")])}</div>' if stats else ""
    return f'''<div class="row"><span class="av l">МД</span><div class="col" style="flex:1;line-height:1.3"><span class="mut num" style="font-size:13px">+380 73 037 77 57</span><b style="font-size:17px">Максимчук Дмитро</b></div><span class="rb" style="width:32px;height:32px;background:#F2F3F5">{ic("pencil",14)}</span></div>
<div class="msg" style="margin-top:12px"><span class="p">{ic("phone",17)}</span><span>{ic("message-circle",17)}</span><span>{ic("send",17)}</span><span>{ic("message-square",17)}</span></div>{s}
<div class="row" style="margin-top:10px;background:#FDF1E3;color:#A85A04;border-radius:12px;padding:8px 12px;font-size:12.5px">{ic("copy",14)}Можливий дубль №45<span style="margin-left:auto;font-weight:600">Відкрити</span></div>'''


def payment():
    return f'''<h3>{sq("wallet","green",True,14)}Оплата<span class="r">+ Оплата</span></h3>
<div class="pill"><span class="sq sm" style="width:24px;height:24px;border-radius:50%;--s:#16A34A;--i:#fff;font-size:10px"><b>R</b></span>Післяплата Rozetka<span style="margin-left:auto" class="fa">{ic("chevron-down",14)}</span></div>
<div class="row" style="margin-top:8px;background:#EAF1FD;color:#1F4FB8;border-radius:12px;padding:9px 12px;font-size:13px;gap:6px">{ic("arrow-up-right",14)}У ТТН піде: <b>післяплата · 2 098 ₴</b></div>'''


def delivery():
    return f'''<h3>{sq("truck","blue",True,14)}Доставка</h3>
<div class="row" style="background:#F6F7F8;border-radius:14px;padding:10px 12px">{sq("truck","orange",True,14)}<div class="col" style="flex:1;line-height:1.3"><b style="font-weight:500">Укрпошта</b><small class="mut">Тим, рийр · індекс не вказано</small></div>{ic("chevron-right",16)}</div>
<div class="row" style="gap:8px;margin-top:10px"><span class="btn s" style="flex:1">{ic("truck",16)}Створити ТТН</span><span class="btn g" style="width:42px;padding:0">{ic("ellipsis",16)}</span></div>'''


def details(narrow=False):
    v = lambda t, e=False: f'<span class="v{" e" if e else ""}">{t}<span class="fa">{ic("chevron-down",13)}</span></span>'
    return f'''<h3>{sq("list","gray",True,14)}Деталі</h3>
<div class="dt{" n" if narrow else ""}"><span>Джерело</span>{v("Prom Antony Store")}<span>Менеджер</span>{v("Іван")}<span>Відділ</span><span class="v" style="background:none;padding:0">Маркетплейси</span><span>Юрособа</span>{v("ФОП Максимчук О. В.")}
<span>Коментар</span><span class="v cm">Коментар до замовлення…</span><span>Позначка</span><span class="v" style="{"" if narrow else "grid-column:2/3"}">—<span class="fa">{ic("chevron-down",13)}</span></span></div>
<div class="fold"><span>Поля 1–4{ic("chevron-down",12)}</span><span>UTM і сайт{ic("chevron-down",12)}</span></div>'''


def summary(btn=False):
    return f'''<div class="mut" style="color:#4B5B7C;font-size:12.5px">До сплати при отриманні</div><div class="big">2 098 ₴</div>
<div class="kv" style="margin-top:8px"><span>Товари</span><b>2 098 ₴</b></div><div class="kv"><span>Оплата</span><b>Післяплата Rozetka</b></div><div class="kv"><span>Доставка</span><b>Укрпошта</b></div>
{f'<span style="flex:1"></span><span class="btn p" style="margin-top:12px">{ic("truck",17)}Створити ТТН</span>' if btn else ""}'''


def todo():
    items = [("Прийняти замовлення", True, ""), ("Товар зарезервовано", True, ""), ("Створити ТТН", False, "Створити"), ("Видаткова накладна", False, "Видати"), ("Чек", False, "Пробити")]
    return "".join(f'<div class="ck{" dn" if d else ""}"><span class="o{" on" if d else ""}">{ic("check",11,3) if d else ""}</span><span>{t}</span>{f"<a>{a}</a>" if a and not d else ""}</div>' for t, d, a in items)


def history():
    return "".join(f'<div class="row" style="align-items:flex-start;padding:6px 0;gap:10px">{sq(i,t,True,13)}<div class="col" style="flex:1;line-height:1.3"><span>{a}</span><small class="fa">{w}</small></div></div>'
                   for i, t, a, w in [("check", "blue", "Статус «Прийнятий» · Іван", "сьогодні 07:12"), ("receipt-text", "gray", "Замовлення створено · Prom", "30.10, 22:33")])


def win(top, body):
    return f'<div class="dim"></div><div class="w">{top}{body}</div>'


# ---------------------------------------------------------------- A. Три колонки: покупець | товари й оплата | доставка й «що далі»
def A():
    body = f'''<div class="wb" style="grid-template-columns:330px 1fr 320px">
<div class="col" style="gap:12px"><div class="c">{customer()}</div><div class="c" style="flex:1">{details(True)}</div></div>
<div class="col" style="gap:12px;min-width:0"><div class="c" style="flex:1">{goods()}</div><div class="c">{payment()}</div></div>
<div class="col" style="gap:12px"><div class="c">{delivery()}</div><div class="c" style="flex:1"><div class="row" style="gap:12px;margin-bottom:6px">{ring("2/5","",.4,"#16A34A",46,4.5,12)}<div class="col"><b style="font-size:15px">Що лишилось</b><small class="mut">3 кроки до відправки</small></div></div>{todo()}</div>
<div class="sum">{summary()}</div></div></div>'''
    return frame("orders", head("Замовлення"), win(topbar(), body))


# ---------------------------------------------------------------- B. Шапка-покупець, товари на 2/3, праворуч стос карток
def B():
    hero = f'''<div class="c row" style="grid-column:1/-1;gap:16px;padding:14px 18px"><span class="av l">МД</span><div class="col" style="line-height:1.3"><span class="mut num">+380 73 037 77 57</span><b style="font-size:18px">Максимчук Дмитро</b></div>
<div class="msg" style="width:200px;margin-left:8px"><span class="p">{ic("phone",16)}</span><span>{ic("message-circle",16)}</span><span>{ic("send",16)}</span><span>{ic("message-square",16)}</span></div>
<div class="row" style="gap:18px;margin-left:14px;font-size:13px">{"".join(f"<span class=col style=line-height:1.2><b style=font-size:16px>{v}</b><small class=mut>{l}</small></span>" for v, l in [("4", "замовлень"), ("—", "викуп"), ("0", "відмов")])}</div>
<span class="row" style="margin-left:auto;background:#FDF1E3;color:#A85A04;border-radius:12px;padding:8px 12px;font-size:12.5px">{ic("copy",14)}Можливий дубль №45 · <b>Відкрити</b></span>
<div class="col" style="text-align:right;line-height:1.15;margin-left:12px"><small class="mut">до сплати</small><b style="font-size:24px;color:#1F4FB8">2 098 ₴</b></div></div>'''
    body = f'''<div class="wb" style="grid-template-columns:1fr 360px;grid-template-rows:auto 1fr">{hero}
<div class="col" style="gap:12px;min-width:0"><div class="c" style="flex:1">{goods()}</div><div class="c">{details()}</div></div>
<div class="col" style="gap:12px"><div class="c">{payment()}</div><div class="c">{delivery()}</div><div class="c" style="flex:1"><b style="font-size:15px">Що лишилось · 2 з 5</b>{todo()}</div></div></div>'''
    return frame("orders", head("Замовлення"), win(topbar(), body))


# ---------------------------------------------------------------- C. Стрічка кроків (як майстер) і праворуч підсумок
def C():
    sec = lambda n, t, s, inner, done=True: f'<div class="c"><div class="row" style="margin-bottom:10px"><span class="stp" style="{"" if done else "background:#ECEDEF;color:#8A8984"}">{ic("check",13,3) if done else n}</span><b style="font-size:16px">{t}</b><small class="mut">{s}</small></div>{inner}</div>'
    body = f'''<div class="wb" style="grid-template-columns:1fr 340px;overflow:hidden">
<div class="col" style="gap:12px;min-width:0;overflow:hidden">
{sec(1,"Покупець","+380 73 037 77 57 · 4 замовлення",f'<div class="row" style="gap:12px"><span class="av">МД</span><b style="font-size:16px;flex:1">Максимчук Дмитро</b><div class="msg" style="width:200px"><span class="p">{ic("phone",16)}</span><span>{ic("message-circle",16)}</span><span>{ic("send",16)}</span><span>{ic("message-square",16)}</span></div></div>')}
{sec(2,"Товари","2 позиції · 2 098 ₴",goods(h3=False))}
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">{sec(3,"Оплата","Післяплата Rozetka",payment().split("</h3>",1)[1])}{sec(4,"Доставка","ТТН ще немає",delivery().split("</h3>",1)[1],False)}</div></div>
<div class="col" style="gap:12px"><div class="sum" style="flex:none">{summary(True)}</div><div class="c">{details(True)}</div><div class="c" style="flex:1"><b style="font-size:15px">Історія</b>{history()}</div></div></div>'''
    return frame("orders", head("Замовлення"), win(topbar(), body))


# ---------------------------------------------------------------- D. «Що далі»: велика наступна дія праворуч, історія поруч
def D():
    nxt = f'''<div class="nx"><small class="mut">Наступний крок</small><b style="font-size:20px;letter-spacing:-.01em">Прийняти замовлення</b><span class="mut" style="font-size:13px">Товар зарезервується, далі — ТТН. Кнопка змінюється сама за статусом</span>
<span class="btn p" style="height:48px">{ic("check",18)}Прийняти замовлення<span style="font:500 11px JB;opacity:.7">Ctrl ⏎</span></span>
<div class="row" style="gap:8px"><span class="btn g sm" style="flex:1">{ic("printer",14)}Друк</span><span class="btn g sm" style="flex:1">{ic("receipt",14)}Чек</span><span class="btn g sm" style="flex:1">{ic("bell",14)}Нагадати</span></div></div>'''
    body = f'''<div class="wb" style="grid-template-columns:1fr 340px">
<div class="col" style="gap:12px;min-width:0">
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px"><div class="c">{customer(False)}</div><div class="c">{payment()}</div><div class="c">{delivery()}</div></div>
<div class="c" style="flex:1">{goods()}</div><div class="c">{details()}</div></div>
<div class="col" style="gap:12px">{nxt}<div class="c"><div class="row" style="gap:12px;margin-bottom:4px">{ring("2/5","",.4,"#16A34A",44,4.5,12)}<b style="font-size:15px">Що лишилось</b></div>{todo()}</div>
<div class="c" style="flex:1"><h3>{sq("clock-fading","gray",True,14)}Історія<span class="r">Усе</span></h3>{history()}<div class="inp e" style="margin-top:8px">Коментар для колег…</div></div></div></div>'''
    return frame("orders", head("Замовлення"), win(topbar(None, 0), body))


# ---------------------------------------------------------------- E. Як на телефоні: смуга статусу кольором, плитки дій, дві колонки
def E():
    hero = f'''<div class="c row" style="gap:14px;padding:14px 18px"><span class="av l">МД</span><div class="col" style="line-height:1.3;flex:1"><span class="mut num">+380 73 037 77 57</span><b style="font-size:18px">Максимчук Дмитро</b></div>
<div class="row" style="gap:18px;font-size:13px;margin-right:12px">{"".join(f"<span class=col style=line-height:1.2><b style=font-size:16px>{v}</b><small class=mut>{l}</small></span>" for v, l in [("4", "замовлень"), ("—", "викуп"), ("ФОП Максимчук", "юрособа")])}</div>
<div class="msg" style="width:220px"><span class="p">{ic("phone",16)}</span><span>{ic("message-circle",16)}</span><span>{ic("send",16)}</span><span>{ic("message-square",16)}</span></div>
<div class="col" style="text-align:right;line-height:1.15;margin-left:12px"><small class="mut">до сплати</small><b style="font-size:24px">2 098 ₴</b></div></div>'''
    tiles = "".join(f'<div class="tile">{sq(i,t,False,18)}{n}</div>' for i, t, n in [("truck", "blue", "ТТН"), ("printer", "gray", "Друк"), ("receipt", "green", "Чек"), ("bell", "orange", "Нагадати"), ("clock-fading", "purple", "Історія · 5")])
    body = f'''<div class="wb" style="grid-template-columns:1fr 380px;grid-template-rows:auto auto 1fr">
<div style="grid-column:1/-1">{hero}</div>
<div class="band" style="background:#2E6BE6">{ic("check",16,2.6)}Прийнятий<small>змінити{ic("chevron-down",14)}</small></div>
<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px">{tiles}</div>
<div class="col" style="gap:12px;min-width:0"><div class="c" style="flex:1">{goods()}</div><div class="c">{details()}</div></div>
<div class="col" style="gap:12px"><div class="c">{payment()}</div><div class="c">{delivery()}</div><div class="c" style="flex:1"><b style="font-size:15px">Що лишилось · 2 з 5</b>{todo()}</div></div></div>'''
    top = f'''<div class="wh"><span class="rb" style="background:#F2F3F5">{ic("chevron-left",19)}</span><div class="col" style="line-height:1.25"><b style="font-size:17px">Замовлення №46</b><small class="mut">30.10, 22:33 · Prom Antony Store</small></div>
<span style="flex:1"></span><span class="sv">{ic("circle-check-big",15)}Збережено</span><span class="rb" style="background:#F2F3F5">{ic("ellipsis",18)}</span><span class="btn p">{ic("truck",17)}Створити ТТН</span><span class="rb" style="background:#F2F3F5">{ic("x",18)}</span></div>'''
    return frame("orders", head("Замовлення"), win(top, body))


V = [("A", "A — три колонки: покупець і деталі · товари й оплата · доставка, «Що лишилось», підсумок", A()),
     ("B", "B — покупець шапкою на всю ширину, товари на 2/3, праворуч оплата, доставка, кроки", B()),
     ("C", "C — як майстер: кроки картками зверху вниз, праворуч підсумок із головною кнопкою", C()),
     ("D", "D — «Що далі»: велика наступна дія праворуч, під нею кроки й історія", D()),
     ("E", "E — як на телефоні: смуга статусу кольором, плитки дій, дві колонки", E())]


def build():
    return page("Картка замовлення — 5 варіантів", CSS, [(k, n, h, 1440, 900) for k, n, h in V], cols=2, gap=40)
