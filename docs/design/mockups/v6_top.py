"""Варіант 6 — «Верхнє меню + розділений екран» (Gainix / Finovia): меню вгорі, список і картка поруч, глибокий зелений."""
from common import *
import mobile

CSS = """
.v6{--ink:#0E1A16;--mut:#66756F;--line:#E3E8E5;--g:#0B5D47;--g2:#E5F2EC;--bg:#EEF1EF;font:400 14px/1.45 'Commissioner',sans-serif;color:var(--ink);background:var(--bg);width:100%;height:100%;display:flex;flex-direction:column}
.v6 .nav{height:64px;display:flex;align-items:center;gap:6px;padding:0 20px}
.v6 .brand{display:flex;align-items:center;gap:9px;font-weight:700;font-size:17px;margin-right:14px}.v6 .brand .lg{width:32px;height:32px;border-radius:50%;background:var(--ink);color:#fff;display:grid;place-items:center;font-weight:700}
.v6 .tabs{display:flex;gap:2px;background:#E2E7E4;border-radius:12px;padding:4px}
.v6 .tabs span{display:inline-flex;align-items:center;gap:7px;padding:7px 12px;border-radius:9px;font-size:13.5px;font-weight:500;color:#3C4B45;white-space:nowrap}
.v6 .tabs span.on{background:#fff;color:var(--ink);box-shadow:0 1px 3px rgba(14,26,22,.12)}.v6 .tabs em{font-style:normal;font-size:11px;font-weight:700;background:var(--g);color:#fff;border-radius:99px;padding:0 6px}
.v6 .nav .r{margin-left:auto;display:flex;align-items:center;gap:8px}
.v6 .ib{width:38px;height:38px;border-radius:50%;background:#fff;display:grid;place-items:center;color:#3C4B45;border:1px solid var(--line)}
.v6 .gbtn{display:inline-flex;align-items:center;gap:7px;height:38px;padding:0 16px;border-radius:10px;background:var(--g);color:#fff;font-weight:600;font-size:13.5px;white-space:nowrap;box-shadow:0 6px 14px -8px rgba(11,93,71,.7)}
.v6 .obtn{display:inline-flex;align-items:center;gap:7px;height:36px;padding:0 13px;border-radius:10px;background:#fff;border:1px solid var(--line);font-weight:500;font-size:13px;white-space:nowrap}
.v6 .av{width:38px;height:38px;border-radius:50%;background:#E8D5C4;display:grid;place-items:center;font-weight:700;font-size:12.5px}
.v6 .sheet{flex:1;min-height:0;background:#fff;margin:0 14px 14px;border-radius:22px;display:flex;overflow:hidden;border:1px solid var(--line)}
.v6 .list{width:420px;border-right:1px solid var(--line);display:flex;flex-direction:column;min-height:0}
.v6 .lh{padding:18px 18px 12px;display:flex;flex-direction:column;gap:12px;border-bottom:1px solid var(--line)}
.v6 .lh h2{font-size:22px;font-weight:700;letter-spacing:-.02em;display:flex;align-items:center;gap:10px}.v6 .lh h2 .r{margin-left:auto;display:flex;gap:6px}
.v6 .sb{display:flex;align-items:center;gap:8px;height:38px;padding:0 12px;border-radius:10px;border:1px solid var(--line);color:#94A19B;font-size:13px}
.v6 .chips{display:flex;gap:6px;overflow:hidden}.v6 .chip{display:inline-flex;align-items:center;gap:6px;height:30px;padding:0 11px;border-radius:99px;border:1px solid var(--line);font-size:12.5px;font-weight:500;white-space:nowrap}
.v6 .chip.on{background:var(--ink);color:#fff;border-color:var(--ink)}.v6 .chip em{font-style:normal;color:#94A19B}.v6 .chip.on em{color:#9FB2AA}
.v6 .li{display:grid;grid-template-columns:1fr auto;gap:2px 12px;padding:12px 18px;border-bottom:1px solid #F0F3F1;position:relative}
.v6 .li.on{background:var(--g2)}.v6 .li.on:before{content:"";position:absolute;left:0;top:10px;bottom:10px;width:3px;border-radius:0 3px 3px 0;background:var(--g)}
.v6 .li b{font-weight:600}.v6 .li .n{color:var(--mut);font-size:12.5px}.v6 .li .s{font-weight:700;text-align:right}.v6 .li .m{font-size:12.5px;color:var(--mut);display:flex;align-items:center;gap:8px}
.v6 .st{display:inline-flex;align-items:center;gap:5px;font-size:12px;font-weight:600;color:color-mix(in srgb,var(--c) 75%,#000)}
.v6 .st i{width:7px;height:7px;border-radius:50%;background:var(--c)}
.v6 .det{flex:1;min-width:0;display:flex;flex-direction:column;min-height:0}
.v6 .dh{padding:18px 24px;display:flex;align-items:center;gap:12px;border-bottom:1px solid var(--line)}
.v6 .dh h2{font-size:22px;font-weight:700;letter-spacing:-.02em}.v6 .dh .r{margin-left:auto;display:flex;gap:6px}
.v6 .stsel{display:inline-flex;align-items:center;gap:7px;height:32px;padding:0 12px;border-radius:9px;font-weight:600;font-size:13px;background:color-mix(in srgb,var(--c) 13%,#fff);color:color-mix(in srgb,var(--c) 75%,#000)}
.v6 .db{padding:18px 24px;display:grid;grid-template-columns:1fr 1fr;gap:14px;overflow:hidden}
.v6 .bx{border:1px solid var(--line);border-radius:16px;padding:14px 16px}.v6 .bx h4{font-size:13.5px;font-weight:700;display:flex;align-items:center;gap:8px;margin-bottom:10px}
.v6 .bx h4 .r{margin-left:auto;display:flex;gap:6px;font-weight:500}
.v6 .kv{display:grid;grid-template-columns:120px 1fr;gap:8px 12px;font-size:13.5px}.v6 .kv span{color:var(--mut)}
.v6 .gi{display:flex;align-items:center;gap:12px;padding:8px 0}.v6 .gi .ph{width:44px;height:44px;border-radius:12px;background:linear-gradient(145deg,#1d2a25,#3b4a44);display:grid;place-items:center;color:#9FD8C1;flex:none}
.v6 .gi .ph.w{background:#F0F3F1;color:#94A19B}.v6 .gi b{font-weight:600;display:block}.v6 .gi small{color:var(--mut);font-size:12px}.v6 .gi .p{margin-left:auto;font-weight:700;white-space:nowrap}
.v6 .tot{display:flex;align-items:baseline;justify-content:space-between;border-top:1px dashed var(--line);margin-top:6px;padding-top:10px}.v6 .tot b{font-size:22px;font-weight:700}
.v6 .foot{margin-top:auto;display:flex;align-items:center;gap:8px;padding:12px 24px;border-top:1px solid var(--line);background:#FAFBFA}
.v6 .foot .r{margin-left:auto;display:flex;gap:8px}
.v6 .mono{font:500 13px 'JB',monospace}
.v6 .ev{display:grid;grid-template-columns:28px 1fr auto;gap:10px;padding:6px 0;font-size:13px}.v6 .ev .ic{width:28px;height:28px;border-radius:50%;background:var(--g2);color:var(--g);display:grid;place-items:center}
.v6 .ev small{display:block;color:var(--mut);font-size:12px}.v6 .ev time{color:#94A19B;font-size:12px}
/* повна картка */
.v6 .page{flex:1;min-height:0;display:flex;flex-direction:column;padding:0 14px 14px;gap:12px}
.v6 .ph{display:flex;align-items:center;gap:12px;padding:4px 8px 0}.v6 .ph h1{font-size:26px;font-weight:700;letter-spacing:-.025em}
.v6 .ph .crumb{color:var(--mut);font-size:13px}.v6 .ph .r{margin-left:auto;display:flex;gap:8px}
.v6 .cols{display:grid;grid-template-columns:1fr 1.3fr 1fr;gap:12px;flex:1;min-height:0}
.v6 .cc{background:#fff;border:1px solid var(--line);border-radius:20px;padding:16px;display:flex;flex-direction:column;gap:12px;overflow:hidden}
.v6 .cc h3{font-size:15px;font-weight:700;display:flex;align-items:center;gap:8px}.v6 .cc h3 .r{margin-left:auto;display:flex;gap:6px;font-weight:500}
.v6 .hist{display:flex;flex-direction:column;gap:6px}.v6 .hist div{display:flex;align-items:center;gap:10px;font-size:13px;padding:8px 10px;border-radius:10px;background:#F5F7F6}
.v6 .hist div .st{margin-left:auto}
.v6 .fld label{display:block;font-size:12px;color:var(--mut);margin-bottom:4px}.v6 .fld .in{display:flex;align-items:center;gap:8px;height:38px;border:1px solid var(--line);border-radius:10px;padding:0 12px;font-size:13.5px}
.v6 .fld .in .i:last-child{margin-left:auto;color:#94A19B}
.v6 .big{font-size:40px;font-weight:700;letter-spacing:-.03em;line-height:1}
.v6 .bar{display:flex;align-items:center;gap:8px;background:var(--ink);color:#fff;border-radius:16px;padding:10px 12px}
.v6 .bar .b{display:inline-flex;align-items:center;gap:7px;height:38px;padding:0 14px;border-radius:10px;background:#1E2C27;font-size:13px;font-weight:500;white-space:nowrap}
.v6 .bar .b.g{background:#2BD49A;color:#0E1A16;font-weight:700}.v6 .bar .sep{width:1px;height:24px;background:#2C3B35}
/* налаштування */
.v6 .stab{width:250px;border-right:1px solid var(--line);padding:16px 12px;display:flex;flex-direction:column;gap:2px}
.v6 .stab span{display:flex;align-items:center;gap:10px;height:38px;padding:0 12px;border-radius:10px;color:#3C4B45;font-weight:500}
.v6 .stab span.on{background:var(--g2);color:var(--g);font-weight:600}
.v6 .acc{border:1px solid var(--line);border-radius:14px;margin-bottom:8px;overflow:hidden}
.v6 .acc .h{display:flex;align-items:center;gap:12px;padding:11px 14px}.v6 .acc .h b{font-weight:600}.v6 .acc .h .sum{margin-left:auto;display:flex;gap:6px;align-items:center;color:var(--mut);font-size:12.5px}
.v6 .acc .h .dot{width:12px;height:12px;border-radius:4px;background:var(--c)}
.v6 .mini{display:inline-flex;align-items:center;gap:5px;font-size:12px;padding:2px 8px;border-radius:7px;background:#F0F3F1;color:#3C4B45}
.v6 .acc.open{border-color:#BFDCCF;box-shadow:0 10px 24px -18px rgba(11,93,71,.6)}.v6 .acc.open .h{background:var(--g2)}
.v6 .acc .bd{padding:14px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.v6 .rule{border:1px solid var(--line);border-radius:12px;padding:12px}.v6 .rule .t{display:flex;align-items:center;gap:8px;font-weight:600;font-size:13px;margin-bottom:8px}
.v6 .rule .t .sw{margin-left:auto}.v6 .rule p{font-size:12.5px;color:var(--mut)}
.v6 .sw{display:inline-block;width:32px;height:18px;border-radius:99px;background:var(--g);position:relative}.v6 .sw:after{content:"";position:absolute;right:2px;top:2px;width:14px;height:14px;border-radius:50%;background:#fff}
.v6 .sw.off{background:#D3DAD6}.v6 .sw.off:after{right:auto;left:2px}
.v6 .sms{background:#F5F7F6;border-radius:10px;padding:10px;font-size:12.5px;margin-top:8px;color:#3C4B45}
/* атрибути */
.v6 .ptabs{display:flex;gap:18px;border-bottom:1px solid var(--line);padding:0 24px}
.v6 .ptabs span{padding:12px 0;font-weight:500;color:var(--mut);border-bottom:2px solid transparent;margin-bottom:-1px;display:inline-flex;gap:7px;align-items:center}
.v6 .ptabs span.on{color:var(--g);border-color:var(--g);font-weight:600}
.v6 .vb{display:grid;grid-template-columns:330px 1fr;flex:1;min-height:0}
.v6 .pick{border-right:1px solid var(--line);padding:18px;display:flex;flex-direction:column;gap:14px}
.v6 .pick h4{font-size:13.5px;font-weight:700;display:flex;align-items:center;gap:8px}.v6 .pick h4 .r{margin-left:auto;color:var(--mut);font-weight:400;font-size:12px}
.v6 .opts{display:flex;flex-wrap:wrap;gap:6px}.v6 .op{display:inline-flex;align-items:center;gap:6px;height:32px;padding:0 11px;border-radius:9px;border:1px solid var(--line);font-size:13px}
.v6 .op.on{border-color:var(--g);background:var(--g2);color:var(--g);font-weight:600}.v6 .op i{width:14px;height:14px;border-radius:4px;background:var(--c);box-shadow:inset 0 0 0 1px rgba(0,0,0,.12)}
.v6 .vlist{padding:18px 24px;display:grid;grid-template-columns:repeat(2,1fr);gap:10px;align-content:start}
.v6 .vc{border:1px solid var(--line);border-radius:14px;padding:12px;display:grid;grid-template-columns:52px 1fr auto;gap:12px;align-items:center}
.v6 .vc .ph{width:52px;height:52px;border-radius:12px;background:var(--c);display:grid;place-items:center;color:rgba(255,255,255,.7);box-shadow:inset 0 0 0 1px rgba(0,0,0,.08)}
.v6 .vc b{font-weight:600;display:block}.v6 .vc small{color:var(--mut);font-size:12px}
.v6 .vc .nums{display:flex;gap:6px;margin-top:6px}.v6 .in2{display:inline-flex;align-items:center;height:28px;padding:0 8px;border:1px solid var(--line);border-radius:8px;font-size:12.5px;font-weight:600}
.v6 .stk{text-align:right}.v6 .stk b{font-size:20px}.v6 .stk.z b{color:#D14343}
"""

NAVT = [("home", "Головна", "house"), ("leads", "Ліди", "inbox"), ("orders", "Замовлення", "receipt-text"), ("board", "Дошка", "square-kanban"),
        ("customers", "Покупці", "contact"), ("products", "Товари", "package"), ("warehouse", "Склад", "boxes"), ("money", "Гроші", "wallet"),
        ("stats", "Аналітика", "chart-column-stacked"), ("more", "Ще", "chevron-down")]


def nav(on):
    t = "".join(f'<span class="{"on" if k == on else ""}">{ic(i, 16)}{n}{"<em>5</em>" if k == "leads" else ""}</span>' for k, n, i in NAVT)
    return f"""<div class="nav"><div class="brand"><span class="lg">m</span>mdmy</div><div class="tabs">{t}</div>
<div class="r"><span class="ib">{ic("search", 17)}</span><span class="ib">{ic("settings", 17)}</span><span class="gbtn">{ic("plus", 16, 2.2)}Нове</span><span class="av">ОЛ</span></div></div>"""


def split():
    items = ""
    for n, o in enumerate(ORDERS[:9]):
        items += f"""<div class="li {"on" if n == 0 else ""}"><b>{o[1]}</b><span class="s">{o[5]} ₴</span><span class="m">№{o[0]} · {o[3]}</span><span class="n">{o[10]}</span>
<span class="m">{pill(o[6])}<span>· {o[7]}</span></span><span></span></div>"""
    lst = f"""<div class="list"><div class="lh"><h2>Замовлення<span class="r"><span class="obtn" style="height:32px">{ic("list-filter", 15)}</span><span class="obtn" style="height:32px">{ic("printer", 15)}</span></span></h2>
<div class="sb">{ic("search", 16)}Телефон, ПІБ, ТТН або №</div><div class="chips"><span class="chip on">Усі <em>248</em></span><span class="chip">Підтверджено <em>31</em></span><span class="chip">Відправлено <em>57</em></span></div></div>
<div style="overflow:hidden">{items}</div></div>"""
    o = ORDER
    goods = "".join(f'<div class="gi" style="{"padding-left:28px" if up else ""}"><span class="ph {"w" if up else ""}">{ic("link" if up else "zap", 18)}</span><span><b>{nm}</b><small>{var} · {q} шт</small></span><span class="p">{s} ₴</span></div>' for nm, var, sku, q, p, s, up in o["items"])
    ev = "".join(f'<div class="ev"><span class="ic">{ic(i, 14)}</span><span>{t}<small>{d}</small></span><time>{tm}</time></div>' for tm, t, d, i in TIMELINE[2:])
    det = f"""<div class="det"><div class="dh"><div><div style="color:var(--mut);font-size:12.5px">№1482 · сьогодні, 14:32 · Instagram</div><h2>{o["name"]}</h2></div>
<div class="r"><span class="stsel" style="--c:#10B981">{ic("circle-check-big", 15)}Підтверджено{ic("chevron-down", 14)}</span><span class="obtn">{ic("arrow-up-right", 15)}Відкрити</span></div></div>
<div class="db"><div class="bx"><h4>{ic("user", 15)}Покупець<span class="r"><span class="obtn" style="height:28px;padding:0 8px">{ic("phone", 14)}</span><span class="obtn" style="height:28px;padding:0 8px">{ic("message-circle", 14)}</span></span></h4>
<div class="kv"><span>Телефон</span><b style="font-weight:500">{o["phone"]}</b><span>Історія</span><b style="font-weight:500">4 замовлення · викуп 75%</b><span>Менеджер</span><b style="font-weight:500">Олена Литвин</b><span>Юрособа</span><b style="font-weight:500">ФОП Максимчук О. В.</b></div></div>
<div class="bx"><h4>{ic("truck", 15)}Нова Пошта<span class="r"><span class="st" style="--c:#F97316"><i></i>Прямує до відділення</span></span></h4>
<div class="kv"><span>Куди</span><b style="font-weight:500">Київ, №12</b><span>ТТН</span><span class="mono" style="color:var(--ink)">20450913998365</span><span>Очікується</span><b style="font-weight:500">30.10, після 13:00</b><span>Післяплата</span><b style="font-weight:500">1 597 ₴ · контроль оплати</b></div></div>
<div class="bx"><h4>{ic("package", 15)}Товари</h4>{goods}<div class="tot"><span style="color:var(--mut)">Разом</span><b>1 797 ₴</b></div></div>
<div class="bx"><h4>{ic("clock-fading", 15)}Останнє</h4>{ev}</div>
<div class="bx"><h4>{ic("wallet", 15)}Оплата<span class="r"><span class="st" style="--c:#16A34A"><i></i>Чек: передоплата</span></span></h4><div class="kv"><span>Вид</span><b style="font-weight:500">Контроль оплати НП</b><span>Передоплата</span><b style="font-weight:500">200 ₴ · Monobank</b><span>При отриманні</span><b>1 597 ₴</b></div></div>
<div class="bx"><h4>{ic("message-square", 15)}Коментар і позначки</h4><div style="font-size:13.5px">Зателефонувати після 18:00, подарункове пакування.</div><div style="margin-top:10px;display:flex;gap:6px"><span class="chip" style="height:26px">VIP</span><span class="chip" style="height:26px">Подарунок</span><span class="chip" style="height:26px;color:var(--g)">+ позначка</span></div></div></div>
<div class="foot"><span class="obtn">{ic("printer", 15)}Друк{ic("chevron-down", 13)}</span><span class="obtn">{ic("tag", 15)}Наклейка</span><span class="obtn">{ic("receipt", 15)}Чек</span>
<div class="r"><span class="obtn">{ic("message-square", 15)}SMS</span><span class="gbtn">{ic("truck", 15)}Створити ТТН</span></div></div></div>"""
    return f'<div class="v6">{nav("orders")}<div class="sheet">{lst}{det}</div></div>'


def full():
    o = ORDER
    hist = "".join(f'<div><span style="color:var(--mut)">№{n}</span><b style="font-weight:500">{p}</b>{pill(s)}</div>' for n, p, s in [(1391, "Навушники TWS Pro", "got"), (1207, "Павербанк 10000", "ref"), (1102, "Кабель ×3", "got")])
    goods = "".join(f'<div class="gi" style="{"padding-left:28px" if up else ""}"><span class="ph {"w" if up else ""}">{ic("link" if up else "zap", 18)}</span><span><b>{nm}</b><small>{var} · {sku}</small></span><span class="in2" style="margin-left:auto">− {q} +</span><span class="p" style="margin-left:12px;width:70px;text-align:right">{s} ₴</span></div>' for nm, var, sku, q, p, s, up in o["items"])
    fld = lambda l, v, i: f'<div class="fld"><label>{l}</label><div class="in">{ic(i, 15)}{v}{ic("chevron-down", 14)}</div></div>'
    ev = "".join(f'<div class="ev"><span class="ic">{ic(i, 14)}</span><span>{t}<small>{d}</small></span><time>{tm}</time></div>' for tm, t, d, i in TIMELINE)
    body = f"""<div class="page"><div class="ph"><span class="ib">{ic("arrow-left", 17)}</span><div><div class="crumb">Замовлення / №1482 · 29.10.2026, 14:32</div><h1>{o["name"]}</h1></div>
<div class="r"><span class="stsel" style="--c:#10B981;height:38px">{ic("circle-check-big", 15)}Підтверджено{ic("chevron-down", 14)}</span><span class="obtn" style="height:38px">{ic("user", 15)}Олена Литвин</span><span class="obtn" style="height:38px">{ic("landmark", 15)}ФОП Максимчук О. В.</span></div></div>
<div class="cols"><div class="cc"><h3>{ic("user", 16)}Покупець</h3>{fld("ПІБ — одним рядком", o["name"], "user")}{fld("Телефон", o["phone"], "phone")}{fld("Джерело", "Instagram → Інтернет-магазин", "globe")}
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px">{"".join(f'<div style="background:#F5F7F6;border-radius:12px;padding:10px"><div style="font-size:12px;color:var(--mut)">{a}</div><b style="font-size:18px">{b}</b></div>' for a, b in CUSTOMER[:3])}</div>
<div style="font-size:12.5px;color:var(--mut);font-weight:600">Попередні замовлення</div><div class="hist">{hist}</div></div>
<div class="cc"><h3>{ic("package", 16)}Товари<span class="r"><span class="obtn" style="height:30px">{ic("plus", 14)}Товар</span><span class="obtn" style="height:30px">{ic("sparkles", 14)}Допродаж</span></span></h3>{goods}
<div style="border:1px dashed #BFDCCF;background:var(--g2);border-radius:12px;padding:10px 12px;font-size:13px;color:var(--g);display:flex;gap:8px;align-items:center">{ic("sparkles", 15)}Часто беруть разом: чохол для павербанка · 249 ₴<b style="margin-left:auto">Додати</b></div>
<h3 style="margin-top:4px">{ic("truck", 16)}Доставка<span class="r"><span class="st" style="--c:#F97316"><i></i>Прямує до відділення</span></span></h3>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">{fld("Служба", "Нова Пошта", "truck")}{fld("Відділення", "Київ, №12", "map-pin")}{fld("Платник", "Отримувач", "wallet")}
<div class="fld"><label>ТТН</label><div class="in"><span class="mono">20450913998365</span>{ic("copy", 14)}</div></div></div></div>
<div class="cc"><h3>{ic("wallet", 16)}Оплата</h3><div><div style="color:var(--mut);font-size:12.5px">До сплати при отриманні</div><div class="big">1 597 ₴</div></div>
<div class="kv"><span>Товари</span><b style="font-weight:500">1 797 ₴</b><span>Передоплата</span><b style="font-weight:500">200 ₴ · Monobank</b><span>Вид оплати</span><b style="font-weight:500">Контроль оплати НП</b><span>Чек</span><b style="font-weight:500;color:var(--g)">Передоплата ✓</b></div>
<h3 style="margin-top:4px">{ic("clock-fading", 16)}Історія</h3><div>{ev}</div></div></div>
<div class="bar"><span class="b">{ic("printer", 15)}Друк{ic("chevron-down", 13)}</span><span class="b">{ic("tag", 15)}Наклейка</span><span class="b">{ic("receipt", 15)}Фіскалізувати</span><span class="sep"></span>
<span class="b">{ic("phone", 15)}Дзвінок</span><span class="b">{ic("message-square", 15)}SMS</span><span class="b">{ic("message-circle", 15)}Viber</span>
<span style="margin-left:auto;color:#9FB2AA;font-size:12.5px">Збережено щойно</span><span class="b">{ic("check", 15)}Зберегти</span><span class="b g">{ic("truck", 15)}Створити ТТН</span></div></div>"""
    return f'<div class="v6">{nav("orders")}{body}</div>'


def settings():
    st = "".join(f'<span class="{"on" if n == "Статуси" else ""}">{ic(i, 17)}{n}</span>' for n, i in SETTINGS)
    acc = ""
    for code, s, stock, chk, sms in STATUS_ROWS:
        n, c = ST[code]
        minis = "".join(f'<span class="mini">{ic(i, 12)}{v}</span>' for i, v in (("boxes", stock), ("receipt", chk), ("message-square", sms)) if v != "—")
        if code == "sent":
            acc += f"""<div class="acc open"><div class="h"><span class="dot" style="--c:{c}"></span><b>{n}</b><span class="mini">{s}</span><span class="sum">{ic("chevron-down", 16)}</span></div>
<div class="bd"><div class="rule"><div class="t">{ic("boxes", 15)}Склад<span class="sw"></span></div><p>Списати товар і зняти резерв, коли замовлення переходить у цей статус.</p></div>
<div class="rule"><div class="t">{ic("receipt", 15)}Чек Checkbox<span class="sw"></span></div><p>Чек «Продаж» на касі юрособи замовлення. Якщо була передоплата — на решту суми.</p></div>
<div class="rule"><div class="t">{ic("message-square", 15)}SMS / Viber<span class="sw"></span></div><div class="sms">Ваше замовлення №{{номер}} відправлено. ТТН {{ттн}}, сума {{сума}} ₴.</div></div>
<div class="rule"><div class="t">{ic("truck", 15)}Коди Нової Пошти<span class="sw"></span></div><p>Ставити цей статус, коли НП повертає код 1 або 2.</p></div>
<div class="rule"><div class="t">{ic("send", 15)}Telegram<span class="sw off"></span></div><p>Повідомлення в чат складу не надсилається.</p></div>
<div class="rule"><div class="t">{ic("store", 15)}Маркетплейси<span class="sw"></span></div><p>Rozetka: «Передано в доставку», Prom: «Виконується».</p></div></div></div>"""
        else:
            acc += f'<div class="acc"><div class="h"><span class="dot" style="--c:{c}"></span><b>{n}</b><span class="mini">{s}</span><span class="sum">{minis or "без дій"}{ic("chevron-right", 16)}</span></div></div>'
    body = f"""<div class="sheet"><div class="stab"><div style="font-size:20px;font-weight:700;padding:4px 12px 12px">Налаштування</div>{st}</div>
<div style="flex:1;padding:18px 24px;overflow:hidden"><div style="display:flex;align-items:center;gap:10px;margin-bottom:14px"><h2 style="font-size:20px;font-weight:700">Статуси</h2>
<span style="color:var(--mut)">· натисніть статус, щоб налаштувати, що CRM робить сама</span><span style="margin-left:auto" class="obtn">{ic("plus", 15)}Статус</span><span class="gbtn">{ic("check", 15)}Зберегти</span></div>{acc}</div></div>"""
    return f'<div class="v6">{nav("more")}{body}</div>'


def attributes():
    groups = ""
    for g, i, t, v, u in ATTR_GROUPS[:3]:
        on = {"Колір": ["Чорний", "Білий", "Синій"], "Ємність": ["10 000 мА·год", "20 000 мА·год"]}.get(g, [])
        ops = "".join(f'<span class="op {"on" if x in on else ""}">{f"<i style=--c:{c}></i>" if c else ""}{x}</span>' for x, c in v)
        groups += f'<div><h4>{ic(i, 15)}{g}<span class="r">{len(on)} з {len(v)}</span></h4><div class="opts" style="margin-top:8px">{ops}</div></div>'
    vc = ""
    for col, c, cap, sku, pr, stk, res in VARIANTS:
        vc += f"""<div class="vc"><span class="ph" style="--c:{c}">{ic("zap", 18)}</span><span><b>{col} · {cap} мА·год</b><small class="mono" style="font-size:11.5px">{sku}</small>
<div class="nums"><span class="in2">{pr} ₴</span><span class="in2" style="color:var(--mut);font-weight:500">собів. {"1 020" if "20" in cap else "640"} ₴</span></div></span>
<span class="stk {"z" if stk == 0 else ""}"><b>{stk}</b><small style="display:block;color:var(--mut);font-size:12px">резерв {res}</small></span></div>"""
    body = f"""<div class="sheet" style="flex-direction:column"><div class="dh"><span class="gi" style="padding:0"><span class="ph">{ic("zap", 20)}</span></span><div><div style="color:var(--mut);font-size:12.5px">Товари / Павербанки</div><h2>Павербанк Volt</h2></div>
<div class="r"><span class="obtn">{ic("eye", 15)}На сайті</span><span class="obtn">{ic("trash", 15)}В архів</span><span class="gbtn">{ic("check", 15)}Зберегти</span></div></div>
<div class="ptabs"><span>{ic("file-text", 15)}Основне</span><span>{ic("image", 15)}Фото 4</span><span class="on">{ic("layers", 15)}Варіанти 6</span><span>{ic("truck", 15)}Доставка</span><span>{ic("boxes", 15)}Склад</span></div>
<div class="vb"><div class="pick"><div style="font-size:13px;color:var(--mut)">Оберіть значення — CRM складе всі комбінації. Наявні варіанти не зміняться.</div>{groups}
<span class="gbtn" style="justify-content:center">{ic("layers", 15)}Скласти 6 варіантів</span><span class="obtn" style="justify-content:center">{ic("settings", 15)}Керувати атрибутами</span></div>
<div class="vlist">{vc}</div></div></div>"""
    return f'<div class="v6">{nav("products")}{body}</div>'


def build():
    return page("Варіант 6 — Верхнє меню", CSS + mobile.CSS6, [
        ("1-menu", "Меню вгорі + список і картка поруч", split(), None, None), ("2-card", "Повна картка: три колонки + панель дій", full(), None, None),
        ("3-settings", "Налаштування — статус розкривається з правилами", settings(), None, None), ("4-attrs", "Атрибути у товарі: конструктор варіантів", attributes(), None, None),
        ("5-mobile", "Телефон: список, картка, статус із правилами, варіанти", mobile.m6(), None, None)])
