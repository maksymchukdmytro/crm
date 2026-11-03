"""Варіант 7 — «Кобальт» (Taskly): синій + лайм, відділ-перемикач, джерела з кольоровими крапками, мобільна версія з кнопкою «+»."""
from common import *

CSS = """
.v7{--ink:#12142B;--mut:#6B6F86;--line:#E7E8F0;--b:#2D3FE7;--b2:#EEF0FE;--lime:#C8F560;--bg:#F5F6FA;font:400 14px/1.45 'Rubik',sans-serif;color:var(--ink);background:var(--bg);width:100%;height:100%;display:flex}
.v7 .side{width:250px;background:#fff;border-right:1px solid var(--line);padding:16px 14px;display:flex;flex-direction:column;gap:10px}
.v7 .brand{display:flex;align-items:center;gap:9px;font-weight:600;font-size:18px}.v7 .brand .lg{width:32px;height:32px;border-radius:9px;background:var(--b);color:#fff;display:grid;place-items:center}
.v7 .brand .i:last-child{margin-left:auto;color:var(--mut)}
.v7 .ws{display:flex;align-items:center;gap:10px;padding:8px 10px;border:1px solid var(--line);border-radius:12px}
.v7 .ws .a{width:30px;height:30px;border-radius:9px;background:var(--lime);display:grid;place-items:center;font-weight:600;color:var(--ink)}
.v7 .ws small{display:block;font-size:11px;color:var(--mut);line-height:1.1}.v7 .ws b{font-weight:500;font-size:13.5px}.v7 .ws .i:last-child{margin-left:auto;color:var(--mut)}
.v7 .srch{display:flex;align-items:center;gap:8px;height:36px;padding:0 10px;border-radius:10px;background:var(--bg);color:#9A9DB2;font-size:13px}
.v7 .srch kbd{margin-left:auto;font:500 11px 'Rubik';background:#fff;border:1px solid var(--line);border-radius:6px;padding:0 5px;color:var(--mut)}
.v7 .lab{font-size:11.5px;color:#9A9DB2;font-weight:500;padding:4px 8px 0;display:flex;align-items:center}.v7 .lab .i{margin-left:auto}
.v7 .it{display:flex;align-items:center;gap:10px;height:34px;padding:0 10px;border-radius:9px;color:#3D4060;font-size:13.5px}
.v7 .it .i{color:#8A8DA6}.v7 .it.on{background:var(--b2);color:var(--b);font-weight:500}.v7 .it.on .i{color:var(--b)}
.v7 .it em{margin-left:auto;font-style:normal;font-size:11.5px;color:#9A9DB2}.v7 .it em.b{background:var(--b);color:#fff;border-radius:99px;padding:0 7px;font-weight:500}
.v7 .it i.d{width:9px;height:9px;border-radius:3px;background:var(--c)}
.v7 .promo{margin-top:auto;background:var(--ink);color:#fff;border-radius:16px;padding:14px}
.v7 .promo .ic{width:30px;height:30px;border-radius:9px;background:var(--lime);display:grid;place-items:center;color:var(--ink);margin-bottom:10px}
.v7 .promo b{font-weight:500;display:block}.v7 .promo p{font-size:12px;color:#A3A6C0;margin:4px 0 10px}
.v7 .promo span.bt{display:flex;justify-content:center;align-items:center;height:32px;border-radius:9px;background:var(--lime);color:var(--ink);font-weight:500;font-size:13px}
.v7 .me{display:flex;align-items:center;gap:9px;padding:4px}.v7 .me .av{width:32px;height:32px;border-radius:50%;background:#FFD7B8;display:grid;place-items:center;font-size:12px;font-weight:600}
.v7 .me small{display:block;font-size:11.5px;color:var(--mut);line-height:1.1}
.v7 .main{flex:1;min-width:0;padding:16px 22px;display:flex;flex-direction:column;gap:14px}
.v7 .crumb{font-size:12px;color:#9A9DB2}
.v7 .hd{display:flex;align-items:center;gap:10px}.v7 h1{font-size:26px;font-weight:600;letter-spacing:-.02em}.v7 .hd .subt{color:var(--mut);font-size:13px}
.v7 .hd .r{margin-left:auto;display:flex;gap:8px;align-items:center}
.v7 .btn{display:inline-flex;align-items:center;gap:7px;height:38px;padding:0 15px;border-radius:11px;border:1px solid var(--line);background:#fff;font-weight:500;font-size:13.5px;white-space:nowrap}
.v7 .btn.b{background:var(--b);border-color:var(--b);color:#fff;box-shadow:0 8px 16px -10px rgba(45,63,231,.8)}.v7 .btn.l{background:var(--lime);border-color:var(--lime)}
.v7 .faces{display:flex}.v7 .faces span{width:30px;height:30px;border-radius:50%;border:2px solid var(--bg);margin-left:-8px;display:grid;place-items:center;font-size:10.5px;font-weight:600}
.v7 .card{background:#fff;border:1px solid var(--line);border-radius:18px;padding:16px}
.v7 .card h3{font-size:15px;font-weight:600;display:flex;align-items:center;gap:8px}.v7 .card h3 .r{margin-left:auto;display:flex;gap:6px;align-items:center;font-weight:400}
.v7 .k4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.v7 .kp .t{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--mut)}.v7 .kp .t .ic{width:28px;height:28px;border-radius:8px;display:grid;place-items:center;background:var(--c2);color:var(--c)}
.v7 .kp .t .i:last-child{margin-left:auto}
.v7 .kp b{display:block;font-size:34px;font-weight:600;letter-spacing:-.03em;margin:10px 0 0;line-height:1}.v7 .kp small{font-size:12px;color:var(--mut)}
.v7 .kp.hero{background:var(--b);border-color:var(--b);color:#fff}.v7 .kp.hero .t{color:#C9CEFF}.v7 .kp.hero .t .ic{background:var(--lime);color:var(--ink)}
.v7 .kp.hero small{color:#C9CEFF}.v7 .pbar{height:8px;border-radius:99px;background:rgba(255,255,255,.2);margin-top:10px}.v7 .pbar i{display:block;height:100%;border-radius:99px;background:var(--lime)}
.v7 .up{color:#16A34A}.v7 .dn{color:#E5484D}
.v7 .seg{display:inline-flex;gap:2px;background:var(--bg);border-radius:10px;padding:3px}.v7 .seg span{display:inline-flex;align-items:center;gap:5px;padding:5px 10px;border-radius:8px;font-size:12.5px;color:var(--mut)}
.v7 .seg span.on{background:#fff;color:var(--ink);box-shadow:0 1px 2px rgba(0,0,0,.08)}
.v7 .task{display:flex;align-items:center;gap:12px;padding:10px 4px;border-bottom:1px solid #F1F2F7;font-size:13.5px}
.v7 .task .ck{width:20px;height:20px;border-radius:50%;border:1.5px solid #C7C9D9;flex:none;display:grid;place-items:center}
.v7 .task .ck.on{background:var(--b);border-color:var(--b);color:#fff}.v7 .task.done b{color:#A3A6C0;text-decoration:line-through;font-weight:400}
.v7 .task b{font-weight:500}.v7 .task .m{margin-left:auto;display:flex;align-items:center;gap:10px;font-size:12px;color:var(--mut);white-space:nowrap}
.v7 .tg{display:inline-flex;align-items:center;gap:5px;font-size:12px;padding:2px 8px;border-radius:7px;background:var(--bg);color:#3D4060}
.v7 .tg i{width:7px;height:7px;border-radius:2px;background:var(--c)}
.v7 .flag{display:inline-flex;align-items:center;gap:3px}
.v7 .av2{width:24px;height:24px;border-radius:50%;display:grid;place-items:center;font-size:10px;font-weight:600;background:#E4E6FB;color:var(--b)}
.v7 .chart{display:flex;align-items:flex-end;gap:12px;height:150px;margin-top:12px}
.v7 .chart div{flex:1;display:flex;flex-direction:column;justify-content:flex-end;gap:3px;align-items:center;height:100%}
.v7 .chart i{width:100%;border-radius:8px;background:var(--b)}.v7 .chart i.g{background:#E4E6FB}.v7 .chart i.l{background:var(--lime)}
.v7 .chart span{font-size:11.5px;color:var(--mut)}
.v7 .src{display:flex;flex-direction:column;gap:12px;margin-top:10px}.v7 .src div{font-size:13px}.v7 .src .ln{display:flex;justify-content:space-between;margin-bottom:5px}
.v7 .src .pb{height:6px;border-radius:99px;background:#EEF0F6}.v7 .src .pb i{display:block;height:100%;border-radius:99px;background:var(--c)}
.v7 .st{display:inline-flex;align-items:center;gap:5px;height:22px;padding:0 8px;border-radius:7px;font-size:12px;font-weight:500;background:color-mix(in srgb,var(--c) 13%,#fff);color:color-mix(in srgb,var(--c) 75%,#000)}
.v7 .st i{width:6px;height:6px;border-radius:50%;background:var(--c)}
/* список + панель */
.v7 .lw{display:grid;grid-template-columns:1fr 400px;gap:14px;flex:1;min-height:0}
.v7 .grp{display:flex;align-items:center;gap:8px;padding:10px 4px 4px;font-size:13px;font-weight:500}.v7 .grp em{font-style:normal;color:var(--mut);background:var(--bg);border-radius:6px;padding:0 6px;font-size:12px}
.v7 .grp .i:last-child{margin-left:auto;color:var(--mut)}
.v7 .task.sel{background:var(--b2);border-radius:10px;border-color:transparent;padding:10px 8px}
.v7 .pnl{display:flex;flex-direction:column;gap:12px;overflow:hidden}
.v7 .pnl .tp{display:flex;align-items:center;gap:8px;color:var(--mut)}.v7 .pnl .tp .r{margin-left:auto;display:flex;gap:10px}
.v7 .pnl h2{font-size:22px;font-weight:600;letter-spacing:-.02em;line-height:1.2}
.v7 .prow{display:grid;grid-template-columns:110px 1fr;gap:10px;font-size:13.5px;align-items:center}.v7 .prow span.k{display:flex;align-items:center;gap:8px;color:var(--mut)}
.v7 .sub{border:1px solid var(--line);border-radius:14px;padding:12px}
.v7 .sub .h{display:flex;font-size:13px;font-weight:500;margin-bottom:8px}.v7 .sub .h span{margin-left:auto;color:var(--mut);font-weight:400}
.v7 .sub .pb{height:5px;border-radius:99px;background:#EEF0F6;margin-bottom:8px}.v7 .sub .pb i{display:block;height:100%;width:40%;background:var(--b);border-radius:99px}
.v7 .sub .s{display:flex;align-items:center;gap:8px;font-size:13px;padding:4px 0}.v7 .sub .s .ck{width:17px;height:17px;border-radius:5px;border:1.5px solid #C7C9D9;display:grid;place-items:center}
.v7 .sub .s .ck.on{background:var(--b);border-color:var(--b);color:#fff}.v7 .sub .s.done span{color:#A3A6C0;text-decoration:line-through}
.v7 .pfoot{margin-top:auto;display:flex;gap:8px}.v7 .pfoot .btn.l{flex:1;justify-content:center}
.v7 .sq{width:38px;height:38px;border-radius:11px;display:grid;place-items:center;border:1px solid var(--line);background:#fff}.v7 .sq.r{background:#FFECEC;border-color:#FFD5D5;color:#E5484D}
/* налаштування */
.v7 .sgrid{display:grid;grid-template-columns:220px 1fr 320px;gap:14px;flex:1;min-height:0}
.v7 .snav .it{height:36px}
.v7 .srow{display:grid;grid-template-columns:20px 190px 1fr 1fr 1fr;gap:10px;align-items:center;padding:8px 6px;border-bottom:1px solid #F1F2F7;font-size:13px}
.v7 .srow>*{justify-self:start}.v7 .srow .i.g{color:#C7C9D9}
.v7 .tgl{display:inline-block;width:36px;height:20px;border-radius:99px;background:var(--b);position:relative;flex:none}.v7 .tgl:after{content:"";position:absolute;right:2px;top:2px;width:16px;height:16px;border-radius:50%;background:#fff}
.v7 .tgl.off{background:#D9DBE6}.v7 .tgl.off:after{right:auto;left:2px}
.v7 .nt{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #F1F2F7;font-size:13.5px}.v7 .nt .tgl{margin-left:auto}
.v7 .nt small{display:block;font-size:12px;color:var(--mut)}
.v7 .themes{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:10px}.v7 .themes div{height:54px;border-radius:10px;border:1px solid var(--line);position:relative;overflow:hidden}
.v7 .themes div.on{outline:2px solid var(--b);outline-offset:1px}.v7 .themes div:before{content:"";position:absolute;left:6px;top:6px;bottom:6px;width:18px;border-radius:4px;background:var(--x)}
.v7 .dots{display:flex;gap:8px;margin-top:10px}.v7 .dots i{width:22px;height:22px;border-radius:50%;background:var(--c)}.v7 .dots i.on{outline:2px solid var(--c);outline-offset:2px}
.v7 .danger{border:1px solid #FFD5D5;background:#FFF6F6;border-radius:14px;padding:12px;display:flex;align-items:center;gap:10px;font-size:13px}
/* атрибути */
.v7 .ag{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.v7 .agc{background:#fff;border:1px solid var(--line);border-radius:18px;padding:14px;display:flex;flex-direction:column;gap:10px}
.v7 .agc.on{border-color:var(--b);box-shadow:0 0 0 3px var(--b2)}
.v7 .agc .t{display:flex;align-items:center;gap:10px}.v7 .agc .t .ic{width:34px;height:34px;border-radius:10px;background:var(--c2);color:var(--c);display:grid;place-items:center}
.v7 .agc .t b{font-weight:600}.v7 .agc .t small{display:block;font-size:12px;color:var(--mut)}.v7 .agc .t .i:last-child{margin-left:auto;color:var(--mut)}
.v7 .agc .vals{display:flex;flex-wrap:wrap;gap:6px}.v7 .agc .ft{display:flex;align-items:center;justify-content:space-between;font-size:12px;color:var(--mut)}
.v7 .sw7{display:inline-block;width:12px;height:12px;border-radius:4px;background:var(--c);box-shadow:inset 0 0 0 1px rgba(0,0,0,.12);vertical-align:-1px;margin-right:4px}
.v7 table{width:100%;border-collapse:collapse}.v7 th{font-size:12px;font-weight:500;color:var(--mut);text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}
.v7 td{padding:9px 10px;border-bottom:1px solid #F1F2F7;font-size:13.5px}.v7 .mono{font:500 12.5px 'JB',monospace}
.v7 .lvl{display:inline-flex;align-items:center;gap:6px}.v7 .lvl i{width:60px;height:6px;border-radius:99px;background:#EEF0F6;overflow:hidden;display:inline-block}
.v7 .lvl i b{display:block;height:100%;background:var(--c);border-radius:99px}
/* мобільний */
.v7m{background:linear-gradient(160deg,#4558F0 0%,#2D3FE7 45%,#8EA0FF 100%);width:100%;height:100%;display:flex;align-items:center;justify-content:center;gap:34px;font:400 14px/1.4 'Rubik',sans-serif;color:#12142B}
.v7m .ph{width:330px;height:700px;border-radius:46px;background:#0E0F1F;padding:10px;box-shadow:0 40px 60px -30px rgba(10,15,80,.7)}
.v7m .scr{width:100%;height:100%;border-radius:38px;background:#F5F6FA;overflow:hidden;position:relative;display:flex;flex-direction:column}
.v7m .sb{height:44px;display:flex;align-items:center;justify-content:space-between;padding:0 26px;font-size:13px;font-weight:600}
.v7m .isl{width:96px;height:28px;border-radius:99px;background:#0E0F1F;position:absolute;left:50%;top:9px;transform:translateX(-50%)}
.v7m .bd{flex:1;padding:6px 16px 0;display:flex;flex-direction:column;gap:10px;overflow:hidden}
.v7m h2{font-size:22px;font-weight:600;letter-spacing:-.02em}.v7m .mut{color:#6B6F86;font-size:12.5px}
.v7m .c{background:#fff;border-radius:16px;padding:12px;border:1px solid #E7E8F0}
.v7m .hero{background:#2D3FE7;color:#fff;border:0}.v7m .hero b{font-size:36px;font-weight:600;letter-spacing:-.03em}
.v7m .pb{height:7px;border-radius:99px;background:rgba(255,255,255,.25);margin-top:8px}.v7m .pb i{display:block;height:100%;width:72%;border-radius:99px;background:#C8F560}
.v7m .k3{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.v7m .k3 .c b{display:block;font-size:22px;font-weight:600}.v7m .k3 .c small{font-size:11px;color:#6B6F86}
.v7m .row{display:flex;align-items:center;gap:10px;background:#fff;border-radius:14px;padding:10px 12px;border:1px solid #E7E8F0;font-size:13px}
.v7m .row b{font-weight:500;display:block}.v7m .row small{font-size:11.5px;color:#6B6F86}.v7m .row .s{margin-left:auto;font-weight:600;white-space:nowrap}
.v7m .ck{width:20px;height:20px;border-radius:50%;border:1.5px solid #C7C9D9;flex:none}
.v7m .tab{height:76px;background:#fff;border-top:1px solid #E7E8F0;display:flex;align-items:center;justify-content:space-around;padding:0 8px 10px;font-size:10.5px;color:#9A9DB2}
.v7m .tab span{display:flex;flex-direction:column;align-items:center;gap:3px}.v7m .tab span.on{color:#2D3FE7}
.v7m .fab{width:52px;height:52px;border-radius:50%;background:#2D3FE7;color:#fff;display:grid;place-items:center;margin-top:-26px;box-shadow:0 10px 20px -8px rgba(45,63,231,.9)}
.v7m .st{align-self:flex-start;display:inline-flex;align-items:center;gap:5px;height:21px;padding:0 7px;border-radius:7px;font-size:11.5px;font-weight:500;background:color-mix(in srgb,var(--c) 13%,#fff);color:color-mix(in srgb,var(--c) 75%,#000)}
.v7m .st i{width:6px;height:6px;border-radius:50%;background:var(--c)}
.v7m .chips{display:flex;gap:6px}.v7m .chips span{padding:5px 10px;border-radius:99px;font-size:12px;background:#fff;border:1px solid #E7E8F0;white-space:nowrap}
.v7m .chips span.on{background:#12142B;color:#fff;border-color:#12142B}
.v7m .kv{display:grid;grid-template-columns:92px 1fr;gap:7px;font-size:12.5px}.v7m .kv span{color:#6B6F86}
.v7m .acts{display:flex;gap:8px;padding:10px 16px 18px;background:#fff;border-top:1px solid #E7E8F0}
.v7m .acts span{height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;gap:6px;font-weight:500;font-size:13px;border:1px solid #E7E8F0;flex:1}
.v7m .acts span.l{background:#C8F560;border-color:#C8F560;flex:2}
"""

SRCS = [("Instagram", "#E1306C", 96), ("Лендинги", "#2D3FE7", 71), ("Rozetka", "#16A34A", 44), ("TikTok", "#12142B", 21), ("Prom", "#8B5CF6", 16)]


def side(on):
    it = ""
    for k, n, i, c in FLAT_NAV[:8]:
        cnt = {"leads": '<em class="b">5</em>', "orders": "<em>248</em>"}.get(k, "")
        it += f'<div class="it {"on" if k == on else ""}">{ic(i, 17)}{n}{cnt}</div>'
    rest = "".join(f'<div class="it {"on" if k == on else ""}">{ic(i, 17)}{n}</div>' for k, n, i, c in FLAT_NAV[8:] if k in ("payments", "stats", "settings"))
    src = "".join(f'<div class="it" style="--c:{c}"><i class="d"></i>{n}<em>{v}</em></div>' for n, c, v in SRCS[:4])
    return f"""<aside class="side"><div class="brand"><span class="lg">{ic("check", 18, 2.6)}</span>mdmy{ic("panel-left", 17)}</div>
<div class="ws"><span class="a">ІМ</span><span><small>Відділ</small><b>Інтернет-магазин</b></span>{ic("chevron-down", 15)}</div>
<div class="srch">{ic("search", 15)}Пошук<kbd>Ctrl K</kbd></div><div class="lab">Головне меню</div>{it}{rest}
<div class="lab">Джерела{ic("plus", 13)}</div>{src}
<div class="promo"><span class="ic">{ic("inbox", 16)}</span><b>5 нових лідів</b><p>Найстаріший чекає 18 хв</p><span class="bt">Обробити</span></div>
<div class="me"><span class="av">ОЛ</span><span>Олена Литвин<small>Менеджер</small></span></div></aside>"""


def home():
    tasks = [("Передзвонити Ковальченко Ірині", "Новий лід · Лендинг", "#2D3FE7", "14:18", "high", False),
             ("Підтвердити №1484 Дорошенко", "TikTok · Павербанк 20000", "#12142B", "щойно", "high", False),
             ("Створити 9 ТТН до 17:00", "Підтверджено · Нова Пошта", "#F97316", "17:00", "med", False),
             ("Нагадати Мельнику про посилку", "Прибуло у відділення · 3 дні", "#E1306C", "16:00", "low", False),
             ("Закрити зміну Checkbox", "ФОП Максимчук · каса №1", "#16A34A", "23:00", "low", True)]
    fl = {"high": ("#E5484D", "Терміново"), "med": ("#F59E0B", "Сьогодні"), "low": ("#9A9DB2", "Можна пізніше")}
    tl = "".join(f"""<div class="task {"done" if d else ""}"><span class="ck {"on" if d else ""}">{ic("check", 12, 3) if d else ""}</span><b>{t}</b><span class="m"><span class="tg" style="--c:{c}"><i></i>{s}</span>
<span>{ic("clock", 13)} {tm}</span><span class="flag" style="color:{fl[p][0]}">{ic("tag", 13)}{fl[p][1]}</span><span class="av2">ОЛ</span>{ic("ellipsis", 15)}</span></div>""" for t, s, c, tm, p, d in tasks)
    week = [(14, 4, 0), (17, 3, 0), (12, 2, 6), (19, 4, 0), (16, 2, 0), (6, 2, 0), (3, 1, 0)]
    ch = "".join(f'<div><i class="g" style="height:{g * 4}%"></i><i class="{"l" if l else ""}" style="height:{(b + l) * 4}%"></i><span>{d}</span></div>' for (b, g, l), d in zip(week, "Пн Вт Ср Чт Пт Сб Нд".split()))
    src = "".join(f'<div><div class="ln"><span>{n}</span><b style="font-weight:500">{v} · {round(v / 248 * 100)}%</b></div><div class="pb"><i style="--c:{c};width:{v / 96 * 100}%"></i></div></div>' for n, c, v in SRCS)
    body = f"""<div class="crumb">Інтернет-магазин › Головна</div><div class="hd"><div><h1>Добрий день, Олено</h1><div class="subt">Четвер, 29 жовтня · 6 справ на сьогодні і 14 посилок до відправки</div></div>
<div class="r"><span class="faces"><span style="background:#FFD7B8">ОЛ</span><span style="background:#D7E3FF">АН</span><span style="background:#E4F7C4">МК</span></span><span class="btn">{ic("package-plus", 16)}Товар</span><span class="btn b">{ic("plus", 16)}Замовлення</span></div></div>
<div class="k4"><div class="card kp" style="--c:#2D3FE7;--c2:#EEF0FE"><div class="t"><span class="ic">{ic("receipt-text", 15)}</span>Сьогодні{ic("ellipsis", 15)}</div><b>18</b><small><span class="up">↑ 3</span> до вчора · 24 870 ₴</small></div>
<div class="card kp" style="--c:#16A34A;--c2:#E7F8EE"><div class="t"><span class="ic">{ic("circle-check-big", 15)}</span>Апрув тижня{ic("ellipsis", 15)}</div><b>68%</b><small><span class="up">↑ 4,2%</span> до минулого</small></div>
<div class="card kp" style="--c:#F59E0B;--c2:#FFF4DE"><div class="t"><span class="ic">{ic("truck", 15)}</span>Чекають ТТН{ic("ellipsis", 15)}</div><b>9</b><small>3 — понад добу</small></div>
<div class="card kp hero"><div class="t"><span class="ic">{ic("zap", 15)}</span>План на жовтень<span style="margin-left:auto;font-weight:500;color:#fff">312 / 360 тис</span></div><b>86%</b><div class="pbar"><i style="width:86%"></i></div><small>48 тис ₴ до плану · 2 дні</small></div></div>
<div style="display:grid;grid-template-columns:1fr 330px;gap:14px;flex:1;min-height:0"><div class="card" style="overflow:hidden"><h3>Справи на сьогодні<span style="font-size:12px;background:var(--bg);border-radius:6px;padding:0 6px;color:var(--mut)">5</span>
<span class="r"><span class="seg"><span class="on">{ic("list", 13)}Список</span><span>{ic("square-kanban", 13)}Дошка</span><span>{ic("calendar", 13)}Календар</span></span><span class="btn" style="height:32px">{ic("funnel", 14)}Фільтр</span></span></h3>
<div style="margin-top:6px">{tl}</div><div class="task" style="color:#9A9DB2;border:1px dashed var(--line);border-radius:10px;margin-top:8px;padding:10px">{ic("plus", 15)}Додати справу — наприклад «передзвонити №1462 о 18:00»</div></div>
<div style="display:flex;flex-direction:column;gap:14px"><div class="card"><h3>Замовлення за тиждень<span class="r"><span class="st" style="--c:#16A34A"><i></i>+16%</span></span></h3><div class="chart">{ch}</div></div>
<div class="card" style="flex:1"><h3>Джерела<span class="r">{ic("arrow-up-right", 15)}</span></h3><div class="src">{src}</div></div></div></div>"""
    return f'<div class="v7">{side("home")}<main class="main">{body}</main></div>'


def orders():
    groups = [("ok", [ORDERS[0], ORDERS[10]]), ("pack", [ORDERS[3]]), ("sent", [ORDERS[2], ORDERS[8]]), ("arr", [ORDERS[6]])]
    src_c = {"Instagram": "#E1306C", "Лендинг": "#2D3FE7", "Rozetka": "#16A34A", "Facebook": "#1877F2", "Prom": "#8B5CF6", "TikTok": "#12142B"}
    rows = ""
    for code, os_ in groups:
        n, c = ST[code]
        rows += f'<div class="grp">{ic("chevron-down", 14)}<span class="st" style="--c:{c}"><i></i>{n}</span><em>{len(os_)}</em>{ic("plus", 15)}</div>'
        for o in os_:
            sel = o[0] == 1482
            rows += f"""<div class="task {"sel" if sel else ""}"><span class="ck">{""}</span><span><b>{o[1]}</b><div style="font-size:12px;color:var(--mut)">№{o[0]} · {o[3]}</div></span>
<span class="m"><span class="tg" style="--c:{src_c[o[8]]}"><i></i>{o[8]}</span><span>{ic("truck", 13)} {o[7]}</span><b style="color:var(--ink);font-weight:600;width:64px;text-align:right">{o[5]} ₴</b><span class="av2">{"ОЛ" if o[9] == "Олена" else "АН"}</span></span></div>"""
    o = ORDER
    props = [("circle-dot", "Статус", pill("ok")), ("user", "Менеджер", '<span style="display:inline-flex;gap:6px;align-items:center"><span class="av2">ОЛ</span>Олена Литвин</span>'),
             ("phone", "Телефон", o["phone"]), ("truck", "Доставка", "НП · Київ, №12"), ("wallet", "Оплата", "Контроль оплати · 1 597 ₴"), ("landmark", "Юрособа", "ФОП Максимчук О. В.")]
    pr = "".join(f'<span class="k">{ic(i, 15)}{k}</span><span>{v}</span>' for i, k, v in props)
    steps = [("Зарезервувати товар", True), ("Пробити чек передоплати", True), ("Створити ТТН", False), ("Надіслати SMS з ТТН", False), ("Додати в реєстр НП", False)]
    sub = "".join(f'<div class="s {"done" if d else ""}"><span class="ck {"on" if d else ""}">{ic("check", 11, 3) if d else ""}</span><span>{t}</span></div>' for t, d in steps)
    pnl = f"""<div class="card pnl"><div class="tp"><span class="st" style="--c:#2D3FE7"><i></i>№1482 · Instagram</span><span class="r">{ic("link", 16)}{ic("arrow-up-right", 16)}{ic("x", 16)}</span></div>
<h2>{o["name"]}</h2><div class="prow">{pr}</div><div style="font-size:12px;color:var(--mut);font-weight:500">Товари</div>
<div style="font-size:13.5px;display:flex;justify-content:space-between"><span>Павербанк 20000 мА·год · чорний</span><b style="font-weight:500">1 599 ₴</b></div>
<div style="font-size:13.5px;display:flex;justify-content:space-between;color:var(--mut)"><span>↳ Кабель USB-C 1 м (допродаж)</span><span>198 ₴</span></div>
<div class="sub"><div class="h">Що лишилось зробити<span>2 з 5</span></div><div class="pb"><i></i></div>{sub}</div>
<div class="pfoot"><span class="btn l">{ic("truck", 16)}Створити ТТН</span><span class="sq">{ic("printer", 16)}</span><span class="sq">{ic("pencil", 16)}</span><span class="sq r">{ic("ban" if False else "x", 16)}</span></div></div>"""
    body = f"""<div class="crumb">Інтернет-магазин › Замовлення</div><div class="hd"><div><h1>Замовлення</h1><div class="subt">248 за жовтень · 31 підтверджено · 57 у дорозі</div></div>
<div class="r"><span class="btn">{ic("printer", 16)}Реєстр</span><span class="btn b">{ic("plus", 16)}Замовлення</span></div></div>
<div style="display:flex;gap:8px;align-items:center"><span class="seg"><span class="on">{ic("list", 13)}Список</span><span>{ic("square-kanban", 13)}Дошка</span><span>{ic("calendar", 13)}Календар</span></span>
<span class="btn" style="height:32px;border-color:var(--b);color:var(--b);background:var(--b2)">Менеджер: я {ic("x", 13)}</span><span class="btn" style="height:32px">Джерело{ic("chevron-down", 13)}</span><span class="btn" style="height:32px">Доставка{ic("chevron-down", 13)}</span>
<span class="btn" style="height:32px">Дата{ic("chevron-down", 13)}</span><span class="srch" style="margin-left:auto;width:220px">{ic("search", 14)}Телефон або ТТН</span></div>
<div class="lw"><div class="card" style="overflow:hidden;padding-top:6px">{rows}</div>{pnl}</div>"""
    return f'<div class="v7">{side("orders")}<main class="main">{body}</main></div>'


def settings():
    sn = "".join(f'<div class="it {"on" if n == "Статуси" else ""}">{ic(i, 16)}{n}</div>' for n, i in SETTINGS)
    rows = ""
    for code, s, stock, chk, sms in STATUS_ROWS:
        t = lambda v, i: f'<span class="tg" style="color:#C7C9D9;background:none">—</span>' if v == "—" else f'<span class="tg">{ic(i, 12)}{v}</span>'
        rows += f'<div class="srow">{ic("grip-vertical", 14, cls="g")}{pill(code)}{t(stock, "boxes")}{t(chk, "receipt")}{t(sms, "message-square")}</div>'
    nts = [("Новий лід", "Звук і значок у меню", True), ("Лід чекає понад 15 хв", "Нагадування менеджеру", True), ("ТТН не створено до 17:00", "Telegram у чат складу", True),
           ("Чек не пробився", "Telegram власнику", True), ("Щоденний підсумок", "О 21:00, на пошту", False)]
    nt = "".join(f'<div class="nt"><span>{a}<small>{b}</small></span><span class="tgl {"" if on else "off"}"></span></div>' for a, b, on in nts)
    body = f"""<div class="crumb">Налаштування › Статуси</div><div class="hd"><div><h1>Налаштування</h1><div class="subt">Статуси, сповіщення й вигляд для відділу «Інтернет-магазин»</div></div>
<div class="r"><span class="btn">Скасувати</span><span class="btn b">{ic("check", 16)}Зберегти зміни</span></div></div>
<div class="sgrid"><div class="card snav" style="padding:10px">{sn}</div>
<div class="card" style="overflow:hidden"><h3>Статуси<span class="r"><span class="btn" style="height:32px">{ic("plus", 14)}Статус</span></span></h3>
<div class="srow" style="color:var(--mut);font-size:12px;border:0;padding-top:12px"><span></span><span>Назва</span><span>Склад</span><span>Чек Checkbox</span><span>SMS / Viber</span></div>{rows}</div>
<div style="display:flex;flex-direction:column;gap:14px"><div class="card"><h3>Сповіщення</h3>{nt}</div>
<div class="card"><h3>Вигляд</h3><div class="themes"><div class="on" style="--x:#2D3FE7;background:#fff"></div><div style="--x:#C8F560;background:#12142B"></div><div style="--x:#2D3FE7;background:linear-gradient(90deg,#fff 50%,#12142B 50%)"></div></div>
<div class="dots"><i class="on" style="--c:#2D3FE7"></i><i style="--c:#0B5D47"></i><i style="--c:#E5484D"></i><i style="--c:#F59E0B"></i><i style="--c:#12142B"></i></div></div></div></div>"""
    return f'<div class="v7">{side("settings")}<main class="main">{body}</main></div>'


def attributes():
    cols = [("#2D3FE7", "#EEF0FE"), ("#F59E0B", "#FFF4DE"), ("#16A34A", "#E7F8EE"), ("#8B5CF6", "#F1EBFE"), ("#E1306C", "#FDE8F0"), ("#12142B", "#ECEDF3")]
    cards = ""
    for n, (g, i, t, v, u) in enumerate(ATTR_GROUPS):
        c, c2 = cols[n]
        vals = "".join(f'<span class="tg">{f"<span class=sw7 style=--c:{x}></span>" if x else ""}{nm}</span>' for nm, x in v)
        cards += f"""<div class="agc {"on" if n == 0 else ""}"><div class="t"><span class="ic" style="--c:{c};--c2:{c2}">{ic(i, 17)}</span><span><b>{g}</b><small>{t}</small></span>{ic("ellipsis", 16)}</div>
<div class="vals">{vals}</div><div class="ft"><span>{u}</span><span class="lvl" style="--c:{c}"><i><b style="width:{[100, 30, 45, 22, 55, 34][n]}%"></b></i></span></div></div>"""
    rows = "".join(f"""<tr><td><span class="sw7" style="--c:{c}"></span>{col}</td><td>{cap} мА·год</td><td class="mono">{sku}</td><td>{pr} ₴</td>
<td><span class="lvl" style="--c:{"#E5484D" if st == 0 else ("#F59E0B" if st < 5 else "#16A34A")}"><b style="width:22px">{st}</b><i><b style="width:{min(100, st * 4)}%"></b></i></span></td><td style="color:var(--mut)">{res}</td></tr>""" for col, c, cap, sku, pr, st, res in VARIANTS)
    body = f"""<div class="crumb">Склад › Товари › Атрибути</div><div class="hd"><div><h1>Атрибути</h1><div class="subt">6 груп · з них складаються варіанти товарів</div></div>
<div class="r"><span class="seg"><span>Товари</span><span>Категорії</span><span>Бренди</span><span class="on">Атрибути</span></span><span class="btn b">{ic("plus", 16)}Атрибут</span></div></div>
<div class="ag">{cards}</div>
<div class="card" style="flex:1;overflow:hidden"><h3>Колір у товарі «Павербанк Volt»<span style="font-size:12px;background:var(--bg);border-radius:6px;padding:0 6px;color:var(--mut)">6 варіантів</span>
<span class="r"><span class="btn" style="height:32px">{ic("layers", 14)}Згенерувати</span><span class="btn l" style="height:32px">{ic("check", 14)}Зберегти</span></span></h3>
<table style="margin-top:6px"><thead><tr><th>Колір</th><th>Ємність</th><th>Артикул</th><th>Ціна</th><th>Залишок</th><th>Резерв</th></tr></thead><tbody>{rows}</tbody></table></div>"""
    return f'<div class="v7">{side("products")}<main class="main">{body}</main></div>'


def phone(inner, tab_on, acts=None):
    tabs = [("home", "house", "Головна"), ("orders", "receipt-text", "Замовлення"), ("+", "", ""), ("leads", "inbox", "Ліди"), ("more", "layout-grid", "Ще")]
    t = "".join('<span class="fab">' + ic("plus", 24, 2.2) + '</span>' if k == "+" else f'<span class="{"on" if k == tab_on else ""}">{ic(i, 20)}{n}</span>' for k, i, n in tabs)
    bottom = acts if acts else f'<div class="tab">{t}</div>'
    return f'<div class="ph"><div class="scr"><div class="isl"></div><div class="sb"><span>9:41</span><span>{ic("activity", 14)}</span></div><div class="bd">{inner}</div>{bottom}</div></div>'


def mobile():
    h = f"""<div style="display:flex;align-items:center;gap:10px"><span style="width:38px;height:38px;border-radius:50%;background:#FFD7B8;display:grid;place-items:center;font-weight:600;font-size:13px">ОЛ</span>
<span><span class="mut">Четвер, 29 жовтня</span><h2 style="font-size:19px">Добрий день, Олено</h2></span><span style="margin-left:auto">{ic("bell", 20)}</span></div>
<div class="c hero"><div style="display:flex;justify-content:space-between;font-size:12.5px;color:#C9CEFF"><span>План на жовтень</span><span>312 / 360 тис</span></div><b>86%</b><div class="pb"><i></i></div></div>
<div class="k3"><div class="c"><b>18</b><small>сьогодні</small></div><div class="c"><b>68%</b><small>апрув</small></div><div class="c"><b>9</b><small>без ТТН</small></div></div>
<div style="display:flex;justify-content:space-between;align-items:center"><b style="font-weight:600">Ліди · 5</b><span style="color:#2D3FE7;font-size:12.5px">Усі</span></div>
{"".join(f'<div class="row"><span class="ck"></span><span><b>{n}</b><small>{p}</small></span><span class="s">{s}</span></div>' for n, p, s in [("Коваленко Ірина", "Набір кабелів · 14:18", "649 ₴"), ("Дорошенко Ігор", "Павербанк 20000 · щойно", "1 599 ₴"), ("Савчук Олена", "Лампа LED · 3 хв", "899 ₴")])}"""
    lst = f"""<div style="display:flex;align-items:center"><h2>Замовлення</h2><span style="margin-left:auto;display:flex;gap:14px">{ic("search", 20)}{ic("funnel", 20)}</span></div>
<div class="mut">248 за жовтень · 31 чекають відправки</div><div class="chips"><span class="on">Усі 248</span><span>Підтверджено 31</span><span>У дорозі 57</span></div>
{"".join(f'<div class="row" style="flex-wrap:wrap"><span style="flex:1;min-width:0"><b>{o[1]}</b><small>№{o[0]} · {o[3]}</small></span><span class="s">{o[5]} ₴</span><span style="width:100%;display:flex;justify-content:space-between;align-items:center;margin-top:4px">{pill(o[6])}<small style="font-size:11.5px;color:#6B6F86">{o[7]}</small></span></div>' for o in ORDERS[:5])}"""
    o = ORDER
    cd = f"""<div style="display:flex;align-items:center;gap:14px">{ic("chevron-left", 22)}<span class="mut" style="margin-left:auto">№1482</span>{ic("ellipsis", 20)}</div>
{pill("ok")}<h2 style="font-size:21px">{o["name"]}</h2>
<div class="kv"><span>Телефон</span><b style="font-weight:500">{o["phone"]}</b><span>Менеджер</span><b style="font-weight:500">Олена Литвин</b><span>Юрособа</span><b style="font-weight:500">ФОП Максимчук О. В.</b><span>Джерело</span><b style="font-weight:500">Instagram</b></div>
<div class="c"><div class="mut" style="margin-bottom:6px">Товари</div><div style="display:flex;justify-content:space-between;font-size:13px"><span>Павербанк 20000, чорний</span><b style="font-weight:500">1 599 ₴</b></div>
<div style="display:flex;justify-content:space-between;font-size:13px;color:#6B6F86;margin-top:4px"><span>↳ Кабель USB-C 1 м</span><span>198 ₴</span></div>
<div style="display:flex;justify-content:space-between;margin-top:8px;padding-top:8px;border-top:1px dashed #E7E8F0"><span class="mut">До сплати</span><b style="font-size:18px">1 597 ₴</b></div></div>
<div class="c"><div class="mut" style="margin-bottom:6px">Нова Пошта · Київ, №12</div><b style="font:500 14px 'JB',monospace">20450913998365</b><div class="mut" style="margin-top:4px">Прямує до відділення · 30.10</div></div>"""
    acts = f'<div class="acts"><span>{ic("phone", 17)}</span><span>{ic("message-circle", 17)}</span><span class="l">{ic("truck", 17)}Створити ТТН</span></div>'
    return f'<div class="v7m">{phone(h, "home")}{phone(lst, "orders")}{phone(cd, "orders", acts)}</div>'


def build():
    return page("Варіант 7 — Кобальт", CSS, [
        ("1-menu", "Бокова панель з відділом і джерелами + головна зі справами", home(), None, None),
        ("2-card", "Замовлення списком по статусах + картка збоку з чеклистом", orders(), None, None),
        ("3-settings", "Налаштування: статуси, сповіщення, вигляд", settings(), None, None), ("4-attrs", "Атрибути картками + варіанти", attributes(), None, None),
        ("5-mobile", "Телефон: головна, список, картка", mobile(), None, None)])
