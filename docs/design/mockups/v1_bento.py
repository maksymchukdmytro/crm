"""Варіант 1 — «Бенто-лайм» (Fynix / TrustVest): сірий фон, білі блоки-бенто, лайм + темно-зелений."""
from common import *
import mobile

CSS = """
.v1{--bg:#ECEEE9;--card:#fff;--ink:#0F231B;--forest:#0F3B2C;--lime:#C6F36D;--lime2:#EAF9CF;--mut:#6A786F;--line:#E2E6DF;
  font:500 14px/1.45 'Manrope',sans-serif;color:var(--ink);background:var(--bg);width:100%;height:100%;display:flex}
.v1 .side{width:244px;padding:22px 16px 16px;display:flex;flex-direction:column;gap:14px}
.v1 .brand{display:flex;align-items:center;gap:10px;font-weight:800;font-size:18px;letter-spacing:-.02em}
.v1 .logo{width:34px;height:34px;border-radius:10px;background:var(--forest);color:var(--lime);display:grid;place-items:center;font-weight:800}
.v1 .ws{display:flex;align-items:center;gap:10px;background:var(--card);border-radius:14px;padding:9px 10px;border:1px solid var(--line)}
.v1 .ws .av{width:30px;height:30px;border-radius:9px;background:var(--lime2);display:grid;place-items:center;color:var(--forest)}
.v1 .ws b{display:block;font-size:13px}.v1 .ws small{color:var(--mut);font-size:11.5px}.v1 .ws .i:last-child{margin-left:auto;color:var(--mut)}
.v1 .acts{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.v1 .btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;height:38px;padding:0 14px;border-radius:12px;font-weight:700;font-size:13px;border:1px solid var(--line);background:#fff;color:var(--ink);white-space:nowrap}
.v1 .btn.f{background:var(--forest);color:#fff;border-color:var(--forest)}.v1 .btn.l{background:var(--lime);border-color:var(--lime);color:var(--forest)}
.v1 .search{display:flex;align-items:center;gap:8px;height:38px;padding:0 12px;border-radius:12px;background:#F6F7F4;color:var(--mut);font-size:13px;border:1px solid var(--line)}
.v1 .search kbd{margin-left:auto;font:600 11px 'Manrope';background:#fff;border:1px solid var(--line);border-radius:6px;padding:1px 6px}
.v1 .nav{display:flex;flex-direction:column;gap:8px;overflow:hidden}
.v1 .grp small{display:block;color:var(--mut);font-size:11.5px;font-weight:600;margin:0 10px 4px}
.v1 .it{display:flex;align-items:center;gap:11px;height:32px;padding:0 10px;border-radius:11px;color:#33473D;font-weight:600}
.v1 .it .i{color:#7E8C84}.v1 .it.on{background:#fff;color:var(--ink);box-shadow:0 1px 0 var(--line),0 6px 16px -10px rgba(15,59,44,.35)}
.v1 .it.on .i{color:var(--forest)}.v1 .it em{margin-left:auto;font-style:normal;font-size:11.5px;font-weight:700;padding:1px 8px;border-radius:99px;background:#DDE2DA;color:#33473D}
.v1 .it em.hot{background:var(--lime);color:var(--forest)}
.v1 .promo{margin-top:auto;background:var(--forest);color:#fff;border-radius:18px;padding:16px;position:relative;overflow:hidden}
.v1 .promo:after{content:"";position:absolute;right:-30px;top:-30px;width:110px;height:110px;border-radius:50%;background:radial-gradient(circle,var(--lime) 0,rgba(198,243,109,0) 70%);opacity:.45}
.v1 .promo b{font-size:22px;font-weight:800;letter-spacing:-.03em;display:block}.v1 .promo p{color:#B8CCC2;font-size:12.5px;margin:2px 0 12px}
.v1 .promo .btn{height:34px;width:100%;background:var(--lime);border:0;color:var(--forest)}
.v1 .me{display:flex;align-items:center;gap:10px;padding:4px 6px}.v1 .me .av{width:34px;height:34px;border-radius:50%;background:#F2C6A0;display:grid;place-items:center;font-weight:800;font-size:13px;color:#5B3A1E}
.v1 .me b{display:block;font-size:13px}.v1 .me small{color:var(--mut);font-size:11.5px}.v1 .me .i{margin-left:auto;color:var(--mut)}
.v1 .main{flex:1;min-width:0;padding:22px 24px 22px 8px;display:flex;flex-direction:column;gap:16px}
.v1 .top{display:flex;align-items:flex-end;gap:12px}
.v1 h1{font-size:28px;font-weight:800;letter-spacing:-.03em;line-height:1.1}.v1 .sub{color:var(--mut);font-size:13px;margin-top:4px}
.v1 .top .r{margin-left:auto;display:flex;gap:8px;align-items:center}
.v1 .ib{width:38px;height:38px;border-radius:12px;background:#fff;border:1px solid var(--line);display:grid;place-items:center;color:#33473D;position:relative}
.v1 .ib .dot{position:absolute;top:8px;right:9px;width:7px;height:7px;border-radius:50%;background:#E5484D;border:2px solid #fff}
.v1 .card{background:var(--card);border-radius:20px;padding:18px;border:1px solid var(--line)}
.v1 .ch{display:flex;align-items:center;gap:10px;margin-bottom:12px}.v1 .ch h3{font-size:15.5px;font-weight:800;letter-spacing:-.01em}
.v1 .ch .r{margin-left:auto;display:flex;gap:6px;align-items:center}
.v1 .chip{display:inline-flex;align-items:center;gap:6px;height:30px;padding:0 11px;border-radius:10px;border:1px solid var(--line);font-size:12.5px;font-weight:600;color:#33473D;background:#fff}
.v1 .kpis{display:grid;grid-template-columns:1.25fr 1fr 1fr 1fr;gap:14px}
.v1 .kpi .lab{display:flex;align-items:center;gap:8px;color:var(--mut);font-weight:600;font-size:13px}
.v1 .kpi .lab .i{padding:6px;width:28px;height:28px;border-radius:9px;background:var(--lime2);color:var(--forest)}
.v1 .kpi b{display:block;font-size:30px;font-weight:800;letter-spacing:-.035em;margin:10px 0 2px}
.v1 .kpi small{font-size:12px;color:var(--mut)}.v1 .up{color:#178A52;font-weight:700}.v1 .dn{color:#D14343;font-weight:700}
.v1 .kpi.hero{background:var(--lime);border-color:var(--lime);position:relative;overflow:hidden}
.v1 .kpi.hero .lab{color:var(--forest)}.v1 .kpi.hero .lab .i{background:rgba(255,255,255,.55)}
.v1 .kpi.hero b{font-size:34px}.v1 .kpi.hero small{color:#2D5A40}
.v1 .kpi.hero:after{content:"";position:absolute;right:-40px;bottom:-60px;width:180px;height:180px;border-radius:50%;border:26px solid rgba(15,59,44,.07)}
.v1 .seg{display:flex;gap:4px;background:#F2F4EF;border-radius:12px;padding:4px}
.v1 .seg span{padding:6px 11px;border-radius:9px;font-size:12.5px;font-weight:700;color:#55665C;white-space:nowrap}
.v1 .seg span em{font-style:normal;color:#97A39B;margin-left:5px;font-weight:600}
.v1 .seg span.on{background:#fff;color:var(--ink);box-shadow:0 1px 3px rgba(15,35,27,.12)}
.v1 table{width:100%;border-collapse:collapse}
.v1 th{font-size:12px;color:var(--mut);font-weight:600;text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}
.v1 td{padding:9px 10px;border-bottom:1px solid #F0F2EE;font-size:13px;white-space:nowrap}
.v1 tr.sel td{background:#F7FCEB}
.v1 .cb{width:16px;height:16px;border-radius:5px;border:1.5px solid #C8CFC9;display:inline-block;vertical-align:middle}
.v1 .cb.on{background:var(--forest);border-color:var(--forest);color:var(--lime)}
.v1 .num{font-weight:700}.v1 .m{color:var(--mut)}.v1 .sum{font-weight:800;text-align:right}
.v1 .st{display:inline-flex;align-items:center;gap:6px;height:24px;padding:0 9px;border-radius:8px;font-size:12px;font-weight:700;
  color:color-mix(in srgb,var(--c) 75%,#000);background:color-mix(in srgb,var(--c) 13%,#fff)}
.v1 .st i{width:6px;height:6px;border-radius:50%;background:var(--c)}
.v1 .src{display:inline-flex;align-items:center;gap:6px;color:#33473D}
.v1 .src i{width:8px;height:8px;border-radius:3px;background:var(--c)}
.v1 .ups{font-size:11px;font-weight:700;color:var(--forest);background:var(--lime2);padding:1px 6px;border-radius:6px;margin-left:6px}
.v1 .ws2{display:inline-flex;align-items:center;gap:7px;height:38px;padding:0 12px;border-radius:12px;background:#fff;border:1px solid var(--line);font-weight:700;font-size:13px}
.v1 .me2{width:38px;height:38px;border-radius:50%;background:#F2C6A0;display:grid;place-items:center;font-weight:800;font-size:13px;color:#5B3A1E}
.v1 .cb.on{display:inline-grid;place-items:center}
.v1 .prev{margin-top:14px;display:flex;flex-direction:column;gap:6px}.v1 .prev div{display:flex;gap:10px;align-items:center;font-size:12.5px;padding:7px 10px;border-radius:10px;border:1px solid #F0F2EE}
.v1 .prev div b{font-weight:700}.v1 .prev div .st{margin-left:auto}
/* картка */
.v1 .og{display:grid;grid-template-columns:1fr 1fr 330px;grid-template-rows:auto 1fr;gap:14px;flex:1;min-height:0}
.v1 .kv{display:grid;grid-template-columns:auto 1fr;gap:9px 14px;font-size:13px}.v1 .kv span{color:var(--mut)}.v1 .kv b{font-weight:700}
.v1 .cust{display:flex;gap:12px;align-items:center}.v1 .cust .av{width:46px;height:46px;border-radius:14px;background:#F2C6A0;display:grid;place-items:center;font-weight:800;color:#5B3A1E}
.v1 .cust b{font-size:16px;font-weight:800;display:block;letter-spacing:-.01em}.v1 .cust small{color:var(--mut)}
.v1 .stats{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:14px}
.v1 .stats div{background:#F4F6F2;border-radius:12px;padding:9px 10px}.v1 .stats span{display:block;color:var(--mut);font-size:11.5px}.v1 .stats b{font-size:16px;font-weight:800}
.v1 .goods .row{display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid #F0F2EE}
.v1 .goods .ph{width:46px;height:46px;border-radius:12px;background:linear-gradient(145deg,#23262a,#3a3f45);display:grid;place-items:center;color:#9aa}
.v1 .goods .ph.w{background:linear-gradient(145deg,#f4f4f2,#dcdcd8);color:#999}
.v1 .goods .nm{flex:1;min-width:0}.v1 .goods .nm b{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v1 .goods .nm small{white-space:nowrap}.v1 .goods .nm b{display:block;font-weight:700}.v1 .goods .nm small{color:var(--mut);font-size:12px}
.v1 .goods .q{white-space:nowrap;display:flex;align-items:center;gap:6px;background:#F4F6F2;border-radius:10px;padding:4px 8px;font-weight:700}
.v1 .goods .p{width:84px;text-align:right;font-weight:800}
.v1 .goods .sub2{margin-left:58px}.v1 .goods .add{display:flex;gap:8px;margin-top:12px}
.v1 .tot{background:var(--forest);color:#fff;border:0;display:flex;flex-direction:column}
.v1 .tot .big{font-size:42px;font-weight:800;letter-spacing:-.04em;line-height:1;margin:6px 0 4px}.v1 .tot .big small{font-size:20px;color:var(--lime)}
.v1 .tot .ln{display:flex;justify-content:space-between;font-size:13px;color:#B8CCC2;padding:6px 0;border-bottom:1px solid rgba(255,255,255,.08)}
.v1 .tot .ln b{color:#fff}.v1 .tot .btns{margin-top:auto;display:grid;grid-template-columns:1fr 1fr;gap:8px;padding-top:14px}
.v1 .tot .btn{background:rgba(255,255,255,.08);border-color:rgba(255,255,255,.12);color:#fff}.v1 .tot .btn.l{background:var(--lime);color:var(--forest)}
.v1 .track{display:flex;gap:4px;margin:12px 0 8px}.v1 .track i{flex:1;height:6px;border-radius:9px;background:#E6EAE3}.v1 .track i.on{background:var(--forest)}.v1 .track i.cur{background:var(--lime)}
.v1 .ttn{display:flex;align-items:center;gap:10px;background:#F4F6F2;border-radius:12px;padding:10px 12px;margin-top:10px}
.v1 .ttn b{font:700 14px 'JB',monospace;letter-spacing:.02em}.v1 .ttn .r{margin-left:auto;display:flex;gap:6px;color:var(--mut)}
.v1 .tl{display:flex;flex-direction:column;gap:0}
.v1 .tl .e{display:grid;grid-template-columns:30px 1fr auto;gap:10px;padding:7px 0;position:relative}
.v1 .tl .e .ic{width:30px;height:30px;border-radius:10px;background:#F4F6F2;display:grid;place-items:center;color:var(--forest)}
.v1 .tl .e b{font-size:13px;font-weight:700;display:block}.v1 .tl .e small{color:var(--mut);font-size:12px}.v1 .tl .e time{color:var(--mut);font-size:12px}
.v1 .hdr2{display:flex;align-items:center;gap:10px}
.v1 .hdr2 .st{height:32px;padding:0 12px;font-size:13px;border-radius:10px}
/* налаштування */
.v1 .setw{display:grid;grid-template-columns:240px 1fr;gap:14px;flex:1;min-height:0}
.v1 .sl{padding:10px}.v1 .sl .it{height:38px}
.v1 .sgrp{margin-bottom:14px}.v1 .sgrp h4{font-size:13px;font-weight:800;margin:0 0 8px;display:flex;align-items:center;gap:8px}
.v1 .sgrp h4 em{font-style:normal;color:var(--mut);font-weight:600}
.v1 .srow{display:grid;grid-template-columns:22px 210px 1fr 1fr 1fr 44px;align-items:center;gap:12px;padding:8px 10px;border-radius:12px;background:#F7F8F5;margin-bottom:6px;font-size:13px}
.v1 .srow>*{justify-self:start}.v1 .srow .i.g{color:#B3BCB5}.v1 .tag{display:inline-flex;align-items:center;gap:5px;font-size:12px;font-weight:700;color:#33473D;background:#fff;border:1px solid var(--line);border-radius:8px;padding:2px 8px}
.v1 .tag.n{color:#A5AEA8;background:none;border-color:transparent}
.v1 .tog{display:inline-block;vertical-align:middle;width:36px;height:21px;border-radius:99px;background:var(--forest);position:relative}.v1 .tog:after{content:"";position:absolute;right:3px;top:3px;width:15px;height:15px;border-radius:50%;background:var(--lime)}
.v1 .tog.off{background:#D5DBD5}.v1 .tog.off:after{right:auto;left:3px;background:#fff}
.v1 .shead{display:grid;grid-template-columns:22px 210px 1fr 1fr 1fr 44px;gap:12px;padding:0 10px 6px;font-size:12px;color:var(--mut);font-weight:600}
/* атрибути */
.v1 .tabs2{display:flex;gap:4px;background:#fff;border:1px solid var(--line);border-radius:14px;padding:4px;align-self:flex-start}
.v1 .tabs2 span{padding:7px 14px;border-radius:10px;font-weight:700;font-size:13px;color:#55665C}.v1 .tabs2 span.on{background:var(--forest);color:#fff}
.v1 .aw{display:grid;grid-template-columns:300px 1fr;gap:14px;flex:1;min-height:0}
.v1 .ag{display:flex;align-items:center;gap:12px;padding:12px;border-radius:14px;border:1px solid transparent;margin-bottom:6px}
.v1 .ag.on{background:#F7FCEB;border-color:#D9F0B0}.v1 .ag .ic{width:38px;height:38px;border-radius:12px;background:#F4F6F2;display:grid;place-items:center;color:var(--forest)}
.v1 .ag.on .ic{background:var(--lime)}.v1 .ag b{display:block;font-weight:800}.v1 .ag small{color:var(--mut);font-size:12px}
.v1 .ag .i:last-child{margin-left:auto;color:#B3BCB5}
.v1 .vals{display:flex;flex-wrap:wrap;gap:8px}
.v1 .val{display:inline-flex;align-items:center;gap:8px;height:38px;padding:0 12px 0 8px;border-radius:12px;border:1px solid var(--line);font-weight:700;background:#fff}
.v1 .val .sw{width:22px;height:22px;border-radius:7px;background:var(--c);box-shadow:inset 0 0 0 1px rgba(0,0,0,.08)}
.v1 .val .i{color:#B3BCB5}.v1 .val.add{border-style:dashed;color:var(--mut);padding:0 12px}
.v1 .vm td{padding:8px 10px}.v1 .sw2{display:inline-block;width:14px;height:14px;border-radius:5px;background:var(--c);vertical-align:-2px;margin-right:6px;box-shadow:inset 0 0 0 1px rgba(0,0,0,.1)}
.v1 .bar{display:inline-block;width:70px;height:6px;border-radius:9px;background:#E9ECE6;vertical-align:middle;margin-left:8px;overflow:hidden}
.v1 .bar i{display:block;height:100%;background:var(--forest);border-radius:9px}.v1 .bar i.lo{background:#E5A23A}.v1 .bar i.z{background:#E5484D}
.v1 .inp{display:inline-flex;align-items:center;height:30px;padding:0 10px;border-radius:9px;border:1px solid var(--line);background:#fff;font-weight:700;min-width:84px}
.v1 .mono{font:600 12.5px 'JB',monospace;color:#33473D}
"""

SRC = {"Instagram": "#E1306C", "Лендинг": "#0F3B2C", "Rozetka": "#00A046", "Facebook": "#1877F2", "Prom": "#7B3FE4", "TikTok": "#111"}


def side(active):
    groups = ""
    for g, items in NAV:
        its = "".join(
            f'<div class="it {"on" if k == active else ""}">{ic(i, 18)}{n}'
            + (f'<em class="{"hot" if k == "leads" else ""}">{c}</em>' if c else "") + "</div>" for k, n, i, c in items)
        groups += f'<div class="grp"><small>{g}</small>{its}</div>'
    return f"""<aside class="side">
<div class="brand"><span class="logo">m</span>mdmy</div>
<div class="acts"><span class="btn f">{ic("plus", 16, 2.2)}Замовлення</span><span class="btn l">{ic("package-plus", 16)}Товар</span></div>
<nav class="nav">{groups}</nav>
<div class="promo"><b>5 нових лідів</b><p>Найстаріший чекає 18 хв — передзвоніть, поки клієнт теплий.</p><span class="btn">Обробити ліди</span></div>
</aside>"""


def top(title, sub, extra=""):
    return f"""<div class="top"><div><h1>{title}</h1><div class="sub">{sub}</div></div><div class="r">{extra}
<span class="ws2">{ic("store", 15)}Інтернет-магазин{ic("chevron-down", 14)}</span><span class="ib">{ic("search", 17)}</span><span class="ib">{ic("bell", 17)}<span class="dot"></span></span><span class="me2">ОЛ</span></div></div>"""


def orders():
    rows = ""
    for n, (oid, name, ph, prod, more, s, st, dl, src, mgr, tm) in enumerate(ORDERS[:10]):
        rows += f"""<tr class="{"sel" if n == 0 else ""}"><td><span class="cb {"on" if n == 0 else ""}">{ic("check", 12, 3) if n == 0 else ""}</span></td><td class="num">{oid}</td>
<td><b style="font-weight:700">{name}</b><div class="m" style="font-size:12px">{ph}</div></td>
<td>{prod}{f'<span class="ups">+{more}</span>' if more else ''}</td><td>{pill(st)}</td><td class="m">{dl}</td>
<td><span class="src" style="--c:{SRC[src]}"><i></i>{src}</span></td><td class="m">{mgr}</td><td class="m">{tm}</td><td class="sum">{s} ₴</td></tr>"""
    seg = "".join(f'<span class="{"on" if i == 0 else ""}">{t}<em>{c}</em></span>' for i, (t, c) in enumerate(TABS))
    kpis = f"""<div class="kpis">
<div class="card kpi hero"><div class="lab">{ic("receipt-text", 16)}Сьогодні</div><b>18 замовлень</b><small>24 870 ₴ · середній чек 1 382 ₴</small></div>
<div class="card kpi"><div class="lab">{ic("circle-check-big", 16)}Апрув</div><b>68%</b><small><span class="up">↑ 4,2%</span> до минулого тижня</small></div>
<div class="card kpi"><div class="lab">{ic("package", 16)}Викуп</div><b>81%</b><small><span class="dn">↓ 1,1%</span> 9 відмов за тиждень</small></div>
<div class="card kpi"><div class="lab">{ic("truck", 16)}Чекають ТТН</div><b>9</b><small>з них 3 — понад добу</small></div></div>"""
    table = f"""<div class="card" style="flex:1;min-height:0;overflow:hidden"><div class="ch"><div class="seg">{seg}</div>
<div class="r"><span class="chip">{ic("funnel", 15)}Фільтри</span><span class="chip">{ic("calendar", 15)}Жовтень</span><span class="chip">{ic("columns-3" if False else "layout-grid", 15)}Колонки</span></div></div>
<table><thead><tr><th></th><th>№</th><th>Покупець</th><th>Товар</th><th>Статус</th><th>Доставка</th><th>Джерело</th><th>Менеджер</th><th>Час</th><th style="text-align:right">Сума</th></tr></thead>
<tbody>{rows}</tbody></table></div>"""
    return f'<div class="v1">{side("orders")}<main class="main">{top("Замовлення", "Четвер, 29 жовтня · 31 замовлення чекає відправки", "<span class=\'btn\'>" + ic("printer", 16) + "Реєстр</span>")}{kpis}{table}</main></div>'


def card():
    o = ORDER
    goods = ""
    for nm, var, sku, q, p, s, up in o["items"]:
        goods += f"""<div class="row {"sub2" if up else ""}"><span class="ph {"w" if up else ""}">{ic("zap" if not up else "link", 18)}</span>
<span class="nm"><b>{nm}</b><small>{var}</small></span><span class="q">− {q} +</span><span class="p">{s} ₴</span></div>"""
    stats = "".join(f"<div><span>{a}</span><b>{b}</b></div>" for a, b in CUSTOMER)
    tl = "".join(f'<div class="e"><span class="ic">{ic(i, 15)}</span><span><b>{t}</b><small>{d}</small></span><time>{tm}</time></div>' for tm, t, d, i in TIMELINE)
    hdr = f"""<div class="top"><div><div class="hdr2"><h1>Замовлення №1482</h1>{pill("ok")}<span class="chip">{ic("chevron-down", 15)}</span></div>
<div class="sub">29.10.2026, 14:32 · Лендинг «Павербанк 20000» · Instagram / stories</div></div><div class="r">
<span class="btn">{ic("printer", 16)}Друк{ic("chevron-down", 14)}</span><span class="btn">{ic("receipt", 16)}Фіскалізувати</span>
<span class="btn f">{ic("truck", 16)}Створити ТТН</span></div></div>"""
    grid = f"""<div class="og">
<div class="card"><div class="ch"><h3>Покупець</h3><div class="r"><span class="ib" style="width:32px;height:32px">{ic("phone", 15)}</span><span class="ib" style="width:32px;height:32px">{ic("message-circle", 15)}</span></div></div>
<div class="cust"><span class="av">ШТ</span><span><b>{o["name"]}</b><small>{o["phone"]} · {o["email"]}</small></span></div>
<div class="stats">{stats}</div>
<div class="prev"><div><span class="m">№1391</span><b>Навушники TWS Pro</b>{pill("got")}</div><div><span class="m">№1207</span><b>Павербанк 10000</b>{pill("ref")}</div></div></div>
<div class="card"><div class="ch"><h3>Деталі</h3></div><div class="kv">
<span>Менеджер</span><b>Олена Литвин</b><span>Джерело</span><b>Instagram → відділ «Інтернет-магазин»</b>
<span>Юрособа</span><b>ФОП Максимчук О. В. · каса Checkbox №1</b><span>Позначки</span><b><span class="tag">{ic("star", 12) if False else ""}VIP</span> <span class="tag">Подарунок</span></b>
<span>Коментар</span><b style="font-weight:600">Зателефонувати після 18:00</b></div></div>
<div class="card tot" style="grid-row:span 2"><div style="color:#B8CCC2;font-size:13px;font-weight:600">До сплати при отриманні</div>
<div class="big">1 797 <small>₴</small></div><div style="color:#B8CCC2;font-size:12.5px;margin-bottom:12px">Тисяча сімсот дев'яносто сім гривень</div>
<div class="ln"><span>Товари (2)</span><b>1 797 ₴</b></div><div class="ln"><span>Знижка</span><b>0 ₴</b></div>
<div class="ln"><span>Передоплата · Monobank</span><b>200 ₴</b></div><div class="ln"><span>Оплата</span><b>Контроль оплати НП</b></div>
<div class="ln"><span>Чек Checkbox</span><b style="color:var(--lime)">Передоплата ✓</b></div>
<div style="margin-top:14px;color:#B8CCC2;font-size:12.5px;font-weight:600">Історія</div>
<div class="tl" style="margin-top:4px">{"".join(f'<div class="e" style="grid-template-columns:8px 1fr auto"><span style="width:8px;height:8px;border-radius:50%;background:var(--lime);margin-top:6px"></span><span><b style="color:#fff">{t}</b><small style="color:#8FA89B">{d}</small></span><time style="color:#8FA89B">{tm}</time></div>' for tm, t, d, i in TIMELINE[1:])}</div>
</div>
<div class="card goods" style="grid-column:span 1"><div class="ch"><h3>Товари</h3><div class="r"><span class="chip">{ic("plus", 14)}Товар</span><span class="chip">{ic("sparkles", 14)}Допродаж</span></div></div>{goods}
<div class="add"><span class="chip" style="background:#F7FCEB;border-color:#D9F0B0;color:var(--forest)">{ic("sparkles", 14)}Пропозиція: Чохол для павербанка · 249 ₴</span></div></div>
<div class="card"><div class="ch"><h3>Доставка</h3><div class="r"><span class="chip">{ic("truck", 14)}Нова Пошта</span></div></div>
<div class="kv"><span>Місто</span><b>Київ</b><span>Відділення</span><b>№12 · вул. Межигірська, 1</b><span>Платник</span><b>Отримувач</b></div>
<div class="ttn">{ic("scan-barcode", 18)}<b>20450913998365</b><span class="r">{ic("copy", 16)}{ic("refresh-cw", 16)}{ic("printer", 16)}</span></div>
<div class="track"><i class="on"></i><i class="on"></i><i class="cur"></i><i></i><i></i></div>
<div style="display:flex;justify-content:space-between;font-size:12px;color:var(--mut)"><span>Створено</span><b style="color:var(--ink)">Прямує до відділення</b><span>Отримано</span></div>
<div class="kv" style="margin-top:14px"><span>Очікується</span><b>30 жовтня, після 13:00</b><span>Вартість</span><b>85 ₴ · платить отримувач</b><span>Ключ НП</span><b>ФОП Максимчук · Тульчин</b></div></div>
</div>"""
    return f'<div class="v1">{side("orders")}<main class="main">{hdr}{grid}</main></div>'


def settings():
    sl = "".join(f'<div class="it {"on" if n == "Статуси" else ""}">{ic(i, 17)}{n}</div>' for n, i in SETTINGS)

    def rows(sec):
        out = ""
        for code, s, stock, chk, sms in STATUS_ROWS:
            if s != sec:
                continue
            t = lambda v: f'<span class="tag n">—</span>' if v == "—" else f'<span class="tag">{v}</span>'
            out += f'<div class="srow">{ic("grip-vertical", 16, cls="g")}{pill(code)}{t(stock)}{t(chk)}{t(sms)}<span class="tog {"off" if code == "dup" else ""}"></span></div>'
        return out
    head = '<div class="shead"><span></span><span>Статус</span><span>Склад</span><span>Чек Checkbox</span><span>SMS / Viber</span><span>Активний</span></div>'
    body = f"""<div class="setw"><div class="card sl">{sl}</div><div class="card" style="overflow:hidden">
<div class="ch"><h3>Статуси й автоматизації</h3><div class="r"><span class="chip">{ic("eye", 14)}Як бачить менеджер</span><span class="btn f" style="height:32px">{ic("plus", 15)}Статус</span></div></div>
<div class="sgrp"><h4>{ic("inbox", 16)}Ліди <em>· робота з заявкою до підтвердження</em></h4>{head}{rows("Ліди")}</div>
<div class="sgrp"><h4>{ic("receipt-text", 16)}Замовлення <em>· від підтвердження до отримання</em></h4>{head}{rows("Замовлення")}</div></div></div>"""
    return f'<div class="v1">{side("settings")}<main class="main">{top("Налаштування", "Статуси визначають, що CRM робить сама: резерв, чек, SMS", "<span class=\'btn\'>" + ic("undo-2", 16) + "Скасувати</span><span class=\'btn l\'>" + ic("check", 16, 2.2) + "Зберегти</span>")}{body}</main></div>'


def attributes():
    groups = "".join(f'<div class="ag {"on" if n == 0 else ""}"><span class="ic">{ic(i, 18)}</span><span><b>{g}</b><small>{len(v)} значення · {u}</small></span>{ic("chevron-right", 16)}</div>'
                     for n, (g, i, t, v, u) in enumerate(ATTR_GROUPS))
    vals = "".join(f'<span class="val" style="--c:{c}"><span class="sw"></span>{n}{ic("grip-vertical", 14)}</span>' for n, c in ATTR_GROUPS[0][3])
    rows = ""
    for col, c, cap, sku, pr, stock, res in VARIANTS:
        cls = "z" if stock == 0 else ("lo" if stock < 5 else "")
        rows += f"""<tr><td><span class="sw2" style="--c:{c}"></span>{col}</td><td>{cap} мА·год</td><td class="mono">{sku}</td>
<td><span class="inp">{pr} ₴</span></td><td><b>{stock}</b><span class="bar"><i class="{cls}" style="width:{min(100, stock * 4)}%"></i></span></td><td class="m">{res}</td><td><span class="tog {"off" if stock == 0 else ""}"></span></td></tr>"""
    body = f"""<div class="tabs2"><span>Товари</span><span>Категорії</span><span>Бренди</span><span class="on">Атрибути</span></div>
<div class="aw"><div class="card"><div class="ch"><h3>Групи атрибутів</h3><div class="r"><span class="chip">{ic("plus", 14)}</span></div></div>{groups}</div>
<div style="display:flex;flex-direction:column;gap:14px;min-height:0">
<div class="card"><div class="ch"><h3>Колір</h3><span class="chip">{ic("palette", 14)}Тип: кольорові плашки</span><div class="r"><span class="chip">{ic("pencil", 14)}Перейменувати</span></div></div>
<div class="vals">{vals}<span class="val add">{ic("plus", 15)}Значення</span></div></div>
<div class="card" style="flex:1;overflow:hidden"><div class="ch"><span class="ph" style="width:40px;height:40px;border-radius:12px;background:linear-gradient(145deg,#23262a,#3a3f45);display:grid;place-items:center;color:#9aa">{ic("zap", 18)}</span>
<div><h3>Варіанти: Павербанк Volt</h3><div class="sub" style="margin:0">Колір × Ємність · 6 варіантів · 63 шт на складі</div></div>
<div class="r"><span class="chip">{ic("layers", 14)}Згенерувати комбінації</span><span class="btn f" style="height:32px">{ic("check", 15)}Зберегти</span></div></div>
<table class="vm"><thead><tr><th>Колір</th><th>Ємність</th><th>Артикул</th><th>Ціна</th><th>Залишок</th><th>Резерв</th><th>Продаж</th></tr></thead><tbody>{rows}</tbody></table></div></div></div>"""
    return f'<div class="v1">{side("products")}<main class="main">{top("Атрибути", "Колір, ємність, розмір — з них збираються варіанти товару з власним залишком")}{body}</main></div>'


def build():
    return page("Варіант 1 — Бенто-лайм", CSS + mobile.CSS1, [
        ("1-menu", "Бокова панель і список замовлень", orders(), None, None), ("2-card", "Картка замовлення", card(), None, None),
        ("3-settings", "Налаштування → Статуси", settings(), None, None), ("4-attrs", "Товари → Атрибути", attributes(), None, None),
        ("5-mobile", "Телефон: меню, список, картка, вибір варіанта", mobile.m1(), None, None)])
