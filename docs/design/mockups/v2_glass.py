"""Варіант 2 — «Тепле скло» (Lendora + Liquid Glass): меню вгорі, плаваюча панель дій унизу, тонкі великі цифри."""
from common import *

CSS = """
.v2{--ink:#2A2018;--mut:#8A7B6B;--honey:#EFA51B;--peach:#F2946A;--glass:rgba(255,255,255,.52);--gl:rgba(255,255,255,.78);--line:rgba(120,90,50,.12);
  font:400 14px/1.45 'Geologica',sans-serif;color:var(--ink);width:100%;height:100%;position:relative;overflow:hidden;
  background:radial-gradient(900px 500px at 85% 15%,#FFE3B8 0,rgba(255,227,184,0) 60%),radial-gradient(700px 600px at 10% 90%,#F7D9E6 0,rgba(247,217,230,0) 60%),
  radial-gradient(800px 500px at 50% 50%,#FFF6E8 0,rgba(255,246,232,0) 70%),#F3EEE6}
.v2:before{content:"";position:absolute;inset:0;background:repeating-linear-gradient(90deg,rgba(255,255,255,.0) 0 118px,rgba(255,255,255,.35) 118px 120px);
  -webkit-mask:linear-gradient(#000,transparent 40%);opacity:.6}
.v2 .wrap{position:relative;height:100%;display:flex;flex-direction:column;padding:18px 26px 0;gap:16px}
.v2 .g{background:var(--glass);backdrop-filter:blur(22px) saturate(1.4);border:1px solid var(--gl);border-radius:26px;box-shadow:0 1px 0 rgba(255,255,255,.9) inset,0 20px 40px -28px rgba(110,70,20,.35)}
.v2 .bar{display:flex;align-items:center;gap:14px}
.v2 .brand{display:flex;align-items:center;gap:10px;font-weight:600;font-size:17px}.v2 .logo{width:34px;height:34px;border-radius:12px;background:var(--ink);color:#FFD27A;display:grid;place-items:center;font-weight:700}
.v2 .tabs{display:flex;gap:2px;padding:5px;border-radius:99px;margin:0 auto}
.v2 .tabs span{display:inline-flex;align-items:center;gap:7px;padding:8px 14px;border-radius:99px;font-size:13px;font-weight:500;color:#5D4F42;white-space:nowrap}
.v2 .tabs span.on{background:#fff;color:var(--ink);box-shadow:0 4px 12px -6px rgba(110,70,20,.4)}
.v2 .tabs em{font-style:normal;font-size:11px;font-weight:600;background:var(--honey);color:#fff;border-radius:99px;padding:0 6px}
.v2 .rb{display:flex;gap:8px;align-items:center}
.v2 .circ{width:40px;height:40px;border-radius:50%;display:grid;place-items:center;color:#5D4F42}
.v2 .av{width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,#F6C99B,#E79A6C);display:grid;place-items:center;font-weight:600;color:#5A2F12;font-size:13px}
.v2 .pbtn{display:inline-flex;align-items:center;gap:7px;height:40px;padding:0 16px;border-radius:99px;font-weight:500;font-size:13px;white-space:nowrap}
.v2 .pbtn.d{background:var(--ink);color:#fff}.v2 .pbtn.h{background:var(--honey);color:#fff}
.v2 .head{display:flex;align-items:center;gap:14px}.v2 .back{width:42px;height:42px;border-radius:50%;display:grid;place-items:center}
.v2 h1{font-size:34px;font-weight:300;letter-spacing:-.03em}.v2 h1 b{font-weight:500}
.v2 .head .r{margin-left:auto;display:flex;gap:8px}
.v2 .row{display:flex;gap:16px;flex:1;min-height:0}
.v2 .lab{font-size:12.5px;color:var(--mut)}
.v2 .p{padding:20px}.v2 h3{font-size:15px;font-weight:500;display:flex;align-items:center;gap:8px}.v2 h3 small{font-size:12px;color:var(--mut);font-weight:400}
.v2 .nums{display:flex;gap:44px;padding:6px 4px 0}
.v2 .n{display:flex;flex-direction:column}.v2 .n b{font-size:64px;font-weight:200;letter-spacing:-.05em;line-height:1}.v2 .n b sup{font-size:18px;font-weight:400;vertical-align:top;margin-left:4px;color:var(--honey)}
.v2 .n b i{font-style:normal;color:#C9B8A6}
.v2 .stl .s{display:flex;align-items:center;gap:10px;padding:9px 2px;border-bottom:1px solid var(--line);font-size:13.5px}
.v2 .stl .s i{width:8px;height:8px;border-radius:50%;background:var(--c)}.v2 .stl .s b{margin-left:auto;font-size:20px;font-weight:300;letter-spacing:-.02em}
.v2 .stl .s b small{font-size:12px;color:#C9B8A6;margin-left:2px}
.v2 .stl .s .bdg{font-size:11.5px;padding:3px 10px;border-radius:99px;background:rgba(255,255,255,.75);color:#5D4F42;min-width:76px;text-align:center}
.v2 .stl .s .bdg.y{background:#FFE08A;color:#6B4A00}.v2 .stl .s .bdg.r{background:#F7715E;color:#fff}
.v2 table{width:100%;border-collapse:collapse}.v2 th{font-size:12px;font-weight:400;color:var(--mut);text-align:left;padding:8px 10px}
.v2 td{padding:10px 10px;border-top:1px solid var(--line);font-size:13.5px;white-space:nowrap}
.v2 td.s{text-align:right;font-weight:500}.v2 .mut{color:var(--mut)}
.v2 .st{display:inline-flex;align-items:center;gap:6px;padding:4px 11px;border-radius:99px;font-size:12px;background:rgba(255,255,255,.8);color:color-mix(in srgb,var(--c) 70%,#2A2018)}
.v2 .st i{width:7px;height:7px;border-radius:50%;background:var(--c)}
.v2 .hot{background:linear-gradient(160deg,#FCE6C2 0%,#F8B969 55%,#F2946A 100%);border:0;color:#3B2410;position:relative;overflow:hidden}
.v2 .hot .big{font-size:25px;font-weight:300;line-height:1.1;letter-spacing:-.02em;color:#fff;margin-top:auto}
.v2 .hot .arr{position:absolute;right:18px;bottom:18px;width:46px;height:46px;border-radius:50%;border:1px solid rgba(255,255,255,.8);display:grid;place-items:center;color:#fff}
.v2 .faces{display:flex}.v2 .faces span{width:26px;height:26px;border-radius:50%;border:2px solid #FCE6C2;margin-left:-6px;display:grid;place-items:center;font-size:10px;font-weight:600;background:#fff}
.v2 .dock{position:absolute;left:50%;bottom:18px;transform:translateX(-50%);display:flex;align-items:center;gap:6px;padding:7px;border-radius:99px;z-index:5}
.v2 .dock span{width:46px;height:46px;border-radius:50%;display:grid;place-items:center;color:#5D4F42}
.v2 .dock span.on{background:var(--ink);color:#fff;width:auto;padding:0 18px;gap:8px;display:inline-flex;align-items:center;font-size:13px}
.v2 .dock .sep{width:1px;height:26px;background:var(--line);border-radius:0}
/* картка */
.v2 .col{display:flex;flex-direction:column;gap:16px;min-height:0}
.v2 .kv{display:grid;grid-template-columns:110px 1fr;gap:10px 12px;font-size:13.5px}.v2 .kv span{color:var(--mut)}
.v2 .who{display:flex;gap:12px;align-items:center;margin:14px 0}.v2 .who .av{width:52px;height:52px;font-size:16px}
.v2 .who b{font-size:18px;font-weight:500;display:block;letter-spacing:-.01em}.v2 .who small{color:var(--mut)}
.v2 .mini{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.v2 .mini div{background:rgba(255,255,255,.6);border-radius:16px;padding:10px}
.v2 .mini b{display:block;white-space:nowrap;font-size:20px;font-weight:300;letter-spacing:-.03em}.v2 .mini span{font-size:11.5px;color:var(--mut)}
.v2 .gd{display:flex;align-items:center;gap:12px;padding:12px 0;border-top:1px solid var(--line)}
.v2 .gd .ph{width:52px;height:52px;border-radius:16px;background:linear-gradient(150deg,#2E2620,#5A4A3C);display:grid;place-items:center;color:#FFD27A}
.v2 .gd .ph.w{background:linear-gradient(150deg,#fff,#EDE3D6);color:#B39A7E}
.v2 .gd b{font-weight:500;display:block}.v2 .gd small{color:var(--mut);font-size:12px}.v2 .gd .q{margin-left:auto;padding:5px 12px;border-radius:99px;background:rgba(255,255,255,.75);font-size:13px}
.v2 .gd .pr{width:80px;text-align:right;font-size:17px;font-weight:400}
.v2 .ttn{display:flex;align-items:center;gap:10px;padding:12px 14px;border-radius:18px;background:rgba(255,255,255,.65);margin-top:12px}
.v2 .ttn b{font:500 15px 'JB',monospace}.v2 .ttn span.r{margin-left:auto;display:flex;gap:10px;color:var(--mut)}
.v2 .curve{height:84px;margin-top:12px;position:relative}
.v2 .tot .big{font-size:76px;font-weight:200;letter-spacing:-.05em;line-height:1;color:#fff}.v2 .tot .big sup{font-size:22px;font-weight:400;vertical-align:top}
.v2 .tot .ln{display:flex;justify-content:space-between;font-size:13px;padding:8px 0;border-top:1px solid rgba(255,255,255,.4)}
.v2 .tl .e{display:grid;grid-template-columns:14px 1fr auto;gap:10px;padding:7px 0}.v2 .tl .e i{width:10px;height:10px;border-radius:50%;border:2px solid var(--honey);margin-top:5px}
.v2 .tl .e b{font-weight:500;font-size:13px;display:block}.v2 .tl .e small{color:var(--mut);font-size:12px}.v2 .tl time{color:var(--mut);font-size:12px}
/* налаштування */
.v2 .sn{display:flex;flex-direction:column;gap:4px;padding:12px;width:250px}
.v2 .sn span{display:flex;align-items:center;gap:10px;padding:10px 14px;border-radius:99px;color:#5D4F42;font-size:13.5px}
.v2 .sn span.on{background:#fff;color:var(--ink);box-shadow:0 4px 12px -6px rgba(110,70,20,.4)}
.v2 .sr{display:grid;grid-template-columns:200px 1fr 1fr 1fr 52px;gap:12px;align-items:center;padding:6px 12px;border-radius:20px;margin-bottom:5px;background:rgba(255,255,255,.45)}
.v2 .sr>*{justify-self:start}
.v2 .chipg{display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border-radius:99px;background:rgba(255,255,255,.85);font-size:12.5px}
.v2 .chipg.n{background:none;color:#C9B8A6}
.v2 .tg{display:inline-block;width:44px;height:26px;border-radius:99px;background:linear-gradient(90deg,#F8B969,#F2946A);position:relative;box-shadow:inset 0 1px 3px rgba(0,0,0,.12)}
.v2 .tg:after{content:"";position:absolute;right:3px;top:3px;width:20px;height:20px;border-radius:50%;background:#fff;box-shadow:0 2px 4px rgba(0,0,0,.2)}
.v2 .tg.off{background:rgba(255,255,255,.7)}.v2 .tg.off:after{right:auto;left:3px}
.v2 .sec{display:flex;align-items:center;gap:10px;margin:14px 0 10px;font-size:13px;color:var(--mut)}.v2 .sec b{color:var(--ink);font-weight:500;font-size:15px}
/* атрибути */
.v2 .ag{display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:22px}.v2 .ag.on{background:#fff;box-shadow:0 8px 20px -14px rgba(110,70,20,.5)}
.v2 .ag .ic{width:40px;height:40px;border-radius:14px;background:rgba(255,255,255,.7);display:grid;place-items:center;color:#8A5A12}.v2 .ag.on .ic{background:#FFE08A}
.v2 .ag b{font-weight:500;display:block}.v2 .ag small{font-size:12px;color:var(--mut)}
.v2 .vals{display:flex;gap:10px;flex-wrap:wrap}
.v2 .vl{display:inline-flex;align-items:center;gap:10px;padding:8px 16px 8px 8px;border-radius:99px;background:rgba(255,255,255,.75);font-size:14px}
.v2 .vl .sw{width:28px;height:28px;border-radius:50%;background:var(--c);box-shadow:inset 0 0 0 1px rgba(0,0,0,.1)}
.v2 .vl.add{background:none;border:1.5px dashed rgba(120,90,50,.3);color:var(--mut);padding:8px 16px}
.v2 .tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.v2 .tile{padding:16px;border-radius:22px;background:rgba(255,255,255,.6);display:flex;flex-direction:column;gap:8px}
.v2 .tile .t{display:flex;align-items:center;gap:8px}.v2 .tile .sw{width:18px;height:18px;border-radius:50%;background:var(--c);box-shadow:inset 0 0 0 1px rgba(0,0,0,.12)}
.v2 .tile .t b{font-weight:500}.v2 .tile .t small{margin-left:auto;font:500 11.5px 'JB',monospace;color:var(--mut)}
.v2 .tile .stk{font-size:44px;font-weight:200;letter-spacing:-.04em;line-height:1}.v2 .tile .stk small{font-size:13px;color:var(--mut);margin-left:6px;letter-spacing:0;font-weight:400}
.v2 .tile .ft{display:flex;justify-content:space-between;align-items:center;font-size:13px}.v2 .tile .ft b{font-weight:500;font-size:15px}
.v2 .tile.z{background:rgba(255,255,255,.3)}.v2 .tile.z .stk{color:#E2694E}
"""


def topbar(active):
    tabs = [("home", "Головна", "house"), ("leads", "Ліди", "inbox"), ("orders", "Замовлення", "receipt-text"), ("board", "Дошка", "square-kanban"),
            ("customers", "Покупці", "contact"), ("products", "Товари", "package"), ("warehouse", "Склад", "boxes"),
            ("money", "Гроші", "wallet"), ("stats", "Аналітика", "chart-column-stacked"), ("settings", "Налаштування", "settings")]
    t = "".join(f'<span class="{"on" if k == active else ""}">{ic(i, 16)}{n}{"<em>12</em>" if k == "leads" else ""}</span>' for k, n, i in tabs)
    return f"""<div class="bar"><div class="brand"><span class="logo">m</span>mdmy</div><nav class="tabs g">{t}</nav>
<div class="rb"><span class="circ g">{ic("search", 17)}</span><span class="circ g">{ic("bell", 17)}</span><span class="av">ОЛ</span></div></div>"""


def dock(items, on):
    out = ""
    for k, i, label in items:
        if k == "|":
            out += '<span class="sep"></span>'
        elif k == on:
            out += f'<span class="on">{ic(i, 18)}{label}</span>'
        else:
            out += f'<span title="{label}">{ic(i, 19)}</span>'
    return f'<div class="dock g">{out}</div>'


MAIN_DOCK = [("new", "plus", "Замовлення"), ("prod", "package-plus", "Товар"), ("|", "", ""), ("search", "search", "Пошук"),
             ("ttn", "truck", "ТТН"), ("print", "printer", "Друк"), ("sms", "message-square", "SMS")]


def orders():
    st = [("ok", 31, "Активний", ""), ("pack", 14, "Активний", ""), ("sent", 57, "У дорозі", ""), ("arr", 22, "Забрати", "y"),
          ("got", 96, "Готово", ""), ("ref", 9, "Повернути", "r")]
    stl = "".join(f'<div class="s" style="--c:{ST[c][1]}"><i></i>{ST[c][0]}<b>{n}<small>/248</small></b><span class="bdg {cl}">{t}</span></div>' for c, n, t, cl in st)
    rows = "".join(f"""<tr><td class="mut">{o[0]}</td><td>{o[1]}<div class="mut" style="font-size:12px">{o[2]}</div></td><td>{o[3]}</td><td>{pill(o[6])}</td>
<td class="mut">{o[7]}</td><td class="s">{o[5]} ₴</td></tr>""" for o in ORDERS[:9])
    body = f"""<div class="head"><span class="back g">{ic("chevron-left", 18)}</span><h1>Огляд <b>замовлень</b></h1>
<div class="r"><span class="pbtn g">{ic("calendar", 16)}Цей тиждень{ic("chevron-down", 14)}</span><span class="pbtn g">{ic("funnel", 16)}Фільтри</span><span class="pbtn d">{ic("plus", 16)}Замовлення</span></div></div>
<div class="row" style="flex:0 0 auto"><div class="nums" style="flex:1">
<div class="n"><b>18<sup>шт</sup></b><span class="lab">Замовлень сьогодні</span></div>
<div class="n"><b>24<i>,8</i><sup>тис</sup></b><span class="lab">Виторг сьогодні, ₴</span></div>
<div class="n"><b>68<sup>%</sup></b><span class="lab">Апрув за тиждень</span></div><div class="n"><b>81<sup>%</sup></b><span class="lab">Викуп за місяць</span></div></div></div>
<div class="row" style="padding-bottom:96px">
<div class="g p stl" style="width:330px"><h3>Статуси <small>· жовтень</small></h3>{stl}</div>
<div class="g p" style="flex:1;overflow:hidden"><h3>Останні замовлення <small>· оновлено щойно</small></h3><table><thead><tr><th>№</th><th>Покупець</th><th>Товар</th><th>Статус</th><th>Доставка</th><th style="text-align:right">Сума</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="g p hot" style="width:236px;display:flex;flex-direction:column;gap:10px"><div style="display:flex;align-items:center;gap:8px;font-size:12.5px">Ліди чекають<span class="faces" style="margin-left:6px"><span>КІ</span><span>ЛЮ</span><span>+3</span></span></div>
<div class="big">5 нових<br>лідів — передзвоніть<br>за 15 хв</div><span class="arr">{ic("arrow-up-right", 20)}</span></div></div>"""
    return f'<div class="v2"><div class="wrap">{topbar("orders")}{body}</div>{dock(MAIN_DOCK, "new")}</div>'


def card():
    o = ORDER
    mini = "".join(f"<div><b>{b}</b><span>{a}</span></div>" for a, b in CUSTOMER)
    goods = "".join(f"""<div class="gd" style="{"padding-left:30px" if up else ""}"><span class="ph {"w" if up else ""}">{ic("link" if up else "zap", 20)}</span>
<span><b>{nm}</b><small>{var} · {sku}</small></span><span class="q">{q} шт</span><span class="pr">{s} ₴</span></div>""" for nm, var, sku, q, p, s, up in o["items"])
    tl = "".join(f'<div class="e"><i></i><span><b>{t}</b><small>{d}</small></span><time>{tm}</time></div>' for tm, t, d, i in TIMELINE)
    body = f"""<div class="head"><span class="back g">{ic("chevron-left", 18)}</span><h1>Замовлення <b>№1482</b></h1>{pill("ok")}
<span class="lab">29.10.2026, 14:32 · Instagram / stories</span><div class="r"><span class="pbtn g">{ic("user", 16)}Олена Литвин{ic("chevron-down", 14)}</span>
<span class="pbtn g">{ic("landmark", 16)}ФОП Максимчук О. В.{ic("chevron-down", 14)}</span></div></div>
<div class="row" style="padding-bottom:96px">
<div class="col" style="width:380px"><div class="g p"><h3>Покупець</h3><div class="who"><span class="av">ШТ</span><span><b>{o["name"]}</b><small>{o["phone"]}</small></span></div>
<div class="mini">{mini}</div></div><div class="g p" style="flex:1"><h3>Деталі</h3><div class="kv" style="margin-top:12px"><span>Джерело</span><b style="font-weight:500">Instagram</b>
<span>Відділ</span><b style="font-weight:500">Інтернет-магазин</b><span>Позначки</span><span style="color:var(--ink)"><span class="chipg">VIP</span> <span class="chipg">Подарунок</span></span>
<span>Коментар</span><b style="font-weight:500">Зателефонувати після 18:00</b><span>UTM</span><b style="font-weight:400">instagram / stories / powerbank-20</b></div></div></div>
<div class="col" style="flex:1"><div class="g p"><h3>Товари <small>· 2 позиції</small></h3><div style="margin-top:8px">{goods}</div></div>
<div class="g p" style="flex:1"><h3>Доставка <small>· Нова Пошта</small></h3><div class="kv" style="margin-top:12px"><span>Відділення</span><b style="font-weight:500">Київ, №12 · вул. Межигірська, 1</b><span>Платник</span><b style="font-weight:500">Отримувач</b></div>
<div class="ttn">{ic("scan-barcode", 18)}<b>20450913998365</b><span class="r">{ic("copy", 17)}{ic("refresh-cw", 17)}</span></div>
<div class="curve"><svg viewBox="0 0 400 84" width="100%" height="84" preserveAspectRatio="none"><defs><linearGradient id="cg" x1="0" x2="1"><stop offset="0" stop-color="#F7715E"/><stop offset="1" stop-color="#EFA51B"/></linearGradient></defs>
<path d="M0 74 C 90 72, 170 66, 230 50 S 340 14, 400 8" fill="none" stroke="url(#cg)" stroke-width="3" vector-effect="non-scaling-stroke"/></svg>
<span style="position:absolute;left:0;top:44px" class="lab">Створено 15:20</span><span style="position:absolute;left:57%;top:14px;font-size:12.5px;font-weight:500">● Прямує до відділення</span>
<span style="position:absolute;right:0;top:64px" class="lab">Отримання 30.10</span></div>
<div class="kv" style="margin-top:16px"><span>Очікується</span><b style="font-weight:500">30 жовтня, після 13:00</b><span>Вартість</span><b style="font-weight:500">85 ₴ · платить отримувач</b></div></div></div>
<div class="col" style="width:330px"><div class="g p hot tot"><span style="font-size:12.5px">До сплати при отриманні</span><div class="big">1 797<sup> ₴</sup></div>
<div style="margin-top:14px"><div class="ln"><span>Передоплата · Monobank</span><b style="font-weight:500">200 ₴</b></div><div class="ln"><span>Оплата</span><b style="font-weight:500">Контроль оплати НП</b></div>
<div class="ln"><span>Чек Checkbox</span><b style="font-weight:500">Передоплата ✓</b></div></div></div>
<div class="g p tl" style="flex:1"><h3>Історія</h3><div style="margin-top:8px">{tl}</div></div></div></div>"""
    d = [("ttn", "truck", "Створити ТТН"), ("print", "printer", "Друк"), ("label", "tag", "Наклейка"), ("chk", "receipt", "Чек"), ("|", "", ""),
         ("call", "phone", "Дзвінок"), ("sms", "message-square", "SMS"), ("viber", "message-circle", "Viber"), ("|", "", ""), ("ok", "check", "Зберегти")]
    return f'<div class="v2"><div class="wrap">{topbar("orders")}{body}</div>{dock(d, "ttn")}</div>'


def settings():
    sn = "".join(f'<span class="{"on" if n == "Статуси" else ""}">{ic(i, 17)}{n}</span>' for n, i in SETTINGS)

    def rows(sec):
        out = ""
        for code, s, stock, chk, sms in STATUS_ROWS:
            if s != sec:
                continue
            c = lambda v, i: f'<span class="chipg n">—</span>' if v == "—" else f'<span class="chipg">{ic(i, 14)}{v}</span>'
            out += f'<div class="sr">{pill(code)}{c(stock, "boxes")}{c(chk, "receipt")}{c(sms, "message-square")}<span class="tg {"off" if code == "dup" else ""}"></span></div>'
        return out
    hd = '<div class="sr" style="background:none;padding-top:0;padding-bottom:0;font-size:12px;color:var(--mut)"><span>Статус</span><span>Склад</span><span>Чек</span><span>SMS / Viber</span><span></span></div>'
    body = f"""<div class="head"><span class="back g">{ic("chevron-left", 18)}</span><h1>Налаштування · <b>статуси</b></h1>
<div class="r"><span class="pbtn g">{ic("undo-2", 16)}Скасувати</span><span class="pbtn h">{ic("check", 16)}Зберегти</span></div></div>
<div class="row" style="padding-bottom:96px"><div class="g sn">{sn}</div><div class="g p" style="flex:1;overflow:hidden">
<div class="sec">{ic("inbox", 18)}<b>Ліди</b>· дзвонимо, уточнюємо, підтверджуємо</div>{hd}{rows("Ліди")}
<div class="sec">{ic("receipt-text", 18)}<b>Замовлення</b>· від підтвердження до отримання</div>{hd}{rows("Замовлення")}</div></div>"""
    d = [("add", "plus", "Новий статус"), ("|", "", ""), ("search", "search", "Пошук"), ("eye", "eye", "Перегляд"), ("undo", "undo-2", "Скасувати")]
    return f'<div class="v2"><div class="wrap">{topbar("settings")}{body}</div>{dock(d, "add")}</div>'


def attributes():
    gr = "".join(f'<div class="ag {"on" if n == 0 else ""}"><span class="ic">{ic(i, 18)}</span><span><b>{g}</b><small>{len(v)} значення · {u}</small></span></div>'
                 for n, (g, i, t, v, u) in enumerate(ATTR_GROUPS))
    vals = "".join(f'<span class="vl" style="--c:{c}"><span class="sw"></span>{n}</span>' for n, c in ATTR_GROUPS[0][3])
    tiles = "".join(f"""<div class="tile {"z" if stk == 0 else ""}"><div class="t"><span class="sw" style="--c:{c}"></span><b>{col} · {cap}</b><small>{sku}</small></div>
<div class="stk">{stk}<small>шт · резерв {res}</small></div><div class="ft"><span class="mut">Ціна</span><b>{pr} ₴</b></div></div>"""
                    for col, c, cap, sku, pr, stk, res in VARIANTS)
    body = f"""<div class="head"><span class="back g">{ic("chevron-left", 18)}</span><h1>Товари · <b>атрибути</b></h1>
<div class="r"><span class="pbtn g">Товари</span><span class="pbtn g">Категорії</span><span class="pbtn g">Бренди</span><span class="pbtn d">Атрибути</span></div></div>
<div class="row" style="padding-bottom:96px"><div class="g p" style="width:300px"><h3>Групи</h3><div style="margin-top:10px;display:flex;flex-direction:column;gap:4px">{gr}</div></div>
<div class="col" style="flex:1"><div class="g p"><h3>Колір <small>· кольорові плашки · 32 товари</small></h3><div class="vals" style="margin-top:14px">{vals}<span class="vl add">{ic("plus", 16)}Значення</span></div></div>
<div class="g p" style="flex:1"><h3>Варіанти «Павербанк Volt» <small>· колір × ємність · 63 шт</small></h3><div class="tiles" style="margin-top:14px">{tiles}</div></div></div></div>"""
    d = [("gen", "layers", "Згенерувати варіанти"), ("|", "", ""), ("add", "plus", "Атрибут"), ("img", "image", "Фото"), ("ok", "check", "Зберегти")]
    return f'<div class="v2"><div class="wrap">{topbar("products")}{body}</div>{dock(d, "gen")}</div>'


def build():
    return page("Варіант 2 — Тепле скло", CSS, [
        ("1-menu", "Меню вгорі + панель дій унизу, огляд замовлень", orders(), None, None), ("2-card", "Картка замовлення", card(), None, None),
        ("3-settings", "Налаштування → Статуси", settings(), None, None), ("4-attrs", "Товари → Атрибути", attributes(), None, None)])
