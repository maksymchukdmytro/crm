"""Мобільні версії варіантів 1, 3, 5, 6: по 4 телефони на кадр. Спільні деталі + змінні кольорів і форм кожного стилю."""
from common import *

BASE = """
.mob{--acc:#2D3FE7;--acc2:#EEF0FE;--ink:#14162B;--mut:#6B6F86;--line:#E6E8F0;--card:#fff;--sbg:#F5F6FA;--r:16px;--rs:10px;--prim:var(--acc);--primt:#fff;--bar:#fff;--bart:#9A9DB2;--baron:var(--acc);
  width:100%;height:100%;display:flex;align-items:center;justify-content:center;gap:28px;background:var(--mbg);color:var(--ink)}
.mob figure{display:flex;flex-direction:column;align-items:center;gap:14px}
.mob figcaption{font:600 14px 'Manrope',sans-serif;color:var(--capc,#2A2A2A)}
.mob .ph{width:300px;height:640px;border-radius:44px;background:#0C0C10;padding:9px;box-shadow:0 40px 60px -32px rgba(0,0,0,.5)}
.mob .scr{width:100%;height:100%;border-radius:36px;overflow:hidden;position:relative;display:flex;flex-direction:column;background:var(--sbg);font:var(--font)}
.mob .isl{width:88px;height:25px;border-radius:99px;background:#0C0C10;position:absolute;left:50%;top:9px;transform:translateX(-50%);z-index:9}
.mob .sbar{height:42px;flex:none;display:flex;align-items:center;justify-content:space-between;padding:0 24px;font-size:12.5px;font-weight:600}
.mob .bd{flex:1;min-height:0;padding:2px 14px 0;display:flex;flex-direction:column;gap:9px;overflow:hidden}
.mob .bd>*{flex-shrink:0}
.mob .tp{display:flex;align-items:center;gap:10px}.mob .tp .r{margin-left:auto;display:flex;gap:12px;align-items:center;color:var(--ink)}
.mob h2{font-size:22px;font-weight:700;letter-spacing:-.02em;line-height:1.15}.mob h3{font-size:14px;font-weight:700;display:flex;align-items:center;gap:6px}.mob h3 .r{margin-left:auto;font-weight:500;font-size:12px;color:var(--mut)}
.mob .mut{color:var(--mut);font-size:12px}
.mob .card{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:11px 12px}
.mob .chips{display:flex;gap:6px;overflow:hidden;flex:none}.mob .chips span{flex:none;height:28px;padding:0 11px;border-radius:99px;display:flex;align-items:center;gap:5px;font-size:12px;background:var(--card);border:1px solid var(--line);white-space:nowrap}
.mob .chips span.on{background:var(--ink);border-color:var(--ink);color:#fff}.mob .chips em{font-style:normal;opacity:.6}
.mob .row{display:flex;gap:10px;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:9px 11px;font-size:12.5px}
.mob .row b{display:block;font-weight:600;font-size:13px}.mob .row small{display:block;font-size:11.5px;color:var(--mut)}.mob .row .s{margin-left:auto;text-align:right;font-weight:700;white-space:nowrap}
.mob .st{display:inline-flex;align-items:center;gap:4px;height:20px;padding:0 7px;border-radius:7px;font-size:11px;font-weight:600;white-space:nowrap;background:color-mix(in srgb,var(--c) 13%,#fff);color:color-mix(in srgb,var(--c) 72%,#000)}
.mob .st i{width:6px;height:6px;border-radius:50%;background:var(--c)}
.mob .tab{height:74px;flex:none;background:var(--bar);border-top:1px solid var(--line);display:flex;align-items:center;justify-content:space-around;padding:0 6px 12px;font-size:10px;color:var(--bart)}
.mob .tab span{display:flex;flex-direction:column;align-items:center;gap:3px;position:relative}.mob .tab span.on{color:var(--baron)}
.mob .tab em{position:absolute;top:-4px;right:-4px;font-style:normal;font-size:9.5px;font-weight:700;background:var(--acc);color:#fff;border-radius:99px;padding:0 4px}
.mob .fab{width:50px;height:50px;border-radius:50%;background:var(--prim);color:var(--primt);display:grid;place-items:center;margin-top:-24px;box-shadow:0 10px 18px -8px rgba(0,0,0,.45)}
.mob .acts{display:flex;gap:7px;padding:10px 12px 18px;background:var(--bar);border-top:1px solid var(--line);flex:none}
.mob .acts span{height:44px;min-width:44px;border-radius:var(--rs);display:flex;align-items:center;justify-content:center;gap:6px;font-weight:600;font-size:13px;border:1px solid var(--line);background:var(--card);color:var(--ink)}
.mob .acts span.p{flex:1;white-space:nowrap;background:var(--prim);border-color:var(--prim);color:var(--primt)}
.mob .kv{display:grid;grid-template-columns:86px 1fr;gap:6px 8px;font-size:12.5px;align-items:center}.mob .kv>span:nth-child(odd){color:var(--mut);display:flex;align-items:center;gap:6px}
.mob .kv b{font-weight:600}
.mob .ln{display:flex;justify-content:space-between;font-size:12.5px;gap:8px}.mob .ln.sub{color:var(--mut)}.mob .ln>:last-child{white-space:nowrap}
.mob .sum{display:flex;justify-content:space-between;align-items:baseline;border-top:1px dashed var(--line);padding-top:8px;margin-top:6px}.mob .sum b{font-size:19px;font-weight:700}
.mob .sw{display:inline-block;width:12px;height:12px;border-radius:4px;background:var(--c);box-shadow:inset 0 0 0 1px rgba(0,0,0,.15);flex:none}
.mob .mono{font:600 12.5px 'JB',monospace}
.mob .tgl{width:34px;height:20px;border-radius:99px;background:var(--acc);position:relative;flex:none}.mob .tgl:after{content:"";position:absolute;right:2px;top:2px;width:16px;height:16px;border-radius:50%;background:#fff}
.mob .tgl.off{background:#D5D7E0}.mob .tgl.off:after{right:auto;left:2px}
.mob .dim{position:absolute;inset:0;background:rgba(10,12,20,.42);z-index:3}
.mob .sheet{position:absolute;left:0;right:0;bottom:0;z-index:4;background:var(--card);border-radius:24px 24px 0 0;padding:8px 16px 20px;display:flex;flex-direction:column;gap:10px}
.mob .sheet .grab{width:38px;height:4px;border-radius:9px;background:#D5D7E0;align-self:center}
.mob .opt{display:flex;gap:6px;flex-wrap:wrap}.mob .opt span{height:32px;padding:0 10px;border-radius:var(--rs);border:1px solid var(--line);display:flex;align-items:center;gap:6px;font-size:12.5px}
.mob .opt span.on{border-color:var(--acc);background:var(--acc2);color:var(--acc);font-weight:600}.mob .opt span.no{color:#B5B7C4;text-decoration:line-through}
.mob .grp{background:var(--card);border:1px solid var(--line);border-radius:var(--r);overflow:hidden}.mob .grp div{display:flex;align-items:center;gap:10px;padding:10px 12px;font-size:13px;border-bottom:1px solid var(--line)}
.mob .grp div:last-child{border-bottom:0}.mob .grp div .i:first-child{color:var(--mut)}.mob .grp div small{margin-left:auto;color:var(--mut);font-size:11.5px}.mob .grp div .i:last-child{color:#B5B7C4}
.mob .glab{font-size:11.5px;color:var(--mut);padding:2px 4px 0}
"""


def phone(cap, inner, bottom=""):
    return (f'<figure><div class="ph"><div class="scr"><div class="isl"></div><div class="sbar"><span>9:41</span><span>{ic("activity", 13)}</span></div>'
            f'<div class="bd">{inner}</div>{bottom}</div></div><figcaption>{cap}</figcaption></figure>')


def tabbar(on, items=None, fab=True):
    items = items or [("home", "house", "Головна", ""), ("orders", "receipt-text", "Замовлення", ""), ("+", "", "", ""), ("leads", "inbox", "Ліди", "5"), ("more", "layout-grid", "Ще", "")]
    h = ""
    for k, i, n, b in items:
        if k == "+":
            h += f'<span class="fab">{ic("plus", 24, 2.2)}</span>' if fab else ""
            continue
        h += f'<span class="{"on" if k == on else ""}">{ic(i, 20)}{n}{f"<em>{b}</em>" if b else ""}</span>'
    return f'<div class="tab">{h}</div>'


def stp(code):
    n, c = ST[code]
    return f'<span class="st" style="--c:{c}"><i></i>{n}</span>'


def orow(o, extra=""):
    return (f'<div class="row" style="flex-wrap:wrap"><span style="flex:1;min-width:0"><b>{o[1]}</b><small>№{o[0]} · {o[3]}</small></span><span class="s">{o[5]} ₴</span>'
            f'<span style="width:100%;display:flex;justify-content:space-between;align-items:center;margin-top:3px">{stp(o[6])}<small>{o[7]}</small></span>{extra}</div>')


GOODS = f"""<div class="ln"><span>Павербанк 20000, чорний</span><b>1 599 ₴</b></div><div class="ln sub"><span>↳ Кабель USB-C 1 м · допродаж</span><span>198 ₴</span></div>"""

# ================================================================ 1 · Лайм-бенто
CSS1 = BASE + """
.m1{--mbg:#D9DED5;--acc:#0F3B2C;--acc2:#EAF9CF;--ink:#0F231B;--mut:#6A786F;--line:#E2E6DF;--sbg:#ECEEE9;--r:18px;--rs:13px;--prim:#C6F36D;--primt:#0F231B;--baron:#0F3B2C;--font:500 13px/1.4 'Manrope',sans-serif}
.m1 h2{font-weight:800}.m1 .lime{background:#C6F36D;border-color:#C6F36D}.m1 .forest{background:#0F3B2C;border-color:#0F3B2C;color:#fff}
.m1 .k3{display:grid;grid-template-columns:1.25fr 1fr 1fr;gap:7px}.m1 .k3 .card{padding:10px}.m1 .k3 b{display:block;font-size:20px;font-weight:800;letter-spacing:-.02em}.m1 .k3 small{font-size:10.5px;color:var(--mut)}
.m1 .k3 .lime small{color:#3D5A1B}
.m1 .nav div{display:flex;align-items:center;gap:10px;height:30px;padding:0 10px;border-radius:12px;font-size:13.5px}.m1 .nav div.on{background:#fff;font-weight:700}.m1 .nav div em{margin-left:auto;font-style:normal;font-size:11px;font-weight:700}
.m1 .nav div em.l{background:#C6F36D;border-radius:99px;padding:0 7px}.m1 .nav .lab{font-size:11px;color:var(--mut);height:24px;padding-top:6px}
.m1 .stats{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;margin-top:8px}.m1 .stats div{background:#F3F5F0;border-radius:10px;padding:6px}.m1 .stats small{display:block;font-size:10px;color:var(--mut)}.m1 .stats b{font-size:13.5px;font-weight:800}
.m1 .trk{display:flex;gap:4px;margin-top:8px}.m1 .trk i{flex:1;height:5px;border-radius:9px;background:#DDE3D8}.m1 .trk i.on{background:#0F3B2C}
"""


def m1():
    menu = f"""<div class="tp"><span style="width:32px;height:32px;border-radius:10px;background:#0F3B2C;color:#C6F36D;display:grid;place-items:center;font-weight:800">m</span><b style="font-size:17px;font-weight:800">mdmy</b>
<span class="r">{ic("x", 20)}</span></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:7px"><span class="card forest" style="display:flex;gap:6px;align-items:center;justify-content:center;font-weight:700;padding:9px">{ic("plus", 15)}Замовлення</span>
<span class="card lime" style="display:flex;gap:6px;align-items:center;justify-content:center;font-weight:700;padding:9px">{ic("package-plus", 15)}Товар</span></div>
<div class="nav"><div class="lab">Продажі</div><div>{ic("house", 17)}Головна</div><div>{ic("inbox", 17)}Ліди<em class="l">12</em></div><div class="on">{ic("receipt-text", 17)}Замовлення<em>248</em></div>
<div>{ic("square-kanban", 17)}Дошка</div><div>{ic("contact", 17)}Покупці</div><div class="lab">Склад</div><div>{ic("package", 17)}Товари</div><div>{ic("boxes", 17)}Склад</div>
<div class="lab">Гроші й аналітика</div><div>{ic("wallet", 17)}Оплати</div><div>{ic("chart-column-stacked", 17)}Статистика</div><div>{ic("settings", 17)}Налаштування</div></div>
<div class="card forest" style="margin-top:auto;margin-bottom:14px"><b style="font-size:16px;font-weight:800">5 нових лідів</b><div style="font-size:11.5px;color:#B9CCC2;margin:3px 0 9px">Найстаріший чекає 18 хв</div>
<span style="display:flex;justify-content:center;height:34px;align-items:center;border-radius:11px;background:#C6F36D;color:#0F231B;font-weight:700">Обробити ліди</span></div>"""
    lst = f"""<div class="tp"><div><h2>Замовлення</h2><div class="mut">Четвер, 29 жовтня</div></div><span class="r">{ic("search", 20)}{ic("funnel", 20)}</span></div>
<div class="k3"><div class="card lime"><small>Сьогодні</small><b>18</b><small>24 870 ₴</small></div><div class="card"><small>Апрув</small><b>68%</b><small style="color:#16A34A">↑ 4,2%</small></div><div class="card"><small>Без ТТН</small><b>9</b><small>3 — понад добу</small></div></div>
<div class="chips"><span class="on">Усі <em>248</em></span><span>Підтверджено <em>31</em></span><span>Відправлено <em>57</em></span></div>{"".join(orow(o) for o in ORDERS[:4])}"""
    card = f"""<div class="tp">{ic("chevron-left", 22)}<div><b style="font-size:16px;font-weight:800">№1482</b><div class="mut">14:32 · Instagram</div></div><span class="r">{stp("ok")}</span></div>
<div class="card"><div style="display:flex;align-items:center;gap:9px"><span style="width:34px;height:34px;border-radius:11px;background:#FFE3C9;display:grid;place-items:center;font-weight:800;font-size:12px">ШТ</span>
<span><b style="font-weight:800">Шевченко Тарас</b><div class="mut">+380 67 123 45 67</div></span></div><div class="stats"><div><small>Замовл.</small><b>4</b></div><div><small>Викуп</small><b>75%</b></div><div><small>Відмов</small><b>1</b></div><div><small>Сума</small><b>5,8к</b></div></div></div>
<div class="card">{GOODS}</div>
<div class="card"><div class="ln"><b style="font-weight:800">Нова Пошта</b><span class="mut">Київ, №12</span></div><div class="mono" style="margin-top:4px">20450913998365</div><div class="trk"><i class="on"></i><i class="on"></i><i></i><i></i></div>
<div class="mut" style="margin-top:4px">Прямує до відділення · 30.10</div></div>
<div class="card forest"><div style="font-size:11.5px;color:#B9CCC2">До сплати при отриманні</div><b style="font-size:28px;font-weight:800;letter-spacing:-.02em">1 597 <span style="color:#C6F36D">₴</span></b>
<div class="ln" style="color:#B9CCC2;margin-top:2px"><span>Передоплата 200 ₴</span><span style="color:#C6F36D">Чек ✓</span></div></div>"""
    acts = f'<div class="acts"><span>{ic("phone", 18)}</span><span>{ic("message-circle", 18)}</span><span class="p">{ic("truck", 17)}Створити ТТН</span></div>'
    var = f"""<div style="opacity:.5;display:flex;flex-direction:column;gap:9px"><div class="tp">{ic("chevron-left", 22)}<b style="font-size:16px;font-weight:800">Нове замовлення</b></div><div class="card" style="height:90px"></div><div class="card" style="height:120px"></div></div>
<div class="dim"></div><div class="sheet"><span class="grab"></span><div style="display:flex;gap:10px;align-items:center"><span style="width:46px;height:46px;border-radius:13px;background:#0F231B;color:#C6F36D;display:grid;place-items:center">{ic("zap", 22)}</span>
<span><b style="font-weight:800;font-size:15px">Павербанк Volt</b><div class="mut">оберіть варіант</div></span><b style="margin-left:auto;font-size:17px;font-weight:800">1 599 ₴</b></div>
<div class="mut">Колір</div><div class="opt"><span class="on"><i class="sw" style="--c:#151515"></i>Чорний</span><span><i class="sw" style="--c:#F4F4F2"></i>Білий</span><span class="no"><i class="sw" style="--c:#2F5BEA"></i>Синій</span></div>
<div class="mut">Ємність</div><div class="opt"><span>10 000</span><span class="on">20 000 мА·год</span></div>
<div class="card" style="background:#F3F5F0;border:0;display:flex;gap:8px;align-items:center">{ic("boxes", 16)}<span>Чорний · 20 000: <b style="font-weight:800">18 шт</b>, 3 в резерві</span></div>
<div class="ln"><span>Кількість</span><span class="opt"><span>−</span><span style="font-weight:800">1</span><span>+</span></span></div>
<span style="display:flex;justify-content:center;align-items:center;gap:6px;height:46px;border-radius:14px;background:#0F3B2C;color:#fff;font-weight:700">{ic("plus", 16)}Додати в замовлення</span></div>"""
    return f'<div class="mob m1">{phone("Меню", menu)}{phone("Список із показниками", lst, tabbar("orders"))}{phone("Картка — блоки", card, acts)}{phone("Вибір варіанта товару", var)}</div>'


# ================================================================ 3 · Чистий аркуш
CSS3 = BASE + """
.m3{--mbg:#E4E3DF;--acc:#2E6BE6;--acc2:#EAF1FD;--ink:#1F1F1C;--mut:#7A7975;--line:#ECECE9;--sbg:#fff;--r:10px;--rs:8px;--prim:#1F1F1C;--baron:#1F1F1C;--font:400 13px/1.45 'Onest',sans-serif}
.m3 h2{font-weight:600;font-size:23px}.m3 .card{box-shadow:0 1px 2px rgba(0,0,0,.04)}.m3 .row b,.m3 .row .s{font-weight:500}.m3 .chips span.on{background:#F1F1EF;color:var(--ink);border-color:var(--line);font-weight:500}
.m3 .crumb{font-size:11.5px;color:var(--mut)}.m3 .seg{display:flex;gap:16px;border-bottom:1px solid var(--line);font-size:12.5px;color:var(--mut)}.m3 .seg span{padding:6px 0;display:flex;gap:5px;align-items:center}
.m3 .seg span.on{color:var(--ink);box-shadow:inset 0 -2px 0 var(--ink);font-weight:500}
.m3 .lead{border:1px solid var(--line);border-radius:10px;padding:9px 11px;display:flex;flex-direction:column;gap:3px;font-size:12px}
.m3 .lead .h{display:flex;align-items:center;gap:6px;color:var(--mut)}.m3 .lead .h .tg{font-size:10.5px;padding:0 6px;border-radius:5px;background:var(--c2);color:var(--c)}.m3 .lead b{font-weight:600;font-size:13.5px}
.m3 .lead .f{display:flex;justify-content:space-between;color:var(--mut)}.m3 .lead .f b{color:var(--ink);font-size:12.5px}
.m3 .props{display:grid;grid-template-columns:96px 1fr;gap:7px 8px;font-size:12.5px;align-items:center}.m3 .props>span:nth-child(odd){display:flex;gap:7px;align-items:center;color:var(--mut)}
.m3 .tag{font-size:10.5px;padding:1px 6px;border-radius:5px;background:#EAF7EE;color:#1B7A3D}
.m3 .grp div .i:first-child{color:var(--ink)}
.m3 .val{display:flex;align-items:center;gap:10px;padding:9px 2px;border-bottom:1px solid var(--line);font-size:13px}.m3 .val .i:first-child{color:#C5C4BF}.m3 .val small{margin-left:auto;color:var(--mut)}
"""


def m3():
    leads = [("1481", "Лендинг", "#2E6BE6", "#EAF1FD", "Коваленко Ірина", "Набір кабелів USB-C", "14:18", "649"),
             ("1473", "Instagram", "#C13584", "#FCEAF3", "Лисенко Юлія", "Кабель Lightning 2 м ×2", "09:41", "398"),
             ("1484", "TikTok", "#1F1F1C", "#F1F1EF", "Дорошенко Ігор", "Павербанк 20000 мА·год", "щойно", "1 599"),
             ("1483", "Facebook", "#1877F2", "#E8F1FE", "Савчук Олена", "Лампа настільна LED", "3 хв", "899")]
    lh = "".join(f"""<div class="lead" style="--c:{c};--c2:{c2}"><div class="h"># {n}<span class="tg">{s}</span><span style="margin-left:auto">{ic("ellipsis", 14)}</span></div><b>{nm}</b><span>{p}</span>
<div class="f"><span>{ic("clock", 12)} {t}</span><b>{sm} ₴</b></div></div>""" for n, s, c, c2, nm, p, t, sm in leads)
    l1 = f"""<div class="crumb">Продажі › Ліди</div><div class="tp"><h2>Ліди</h2><span class="r">{ic("search", 19)}<span style="background:#2E6BE6;color:#fff;border-radius:8px;height:30px;padding:0 10px;display:flex;align-items:center;gap:4px;font-size:12.5px;font-weight:500">{ic("plus", 14)}Лід</span></span></div>
<div class="seg"><span>{ic("list", 13)}Список</span><span class="on">{ic("square-kanban", 13)}Дошка</span><span>{ic("clock", 13)}Передзвони</span></div>
<div class="chips"><span class="on"><i class="sw" style="--c:#3B82F6;width:8px;height:8px;border-radius:50%"></i>Новий <em>4</em></span><span>Недодзвон <em>2</em></span><span>Передзвонити <em>3</em></span></div>{lh}"""
    c3 = f"""<div class="crumb">Замовлення › Підтверджено › №1482</div><h2 style="font-size:21px">Шевченко Тарас Григорович</h2>
<div class="props"><span>{ic("circle-dot", 14)}Статус</span><span>{stp("ok")}</span><span>{ic("phone", 14)}Телефон</span><span>+380 67 123 45 67 <span class="tag">Viber</span></span>
<span>{ic("landmark", 14)}Юрособа</span><span>ФОП Максимчук О. В.</span><span>{ic("contact", 14)}Покупець</span><span>4 замовл. · викуп 75%</span><span>{ic("user", 14)}Менеджер</span><span>Олена Литвин</span>
<span>{ic("globe", 14)}Джерело</span><span>Instagram → Інтернет-магазин</span></div>
<div class="seg"><span class="on">Товари 2</span><span>Доставка</span><span>Оплата</span><span>Історія 5</span></div>
<div style="display:flex;flex-direction:column;gap:6px">{GOODS}<div class="sum"><span class="mut">Разом до сплати</span><b>1 797 ₴</b></div></div>
<div class="mut" style="display:flex;align-items:center;gap:6px">{ic("plus", 13)}Додати товар · {ic("sparkles", 13)}Чохол, 249 ₴</div>"""
    acts3 = f'<div class="acts"><span>{ic("phone", 18)}</span><span>{ic("printer", 18)}</span><span class="p">{ic("truck", 17)}Створити ТТН</span></div>'
    grp = lambda t, xs: f'<div class="glab">{t}</div><div class="grp">' + "".join(f'<div>{ic(i, 16)}{n}<small>{s}</small>{ic("chevron-right", 15)}</div>' for i, n, s in xs) + "</div>"
    s3 = f"""<div class="tp"><h2>Налаштування</h2><span class="r">{ic("search", 19)}</span></div>
{grp("Продажі", [("list-checks", "Статуси", "10"), ("layers", "Довідники", ""), ("globe", "Джерела й відділи", "5")])}
{grp("Доставка", [("truck", "Нова Пошта", "2 ключі"), ("box", "Укрпошта", ""), ("map-pin", "Meest", "")])}
{grp("Гроші", [("landmark", "Юрособи", "2"), ("receipt", "Checkbox", "3 каси"), ("credit-card", "Види оплат", "47")])}
{grp("Зв'язок", [("message-square", "SMS і Viber", ""), ("send", "Telegram", "")])}"""
    vals = [("#151515", "Чорний", "12 товарів"), ("#F4F4F2", "Білий", "9 товарів"), ("#2F5BEA", "Синій", "7 товарів"), ("#F2A7C3", "Рожевий", "4 товари")]
    a3 = f"""<div class="crumb">Склад › Товари › Атрибути</div><div class="tp">{ic("palette", 22)}<h2>Колір</h2><span class="r">{ic("ellipsis", 19)}</span></div>
<div class="props"><span>Тип</span><span>Кольорові плашки</span><span>У фільтрі сайту</span><span>Так</span><span>Товарів</span><span>32</span></div>
<div class="seg"><span class="on">Значення 4</span><span>Товари 32</span></div>
{"".join(f'<div class="val">{ic("grip-vertical", 15)}<i class="sw" style="--c:{c}"></i>{n}<small>{s}</small></div>' for c, n, s in vals)}
<div class="val" style="color:var(--mut)">{ic("plus", 15)}Додати значення</div>
<div class="card" style="background:#FAFAF9;display:flex;gap:8px;align-items:flex-start;font-size:12px;color:var(--mut)">{ic("sparkles", 15)}<span>Нове значення одразу з'явиться у всіх товарах з цим атрибутом — варіанти можна згенерувати однією кнопкою.</span></div>"""
    tb = [("home", "house", "Головна", ""), ("leads", "inbox", "Ліди", "5"), ("orders", "receipt-text", "Замовлення", ""), ("products", "package", "Товари", ""), ("settings", "settings", "Ще", "")]
    return (f'<div class="mob m3">{phone("Ліди дошкою — статуси чипами", l1, tabbar("leads", tb, False))}{phone("Картка як сторінка з властивостями", c3, acts3)}'
            f'{phone("Налаштування групами", s3, tabbar("settings", tb, False))}{phone("Атрибут і його значення", a3, tabbar("products", tb, False))}</div>')


# ================================================================ 5 · Темна смуга + дерево
CSS5 = BASE + """
.m5{--mbg:#DCDAE6;--acc:#6D4AFF;--acc2:#F1EDFF;--ink:#17171C;--mut:#70707B;--line:#ECECF0;--sbg:#FAFAFB;--r:10px;--rs:9px;--prim:#6D4AFF;--bar:#17171C;--bart:#8B8B98;--baron:#fff;--font:400 12.5px/1.45 'Inter',sans-serif}
.m5 .tab{border-top:0}.m5 .tab span.on{color:#fff}.m5 .tab span.on:before{content:"";position:absolute;top:-10px;width:22px;height:3px;border-radius:3px;background:#6D4AFF}
.m5 h2{font-size:20px}.m5 .row{border-radius:0;border-width:0 0 1px;padding:8px 2px;background:transparent}
.m5 .tree div{display:flex;align-items:center;gap:8px;height:32px;padding:0 8px;border-radius:8px;font-size:12.5px}.m5 .tree div.on{background:#fff;box-shadow:0 0 0 1px var(--line);font-weight:600}
.m5 .tree div small{margin-left:auto;color:var(--mut)}.m5 .tree div i.d{width:7px;height:7px;border-radius:50%;background:var(--c)}.m5 .tree .sub{padding-left:24px}
.m5 .kp{background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 12px}.m5 .kp small{color:var(--mut);font-size:11px}.m5 .kp b{display:block;font-size:22px;font-weight:700;letter-spacing:-.02em}
.m5 .gh{font-size:11px;color:var(--mut);display:flex;gap:5px;align-items:center;padding-top:4px}
.m5 .cbx{width:16px;height:16px;border-radius:5px;border:1.5px solid #C9C9D3;flex:none;display:grid;place-items:center}.m5 .cbx.on{background:#6D4AFF;border-color:#6D4AFF;color:#fff}
.m5 .bulk{position:absolute;left:10px;right:10px;bottom:84px;z-index:4;background:#17171C;color:#fff;border-radius:14px;padding:10px 12px;display:flex;align-items:center;gap:8px;font-size:12px}
.m5 .bulk span.b{background:#2A2A33;border-radius:8px;padding:6px 9px;font-weight:600}
.m5 .bseg{display:flex;gap:5px;overflow:hidden;flex:none}.m5 .bseg span{flex:none;height:28px;padding:0 10px;border-radius:8px;display:flex;align-items:center;gap:5px;font-size:12px;background:#fff;border:1px solid var(--line)}
.m5 .bseg span.on{background:#6D4AFF;border-color:#6D4AFF;color:#fff;font-weight:600}
.m5 .fld{display:flex;flex-direction:column;gap:3px}.m5 .fld label{font-size:10.5px;color:var(--mut)}.m5 .fld div{height:34px;border:1px solid var(--line);border-radius:8px;background:#fff;display:flex;align-items:center;gap:7px;padding:0 9px;font-size:12.5px}
.m5 .dark{background:#17171C;color:#fff;border-radius:14px;padding:11px 12px}.m5 .dark small{color:#9B9BA8;font-size:11px}
"""


def m5():
    tb = [("sales", "receipt-text", "Продажі", "5"), ("stock", "boxes", "Склад", ""), ("money", "wallet", "Гроші", ""), ("an", "chart-bar", "Аналітика", ""), ("set", "settings", "Налашт.", "")]
    sts = [("Усі", None, "248", True), ("Підтверджено", "#10B981", "31", False), ("Комплектується", "#0891B2", "14", False), ("Відправлено", "#6366F1", "57", False),
           ("Прибуло у відділення", "#F97316", "22", False), ("Отримано", "#16A34A", "96", False), ("Відмова", "#EF4444", "9", False)]
    tr = "".join(f'<div class="sub {"on" if on else ""}" style="--c:{c or "#17171C"}">{"<i class=d></i>" if c else ""}{n}<small>{v}</small></div>' for n, c, v, on in sts)
    t5 = f"""<div class="tp"><h2>Продажі</h2><span class="r"><span style="background:#6D4AFF;color:#fff;border-radius:8px;height:30px;padding:0 10px;display:flex;align-items:center;gap:4px;font-weight:600">{ic("plus", 14)}Нове</span></span></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:7px"><div class="kp"><small>Надійшло сьогодні</small><b style="color:#16A34A;font-size:19px">+24 870 ₴</b></div><div class="kp"><small>Післяплата в дорозі</small><b style="font-size:19px">48 300 ₴</b></div></div>
<div class="tree"><div>{ic("house", 16)}Головна</div><div>{ic("inbox", 16)}Ліди<small style="background:#6D4AFF;color:#fff;border-radius:99px;padding:0 7px">5 нових</small></div>
<div>{ic("chevron-down", 16)}<b style="font-weight:600">Замовлення</b><small>312 840 ₴</small></div>{tr}<div>{ic("contact", 16)}Покупці<small>1 904</small></div></div>
<div class="gh">Мої фільтри</div><div class="tree"><div>{ic("truck", 15)}Чекають ТТН<small>9</small></div><div>{ic("phone", 15)}Передзвонити сьогодні<small>6</small></div></div>"""
    rows = ""
    for k, o in enumerate(ORDERS[:7]):
        sel = k in (0, 2)
        rows += (f'<div class="row"><span class="cbx {"on" if sel else ""}">{ic("check", 10, 3) if sel else ""}</span><span style="flex:1;min-width:0"><b>{o[1]}</b><small>№{o[0]} · {o[3]}</small></span>'
                 f'<span class="s"><span style="display:block">{o[5]} ₴</span><span style="display:inline-flex;align-items:center;gap:4px;font-size:10.5px;font-weight:500;color:{ST[o[6]][1]}">●{ST[o[6]][0]}</span></span></div>')
    l5 = f"""<div class="tp">{ic("chevron-left", 20)}<h2>Замовлення</h2><span class="r">{ic("search", 18)}{ic("funnel", 18)}</span></div>
<div class="gh">Сьогодні, 29 жовтня · 10 замовлень · 12 316 ₴</div><div>{rows}</div>
<div class="bulk"><b>2</b> вибрано<span class="b" style="margin-left:auto">Статус</span><span class="b">ТТН</span><span class="b">{ic("printer", 13)}</span></div>"""
    c5 = f"""<div class="tp">{ic("chevron-left", 20)}<div><b style="font-size:16px;font-weight:700">№1482</b> <span class="mut">· Instagram</span></div><span class="r">{stp("ok")}</span></div>
<div class="bseg"><span>Покупець</span><span class="on">Товари 2</span><span>Доставка</span><span>Оплата</span><span>Історія</span></div>
<div class="card"><h3>{ic("package", 15)}Товари<span class="r">+ Товар</span></h3><div style="display:flex;flex-direction:column;gap:5px;margin-top:6px">{GOODS}</div></div>
<div class="card"><h3>{ic("truck", 15)}Доставка<span class="r" style="color:#F97316">● у дорозі</span></h3><div style="display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:7px">
<div class="fld"><label>Місто</label><div>{ic("map-pin", 13)}Київ</div></div><div class="fld"><label>Відділення</label><div>№12</div></div><div class="fld" style="grid-column:1/-1"><label>ТТН</label><div class="mono">20450913998365</div></div></div></div>
<div class="dark"><small>До сплати при отриманні</small><b style="display:block;font-size:26px;font-weight:700">1 597 ₴</b><div class="ln" style="color:#C9C9D3"><span>Контроль оплати НП</span><span style="color:#B7A6FF">Чек ✓</span></div></div>"""
    acts5 = f'<div class="acts" style="background:#fff"><span>{ic("phone", 18)}</span><span>{ic("message-circle", 18)}</span><span class="p">{ic("truck", 17)}Створити ТТН</span></div>'
    vr = ""
    for k, (cn, cc, cap, sku, pr, stk, rs) in enumerate(VARIANTS):
        sel = k in (2, 3)
        vr += (f'<div class="row"><span class="cbx {"on" if sel else ""}">{ic("check", 10, 3) if sel else ""}</span><i class="sw" style="--c:{cc}"></i><span style="flex:1"><b>{cn} · {cap}</b><small class="mono" style="font-size:11px">{sku}</small></span>'
               f'<span class="s"><span style="display:block">{pr} ₴</span><small style="color:{"#EF4444" if stk < 4 else "var(--mut)"}">{stk} шт · рез. {rs}</small></span></div>')
    v5 = f"""<div class="tp">{ic("chevron-left", 20)}<h2>Павербанк Volt</h2></div><div class="mut">6 варіантів · 63 шт · 2 закінчуються</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:7px"><div class="kp"><small>На складі</small><b>63 шт</b></div><div class="kp"><small>Закінчиться</small><b style="color:#EF4444">~9 днів</b></div></div><div>{vr}</div>
<div class="bulk"><b>2</b> вибрано<span class="b" style="margin-left:auto">Ціна</span><span class="b">Списати</span><span class="b">Вимк.</span></div>"""
    return (f'<div class="mob m5">{phone("Дерево статусів із сумами", t5, tabbar("sales", tb, False))}{phone("Щільний список + масові дії", l5, tabbar("sales", tb, False))}'
            f'{phone("Картка — блоки перемикачем", c5, acts5)}{phone("Варіанти товару + масові дії", v5, tabbar("stock", tb, False))}</div>')


# ================================================================ 6 · Верхнє меню
CSS6 = BASE + """
.m6{--mbg:#D6DED9;--acc:#0B5D47;--acc2:#E5F2EC;--ink:#0E1A16;--mut:#66756F;--line:#E3E8E5;--sbg:#EEF1EF;--r:16px;--rs:12px;--prim:#0B5D47;--baron:#0B5D47;--font:400 13px/1.45 'Commissioner',sans-serif}
.m6 .topnav{display:flex;gap:5px;overflow:hidden;flex:none;background:#E1E6E3;border-radius:12px;padding:3px}.m6 .topnav span{flex:none;height:30px;padding:0 10px;border-radius:9px;display:flex;align-items:center;gap:5px;font-size:12px;color:#3C4B45}
.m6 .topnav span.on{background:#fff;color:var(--ink);font-weight:600;box-shadow:0 1px 3px rgba(14,26,22,.12)}.m6 .topnav em{font-style:normal;font-size:10px;font-weight:700;background:#0B5D47;color:#fff;border-radius:99px;padding:0 5px}
.m6 .srch{height:38px;border-radius:12px;background:#fff;border:1px solid var(--line);display:flex;align-items:center;gap:8px;padding:0 11px;color:#93A19B;font-size:12.5px}
.m6 .row{border-radius:14px}.m6 .row.on{border-color:#0B5D47;box-shadow:inset 3px 0 0 #0B5D47}
.m6 .gfab{position:absolute;right:16px;bottom:24px;z-index:4;height:46px;padding:0 16px;border-radius:14px;background:#0B5D47;color:#fff;display:flex;align-items:center;gap:6px;font-weight:600;box-shadow:0 10px 18px -8px rgba(11,93,71,.8)}
.m6 .darkbar{display:flex;gap:6px;padding:10px 10px 18px;background:#0E1A16;flex:none}.m6 .darkbar span{height:42px;min-width:42px;border-radius:11px;display:flex;align-items:center;justify-content:center;gap:6px;color:#fff;background:#1E2B27;font-size:12.5px;font-weight:600}
.m6 .darkbar span.p{flex:1;background:#2BD49A;color:#0E1A16}
.m6 .rule{background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px;display:flex;flex-direction:column;gap:4px}.m6 .rule .h{display:flex;align-items:center;gap:7px;font-weight:600;font-size:12.5px}.m6 .rule .h .tgl{margin-left:auto}
.m6 .rule small{color:var(--mut);font-size:11px;line-height:1.35}.m6 .tpl{background:#F3F6F4;border-radius:8px;padding:6px 8px;font-size:11px;color:#3C4B45}
.m6 .sline{display:flex;align-items:center;gap:8px;background:#fff;border:1px solid var(--line);border-radius:12px;padding:9px 11px;font-size:12.5px}.m6 .sline .i:last-child{margin-left:auto;color:var(--mut)}
.m6 .sline i.d{width:9px;height:9px;border-radius:3px;background:var(--c)}.m6 .sline .tg{font-size:10.5px;color:var(--mut);background:#F3F6F4;border-radius:6px;padding:0 6px}
.m6 .vc{display:flex;gap:9px;align-items:center;background:#fff;border:1px solid var(--line);border-radius:12px;padding:8px 10px}.m6 .vc .im{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;color:#fff;background:var(--c)}
.m6 .vc b{font-size:12.5px;font-weight:600;display:block}.m6 .vc small{font-size:10.5px;color:var(--mut)}.m6 .vc .n{margin-left:auto;text-align:right;font-weight:700;font-size:16px}.m6 .vc .n small{display:block;font-weight:400}
.m6 .opt span.on{border-color:#0B5D47;background:#E5F2EC;color:#0B5D47}
"""


def m6():
    tn = lambda on: (f'<div class="topnav">' + "".join(f'<span class="{"on" if k == on else ""}">{ic(i, 14)}{n}{f"<em>{b}</em>" if b else ""}</span>' for k, i, n, b in
                     [("home", "house", "Головна", ""), ("leads", "inbox", "Ліди", "5"), ("orders", "receipt-text", "Замовлення", ""), ("products", "package", "Товари", ""), ("set", "settings", "Ще", "")]) + "</div>")
    head = f'<div class="tp"><span style="width:30px;height:30px;border-radius:50%;background:#0E1A16;color:#fff;display:grid;place-items:center;font-weight:700">m</span><b style="font-size:16px;font-weight:700">mdmy</b><span class="r">{ic("bell", 19)}<span style="width:30px;height:30px;border-radius:50%;background:#FFD7B8;display:grid;place-items:center;font-size:11px;font-weight:700">ОЛ</span></span></div>'
    l6 = f"""{head}{tn("orders")}<div class="srch">{ic("search", 15)}Телефон, ПІБ, ТТН або №</div><div class="chips"><span class="on">Усі <em>248</em></span><span>Підтверджено <em>31</em></span><span>Відправлено <em>57</em></span></div>
{"".join(orow(o).replace('class="row"', 'class="row on"', 1) if k == 0 else orow(o) for k, o in enumerate(ORDERS[:4]))}<span class="gfab">{ic("plus", 17)}Нове</span>"""
    c6 = f"""<div class="tp">{ic("chevron-left", 22)}<div style="flex:1"><div class="ln"><span class="mut">№1482 · 14:32</span>{stp("ok")}</div><b style="font-size:17px;font-weight:700">Шевченко Тарас Г.</b></div></div>
<div class="card"><h3>{ic("user", 15)}Покупець<span class="r">{ic("phone", 16)} {ic("message-circle", 16)}</span></h3><div class="kv" style="margin-top:6px"><span>Телефон</span><b>+380 67 123 45 67</b><span>Історія</span><span>4 замовл. · викуп 75%</span></div></div>
<div class="card"><h3>{ic("package", 15)}Товари<span class="r">+ Допродаж</span></h3><div style="display:flex;flex-direction:column;gap:5px;margin-top:6px">{GOODS}</div></div>
<div class="card"><h3>{ic("truck", 15)}Нова Пошта<span class="r" style="color:#D97706">● прямує</span></h3><div class="kv" style="margin-top:6px"><span>Куди</span><span>Київ, №12</span><span>ТТН</span><span class="mono">20450913998365</span></div></div>
<div class="card"><h3>{ic("wallet", 15)}Оплата<span class="r" style="color:#16A34A">чек ✓</span></h3><div class="mut" style="margin-top:4px">До сплати при отриманні</div><b style="font-size:26px;font-weight:700;letter-spacing:-.02em">1 597 ₴</b></div>"""
    bar6 = f'<div class="darkbar"><span>{ic("printer", 17)}</span><span>{ic("tag", 17)}</span><span>{ic("message-square", 17)}</span><span class="p">{ic("truck", 16)}Створити ТТН</span></div>'
    rules = [("boxes", "Склад", True, "Списати товар і зняти резерв", None), ("receipt", "Чек Checkbox", True, "«Продаж» на касі юрособи замовлення", None),
             ("message-square", "SMS / Viber", True, None, "Ваше замовлення №{номер} відправлено. ТТН {ттн}"), ("store", "Маркетплейси", True, "Rozetka: «Передано в доставку»", None),
             ("send", "Telegram", False, "Повідомлення в чат складу", None)]
    rh = "".join(f'<div class="rule"><div class="h">{ic(i, 15)}{t}<span class="tgl {"" if on else "off"}"></span></div>{f"<small>{d}</small>" if d else ""}{f"<div class=tpl>{tp}</div>" if tp else ""}</div>' for i, t, on, d, tp in rules)
    s6 = f"""<div class="tp">{ic("chevron-left", 22)}<h2 style="font-size:19px">Статуси</h2><span class="r"><span style="background:#0B5D47;color:#fff;border-radius:10px;height:30px;padding:0 10px;display:flex;align-items:center;gap:4px;font-weight:600;font-size:12.5px">{ic("check", 14)}Зберегти</span></span></div>
<div class="sline" style="--c:#10B981"><i class="d"></i>Підтверджено<span class="tg">Замовлення</span>{ic("chevron-right", 15)}</div>
<div class="sline" style="--c:#6366F1;border-color:#0B5D47;flex-direction:column;align-items:stretch;gap:8px;background:#F6FAF8"><div style="display:flex;align-items:center;gap:8px"><i class="d"></i><b style="font-weight:600">Відправлено</b><span class="tg">Замовлення</span><span style="margin-left:auto">{ic("chevron-down", 15)}</span></div>{rh}</div>
<div class="sline" style="--c:#F97316"><i class="d"></i>Прибуло у відділення{ic("chevron-right", 15)}</div>"""
    vc = "".join(f'<div class="vc" style="--c:{"#2F5BEA" if cn == "Синій" else ("#E7E9E8" if cn == "Білий" else "#0E1A16")}"><span class="im">{ic("zap", 16)}</span><span><b>{cn} · {cap}</b><small>{sku} · {pr} ₴</small></span>'
                 f'<span class="n" style="color:{"#DC2626" if stk == 0 else "var(--ink)"}">{stk}<small>резерв {rs}</small></span></div>' for cn, cc, cap, sku, pr, stk, rs in VARIANTS[:4])
    v6 = f"""<div class="tp">{ic("chevron-left", 22)}<div><div class="mut">Товари</div><b style="font-size:17px;font-weight:700">Павербанк Volt</b></div></div>
<div class="chips"><span>Основне</span><span>Фото 4</span><span class="on">Варіанти 6</span><span>Доставка</span></div>
<div class="card"><div class="mut">Колір · 3 з 4</div><div class="opt" style="margin:5px 0 8px"><span class="on"><i class="sw" style="--c:#151515"></i>Чорний</span><span class="on"><i class="sw" style="--c:#F4F4F2"></i>Білий</span><span class="on"><i class="sw" style="--c:#2F5BEA"></i>Синій</span><span>Рожевий</span></div>
<div class="mut">Ємність · 2 з 3</div><div class="opt" style="margin-top:5px"><span class="on">10 000</span><span class="on">20 000</span><span>30 000</span></div>
<span style="display:flex;justify-content:center;align-items:center;gap:6px;height:40px;border-radius:12px;background:#0B5D47;color:#fff;font-weight:600;margin-top:10px">{ic("layers", 15)}Скласти 6 варіантів</span></div>{vc}"""
    return (f'<div class="mob m6">{phone("Меню вгорі + список", l6)}{phone("Картка + темна панель дій", c6, bar6)}'
            f'{phone("Статус розкривається з правилами", s6)}{phone("Конструктор варіантів", v6)}</div>')
