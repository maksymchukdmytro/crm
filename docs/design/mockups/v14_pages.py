"""Варіант 14 — 10 сторінок CRM у стилі обраної картки (v13).
Правило заокруглень: усе, що натискають (кнопки, статуси, вкладки, фільтри, позначки, пункти меню) — пігулки;
усе, куди вводять (поля, списки вибору, пошук) — 8 px; картки, блоки, панелі — 14 px; вікна — 18 px."""
from common import *

CSS = """
.ap{--ink:#1F1F1C;--mut:#6F6E69;--faint:#A3A29D;--line:#ECECE9;--soft:#F2F2EF;--bg:#F7F7F5;--acc:#2E6BE6;--acc2:#EAF1FD;--acc3:#C9DBFA;
  --ok:#16A34A;--ok2:#E9F6EE;--warn:#D97706;--warn2:#FDF1E3;--bad:#DC2626;--bad2:#FDECEC;
  font:400 13.5px/1.45 'Onest',sans-serif;color:var(--ink);width:100%;height:100%;display:flex;background:var(--bg);position:relative;overflow:hidden}
.ap b{font-weight:600}
/* бокова панель */
.sb{width:236px;flex:none;display:flex;flex-direction:column;padding:14px 12px 12px;gap:2px}
.sb .br{display:flex;align-items:center;gap:9px;padding:2px 6px 10px}
.sb .lg{flex:none;width:30px;height:30px;border-radius:9px;background:var(--acc);color:#fff;display:grid;place-items:center;font:600 15px 'Onest'}
.sb .br b{font-size:15px}.sb .dp{height:32px;padding:0 10px;border-radius:99px;border:1px solid var(--line);background:#fff;font-size:12.5px;display:flex;align-items:center;gap:7px;color:var(--mut);white-space:nowrap;margin:0 0 4px}
.sb .gh{font-size:11.5px;color:var(--faint);padding:9px 10px 2px}
.sb .it{height:32px;border-radius:99px;padding:0 10px;display:flex;align-items:center;gap:10px;color:#3D3C38;font-size:13.5px;white-space:nowrap}
.sb .it .i{color:var(--mut)}.sb .it.on{background:#fff;box-shadow:0 0 0 1px var(--line);font-weight:500;color:var(--ink)}.sb .it.on .i{color:var(--acc)}
.sb .it em{margin-left:auto;font-style:normal;font-size:11.5px;color:var(--faint)}.sb .it em.a{background:var(--acc);color:#fff;border-radius:99px;padding:0 7px;line-height:18px;font-weight:600}
.sb .sv{height:28px;display:flex;align-items:center;gap:10px;padding:0 10px;font-size:13px;color:var(--mut);border-radius:99px}.sb .sv i{width:8px;height:8px;border-radius:3px;background:var(--c);margin:0 3px}
.sb .sv em{margin-left:auto;font-style:normal;font-size:11.5px;color:var(--faint)}
.sb .us{margin-top:auto;display:flex;align-items:center;gap:10px;padding:8px;border-radius:14px;background:#fff;box-shadow:0 0 0 1px var(--line)}
.sb .us small{display:block;font-size:11.5px;color:var(--mut)}
.av{width:32px;height:32px;border-radius:50%;background:#E3E9F7;color:#3557A8;display:grid;place-items:center;font-size:12px;font-weight:600;flex:none}
.av.g{background:#E5F2E9;color:#2D7046}.av.o{background:#FBEEDD;color:#9A5B12}.av.p{background:#EEE8F8;color:#6A4BA8}.av.l{width:52px;height:52px;font-size:18px}
/* головна область */
.mn{flex:1;min-width:0;display:flex;flex-direction:column;padding:10px 12px 12px 0}
.tb{height:48px;flex:none;display:flex;align-items:center;gap:8px;margin-bottom:10px}
.sr{width:460px;height:38px;border-radius:8px;background:#fff;border:1px solid var(--line);display:flex;align-items:center;gap:8px;padding:0 10px;color:var(--faint)}
.sr kbd{margin-left:auto;font:500 11px 'Onest';border:1px solid var(--line);border-radius:5px;padding:1px 5px;color:var(--mut)}
.tb .r{margin-left:auto;display:flex;gap:6px;align-items:center}
.rb{width:38px;height:38px;border-radius:50%;background:#fff;border:1px solid var(--line);display:grid;place-items:center;color:var(--mut);position:relative;flex:none}
.rb em{position:absolute;top:-3px;right:-3px;width:9px;height:9px;border-radius:50%;background:var(--acc);border:2px solid var(--bg)}
.pg{flex:1;min-height:0;background:#fff;border:1px solid var(--line);border-radius:18px;padding:22px 24px;display:flex;flex-direction:column;gap:14px;overflow:hidden;position:relative}
.pg.fl{background:transparent;border:0;padding:4px 0 0;}
.ph{display:flex;align-items:flex-end;gap:12px;flex:none}
.ph .cr{font-size:12.5px;color:var(--faint);margin-bottom:3px}.ph h1{font-size:26px;font-weight:600;letter-spacing:-.02em;line-height:1.15}
.ph .sub{font-size:13px;color:var(--mut);margin-top:3px}.ph .sub b{color:var(--ink);font-weight:500}
.ph .r{margin-left:auto;display:flex;gap:6px;align-items:center}
/* кнопки — пігулки */
.bt{height:36px;padding:0 14px;border-radius:99px;background:#fff;border:1px solid var(--line);display:inline-flex;align-items:center;gap:7px;font-weight:500;font-size:13px;white-space:nowrap;color:var(--ink);flex:none}
.bt .i{color:var(--mut)}.bt.p{background:var(--acc);border-color:var(--acc);color:#fff}.bt.p .i{color:#fff}
.bt.k{background:var(--acc2);border-color:var(--acc3);color:var(--acc)}.bt.k .i{color:var(--acc)}
.bt.s{height:30px;padding:0 11px;font-size:12.5px;gap:5px}.bt.q{border-color:transparent;background:transparent}.bt.d{color:var(--bad)}.bt.d .i{color:var(--bad)}
.bt.off{color:#C2C1BC;background:var(--bg);border-color:transparent}.bt.off .i{color:#C9C8C3}
.bt kbd{font:500 11px 'Onest';opacity:.65}
/* вкладки, сегменти, фільтри */
.tabs{display:flex;gap:2px;flex:none;flex-wrap:nowrap}
.tab{height:34px;padding:0 10px;border-radius:99px;display:inline-flex;align-items:center;gap:7px;font-size:13px;color:var(--mut);white-space:nowrap;font-weight:500}
.tab em{font-style:normal;font-size:11.5px;color:var(--faint);font-weight:500}.tab em.a{background:var(--acc);color:#fff;border-radius:99px;padding:0 7px;line-height:18px}
.tab.on{background:var(--ink);color:#fff}.tab.on em{color:#B9B8B3}
.seg{display:inline-flex;padding:3px;border-radius:99px;background:var(--soft);gap:2px}
.seg span{height:30px;padding:0 12px;border-radius:99px;display:inline-flex;align-items:center;gap:6px;font-size:12.5px;color:var(--mut);font-weight:500}
.seg span.on{background:#fff;color:var(--ink);box-shadow:0 1px 2px rgba(0,0,0,.08)}
.fls{display:flex;gap:6px;align-items:center;flex:none}
.ch{height:30px;padding:0 11px;border-radius:99px;border:1px dashed #D9D8D3;display:inline-flex;align-items:center;gap:6px;font-size:12.5px;color:var(--mut);white-space:nowrap}
.ch.on{border:1px solid var(--acc3);background:var(--acc2);color:var(--acc);font-weight:500}
.in{height:34px;border-radius:8px;border:1px solid var(--line);background:#fff;display:flex;align-items:center;gap:7px;padding:0 10px;min-width:0;white-space:nowrap;overflow:hidden}
.in .i{color:var(--faint)}.in .cv{margin-left:auto;color:var(--faint)}.in.ph2{color:var(--faint)}.in.ro{background:var(--bg);color:var(--mut)}
.in.fo{border-color:var(--acc);box-shadow:0 0 0 3px var(--acc2)}
/* статуси */
.st{height:24px;padding:0 9px 0 8px;border-radius:99px;display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:500;white-space:nowrap;
  background:color-mix(in srgb,var(--c) 11%,white);color:color-mix(in srgb,var(--c) 78%,black)}
.st i{width:6px;height:6px;border-radius:50%;background:var(--c)}
.tg{height:20px;padding:0 7px;border-radius:99px;font-size:11px;font-weight:500;display:inline-flex;align-items:center;gap:4px;background:var(--soft);color:var(--mut);white-space:nowrap}
.tg.v{background:#F4EEDB;color:#8A6A12}.tg.r{background:var(--bad2);color:var(--bad)}.tg.a{background:var(--acc2);color:var(--acc)}.tg.g{background:var(--ok2);color:#15803D}
.src{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;color:var(--mut)}.src i{width:8px;height:8px;border-radius:3px;background:var(--c)}
/* блоки */
.c{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 18px;display:flex;flex-direction:column;gap:12px;min-width:0;overflow:hidden}
.c h3{font-size:15px;font-weight:600;display:flex;align-items:center;gap:8px}.c h3 small{font-weight:400;font-size:12.5px;color:var(--faint)}
.c h3 .r{margin-left:auto;display:flex;gap:6px;font-weight:500}
.c .lk{color:var(--acc);font-size:12.5px;font-weight:500;display:inline-flex;align-items:center;gap:3px}
.grid{display:grid;gap:12px;min-height:0}
.col{display:flex;flex-direction:column;gap:12px;min-height:0;min-width:0}
.kpi{display:flex;flex-direction:column;gap:4px}
.kpi small{font-size:12.5px;color:var(--mut);display:flex;align-items:center;gap:6px}.kpi .v{font-size:28px;font-weight:600;letter-spacing:-.02em;line-height:1.1}
.kpi .d{font-size:12px;color:var(--mut)}.kpi .d b{font-weight:500;color:var(--ok)}.kpi .d b.n{color:var(--bad)}
.kpi.ac{background:var(--acc2);border-color:var(--acc3)}.kpi.ac .v{color:var(--acc)}
/* таблиця */
.tbl{border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#fff;display:flex;flex-direction:column;min-height:0}
.tr{display:grid;align-items:center;gap:12px;padding:0 14px;height:46px;border-top:1px solid var(--line);font-size:13px;white-space:nowrap}
.tr>*{min-width:0;overflow:hidden;text-overflow:ellipsis}
.tr.h{height:36px;border-top:0;color:var(--faint);font-size:12px;background:#FCFCFB}
.tr.g{height:36px;background:var(--bg);font-size:12.5px;color:var(--mut)}.tr.g b{color:var(--ink);font-weight:600}
.tr.sel{background:#F4F8FE}.tr.hv{background:#FAFAF8}
.tr .t2{display:flex;flex-direction:column;line-height:1.3}.tr .t2 small{font-size:12px;color:var(--faint)}
.tr .n{font:500 12.5px 'JB',monospace;color:var(--mut)}.tr .sum{text-align:right;font-weight:600}
.cb{width:16px;height:16px;border-radius:5px;border:1.5px solid #CFCEC9;display:grid;place-items:center;flex:none;background:#fff}
.cb.on{background:var(--acc);border-color:var(--acc);color:#fff}
.ha{display:flex;gap:4px;justify-content:flex-end}.ha span{width:28px;height:28px;border-radius:50%;border:1px solid var(--line);background:#fff;display:grid;place-items:center;color:var(--mut)}
.im{width:36px;height:36px;border-radius:9px;background:var(--soft);display:grid;place-items:center;color:var(--mut);flex:none}
.im.l{width:64px;height:64px;border-radius:12px}
.pr{display:flex;align-items:center;gap:10px}
.bar{height:6px;border-radius:99px;background:var(--soft);overflow:hidden;flex:1}.bar i{display:block;height:100%;border-radius:99px;background:var(--c,var(--acc))}
/* панель масових дій */
.bulk{position:absolute;left:calc(50% + 118px);transform:translateX(-50%);bottom:18px;z-index:5;background:#fff;border:1px solid var(--line);border-radius:14px;height:56px;padding:0 10px;
  display:flex;align-items:center;gap:6px;box-shadow:0 18px 40px -16px rgba(0,0,0,.28);white-space:nowrap}
.bulk .sep{width:1px;height:22px;background:var(--line);margin:0 4px}.bulk .cnt{display:flex;align-items:center;gap:8px;padding:0 6px;font-weight:500}
.fab{position:absolute;right:26px;bottom:24px;z-index:5;width:54px;height:54px;border-radius:50%;background:var(--acc);color:#fff;display:grid;place-items:center;box-shadow:0 12px 26px -10px rgba(46,107,230,.75)}
/* вікна поверх */
.dim{position:absolute;inset:0;background:rgba(24,24,22,.36);z-index:8}
.win{position:absolute;z-index:9;background:var(--bg);border-radius:18px;box-shadow:0 40px 80px -30px rgba(0,0,0,.45);display:flex;flex-direction:column;overflow:hidden}
.wh{display:flex;align-items:center;gap:10px;padding:16px 20px;flex:none}.wh h2{font-size:19px;font-weight:600;letter-spacing:-.01em}.wh small{color:var(--mut);font-size:13px}
.wh .r{margin-left:auto;display:flex;gap:6px}
.wf{display:flex;align-items:center;gap:8px;padding:12px 20px;border-top:1px solid var(--line);background:#fff;flex:none}
.lab{font-size:12px;color:var(--mut);margin-bottom:5px;display:block}
.fld{display:flex;flex-direction:column}
.hint{font-size:12px;color:var(--acc);display:flex;align-items:center;gap:5px}
.note{font-size:12px;color:var(--faint);display:flex;align-items:center;gap:5px}
.dd{position:absolute;left:0;right:0;top:62px;background:#fff;border:1px solid var(--line);border-radius:12px;box-shadow:0 18px 36px -14px rgba(0,0,0,.28);padding:5px;z-index:3}
.dd div{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:8px;font-size:13px}.dd div small{margin-left:auto;color:var(--faint);font-size:12px}
.dd div.on{background:var(--acc2)}.dd .i{color:var(--mut)}
.sw{display:inline-block;vertical-align:middle;width:38px;height:22px;border-radius:99px;background:#D9D8D3;position:relative;flex:none}.sw::after{content:"";position:absolute;left:3px;top:3px;width:16px;height:16px;border-radius:50%;background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.2)}
.sw.on{background:var(--acc)}.sw.on::after{left:19px}
.ok{color:var(--ok)}.wr{color:var(--warn)}.bd{color:var(--bad)}.mu{color:var(--mut)}.fa{color:var(--faint)}
.kv{display:grid;grid-template-columns:110px 1fr;gap:8px 12px;font-size:13px}.kv span{color:var(--mut)}.kv b{font-weight:500}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.tiles div{background:var(--bg);border-radius:10px;padding:8px 10px;min-width:0;white-space:nowrap}
.tiles b{display:block;font-size:17px;font-weight:600}.tiles small{font-size:11.5px;color:var(--mut)}
"""

# ---------------------------------------------------------------- дані
S = {
    "uns": ("Несортований", "#7C7B76"), "acc": ("Прийнятий", "#2E6BE6"), "sent": ("Відправлений", "#6D5BD0"),
    "wait": ("Очікує на отримання", "#D97706"), "done": ("Завершений", "#16A34A"), "pref": ("Відмова на пошті", "#E11D48"),
    "back": ("Повернуто на склад", "#64748B"), "ref": ("Відмова", "#DC2626"),
    "lnew": ("Новий", "#2E6BE6"), "lno": ("Недодзвон", "#D97706"), "lcb": ("Передзвонити", "#7C3AED"),
}
SRC = {"Instagram": "#D6409F", "Лендинг": "#2E6BE6", "Rozetka": "#00A046", "Prom": "#7B3FE4", "Facebook": "#1877F2", "TikTok": "#1F1F1C", "Сайт": "#0891B2", "Вручну": "#A3A29D"}


def st(code):
    n, c = S[code]
    return f'<span class="st" style="--c:{c}"><i></i>{n}</span>'


def src(name):
    return f'<span class="src" style="--c:{SRC[name]}"><i></i>{name}</span>'


def cb(on=False):
    return f'<span class="cb {"on" if on else ""}">{ic("check", 11, 3) if on else ""}</span>'


NAV2 = [
    ("Продажі", [("home", "Головна", "house", ""), ("leads", "Ліди", "inbox", "a7"), ("orders", "Замовлення", "receipt-text", "a9"),
                 ("invoices", "Видаткові накладні", "file-text", ""), ("board", "Дошка", "square-kanban", ""), ("customers", "Покупці", "contact", "")]),
    ("Склад", [("products", "Товари", "package", "86"), ("stock", "Склад", "boxes", ""), ("purchases", "Закупівлі", "shopping-cart", "")]),
    ("Гроші й аналітика", [("payments", "Оплати", "wallet", ""), ("stats", "Статистика", "chart-column-stacked", ""), ("reports", "Звіти", "chart-bar", "")]),
    ("Керування", [("audit", "Журнал дій", "clock-fading", ""), ("settings", "Налаштування", "settings", ""), ("system", "Система", "activity", "")]),
]


def sidebar(active):
    out = [f'<aside class="sb"><div class="br"><span class="lg">m</span><b>mdmy</b></div><div class="dp">{ic("building", 14)}Відділ: Інтернет-магазин<span style="margin-left:auto;display:flex">{ic("chevron-down", 14)}</span></div>']
    for g, items in NAV2:
        out.append(f'<div class="gh">{g}</div>')
        for k, n, i, cnt in items:
            em = f'<em class="a">{cnt[1:]}</em>' if cnt.startswith("a") else (f"<em>{cnt}</em>" if cnt else "")
            out.append(f'<div class="it {"on" if k == active else ""}">{ic(i, 17)}{n}{em}</div>')
    out.append('<div class="gh">Збережені фільтри</div>')
    for n, c, k in [("Чекають ТТН", "#2E6BE6", "14"), ("Передзвонити сьогодні", "#7C3AED", "5")]:
        out.append(f'<div class="sv" style="--c:{c}"><i></i>{n}<em>{k}</em></div>')
    out.append(f'<div class="us"><span class="av">ОЛ</span><span><b style="font-weight:500">Олена Литвин</b><small>Менеджер</small></span></div></aside>')
    return "".join(out)


def topbar():
    return f"""<div class="tb"><div class="sr">{ic("search", 16)}Шукати замовлення, телефон, ТТН або товар…<kbd>Ctrl K</kbd></div>
<div class="r"><span class="rb">{ic("message-square", 17)}</span><span class="rb">{ic("bell", 17)}<em></em></span></div></div>"""


def shell(active, content, fab=True, extra="", flat=False):
    f = f'<span class="fab">{ic("plus", 26, 2.2)}</span>' if fab else ""
    return f'<div class="ap">{sidebar(active)}<div class="mn">{topbar()}<div class="pg {"fl" if flat else ""}">{content}</div></div>{f}{extra}</div>'


def head(crumb, title, sub, right=""):
    return f'<div class="ph"><div><div class="cr">{crumb}</div><h1>{title}</h1><div class="sub">{sub}</div></div><div class="r">{right}</div></div>'


def tr(cols, cells, cls=""):
    if cls.split()[:1] == ["g"]:
        return f'<div class="tr {cls}" style="display:flex;padding-left:{52 if cells[0] == "" and cols.startswith("26px") else 14}px">{cells[2]}</div>'
    return f'<div class="tr {cls}" style="grid-template-columns:{cols}">' + "".join(f"<div>{c}</div>" for c in cells) + "</div>"


# ---------------------------------------------------------------- 1. Головна
def home(bg=False):
    days = [("Пн", 21, 18), ("Вт", 26, 22), ("Ср", 19, 24), ("Чт", 31, 23), ("Пт", 28, 26), ("Сб", 17, 15), ("Нд", 14, 12)]
    mx = 34
    bars = "".join(
        f'<g transform="translate({30 + k * 92},0)"><rect x="0" y="{170 - p / mx * 150}" width="22" height="{p / mx * 150}" rx="5" fill="#E4E3DF"/>'
        f'<rect x="26" y="{170 - v / mx * 150}" width="22" height="{v / mx * 150}" rx="5" fill="#2E6BE6"/>'
        f'<text x="24" y="190" text-anchor="middle" font-size="12" fill="#6F6E69">{d}</text>'
        f'<text x="37" y="{164 - v / mx * 150}" text-anchor="middle" font-size="11.5" font-weight="600" fill="#1F1F1C">{v}</text></g>'
        for k, (d, v, p) in enumerate(days))
    grid_lines = "".join(f'<line x1="20" x2="680" y1="{170 - t / mx * 150}" y2="{170 - t / mx * 150}" stroke="#F0F0ED"/>' for t in (10, 20, 30))
    chart = f'<svg viewBox="0 0 690 196" width="100%" height="196">{grid_lines}{bars}</svg>'
    recent = [(1482, "Шевченко Тарас", "Павербанк Volt 20 000", "acc", "1 797"), (1481, "Коваленко Ірина", "Набір кабелів USB-C", "uns", "649"),
              (1480, "Бондаренко Олег", "Навушники TWS Pro", "sent", "1 290"), (1479, "Ткаченко Марія", "Лампа настільна LED", "wait", "1 048"),
              ]
    rc = "64px 1.3fr 1.6fr 170px 90px"
    rows = tr(rc, ["№", "Покупець", "Товар", "Статус", '<span style="display:block;text-align:right">Сума</span>'], "h") + "".join(
        tr(rc, [f'<span class="n">{n}</span>', nm, g, st(s), f'<span class="sum" style="display:block">{m} ₴</span>']) for n, nm, g, s, m in recent)
    att = [("Не забирають 3+ дні", "Очікує на отримання", "6", "Подзвонити", "wr"), ("Відмова на пошті", "Посилки їдуть назад", "4", "Прийняти", "bd"),
           ("Гроші не надійшли", "Завершені без оплати НП", "2", "Перевірити", "bd"), ("Без руху 2+ дні", "Прийняті без ТТН", "3", "Відкрити", "wr")]
    att_html = "".join(f'<div style="display:flex;align-items:center;gap:12px;padding:9px 0;border-top:1px solid var(--line)"><span style="font-size:20px;font-weight:600;width:26px" class="{c}">{k}</span>'
                       f'<span style="flex:1;line-height:1.3"><b style="font-weight:500;display:block">{t}</b><small class="mu" style="font-size:12px">{s}</small></span><span class="bt s">{a}</span></div>' for t, s, k, a, c in att)
    ready = "".join(f'<span style="display:flex;flex-direction:column;align-items:center;gap:4px;font-size:11.5px;color:var(--mut)"><span class="rb" style="width:34px;height:34px;{c}">{ic(i, 15)}</span>{n}</span>'
                    for i, n, c in [("boxes", "Резерв 14", "color:var(--ok);border-color:#CDEBD8;background:var(--ok2)"), ("truck", "ТТН 9", "color:var(--acc);border-color:var(--acc3);background:var(--acc2)"),
                                    ("tag", "Наклейка 7", ""), ("receipt", "Чек 9", ""), ("list-checks", "Реєстр 5", "")])
    body = f"""{head("Четвер, 29 жовтня", "Доброго дня, Олено", "У вас <b>7 лідів</b> чекають дзвінка і <b>9 замовлень</b> не розібрано", '<span class="seg"><span class="on">Сьогодні</span><span>Тиждень</span><span>Місяць</span></span>')}
<div class="grid" style="grid-template-columns:repeat(4,1fr);flex:none">
<div class="c kpi"><small>{ic("receipt-text", 15)}Нових замовлень</small><span class="v">18</span><span class="d"><b>+4</b> до вчора</span></div>
<div class="c kpi"><small>{ic("banknote", 15)}Сума замовлень</small><span class="v">24 316 ₴</span><span class="d"><b>+11%</b> до вчора</span></div>
<div class="c kpi ac"><small>{ic("inbox", 15)}Ліди чекають дзвінка</small><span class="v">7</span><span class="d">найдовше чекає <b class="n">18 хв</b></span></div>
<div class="c kpi"><small>{ic("percent", 15)}Викуп за 30 днів</small><span class="v">78%</span><span class="d"><b class="n">−2 п.</b> до вересня</span></div></div>
<div class="grid" style="grid-template-columns:8fr 4fr;flex:1">
<div class="col"><div class="c" style="flex:none"><h3>Замовлення за тиждень<small>цей тиждень — синім, минулий — сірим</small><span class="r"><span class="lk">Статистика{ic("chevron-right", 14)}</span></span></h3>{chart}</div>
<div class="c" style="flex:1;padding-bottom:6px"><h3>Останні замовлення<span class="r"><span class="lk">Усі замовлення{ic("chevron-right", 14)}</span></span></h3><div style="margin:0 -18px">{rows}</div></div></div>
<div class="col"><div class="c"><h3>До відправки сьогодні<span class="r"><span class="tg a">{ic("clock", 12)}кур'єр о 16:00</span></span></h3>
<div style="display:flex;align-items:baseline;gap:8px"><span style="font-size:28px;font-weight:600;letter-spacing:-.02em">5 з 14</span><span class="mu">готові до передачі</span></div>
<div class="bar" style="flex:none"><i style="width:36%"></i></div><div style="display:flex;justify-content:space-between">{ready}</div>
<span class="bt k" style="justify-content:center">Відкрити список «До відправки»</span></div>
<div class="c" style="flex:1;gap:4px"><h3 style="margin-bottom:6px">Потребує уваги<small>15</small></h3>{att_html}</div></div></div>"""
    return shell("home", body, fab=not bg)


# ---------------------------------------------------------------- 2. Замовлення
ORD = [
    (1482, "Шевченко Тарас", "+380 67 123 45 67", "Павербанк Volt 20 000", "+1", "acc", "НП · Київ, №12", "ТТН не створена", "Instagram", "ОЛ", "14:32", "1 797", ["VIP"]),
    (1481, "Коваленко Ірина", "+380 93 552 10 08", "Набір кабелів USB-C", "", "uns", "—", "", "Сайт", "", "14:18", "649", ["Дубль?"]),
    (1480, "Бондаренко Олег", "+380 50 771 23 90", "Навушники TWS Pro", "", "sent", "НП · Львів, №4", "у дорозі", "Rozetka", "АН", "13:57", "1 290", []),
    (1479, "Ткаченко Марія", "+380 66 410 77 12", "Лампа настільна LED", "+1", "acc", "Укрпошта · Вінниця", "ТТН не створена", "Facebook", "ОЛ", "13:40", "1 048", ["Повторний"]),
    (1478, "Кравченко Андрій", "+380 97 300 45 61", "Зарядка GaN 65 Вт", "", "done", "НП · Одеса, №31", "отримано", "Prom", "АН", "12:15", "749", []),
    (1477, "Олійник Світлана", "+380 68 905 12 44", "Павербанк 10 000", "", "pref", "НП · Дніпро, №7", "повертається", "Instagram", "ОЛ", "11:52", "999", []),
    (1476, "Мельник Денис", "+380 63 118 90 05", "Смарт-годинник Fit 3", "+1", "wait", "НП · Тульчин, №1", "4-й день", "TikTok", "АН", "11:30", "2 398", []),
    (1475, "Шевчук Анна", "+380 95 640 31 27", "Чохол MagSafe", "", "acc", "Meest · Київ", "ТТН не створена", "Лендинг", "ОЛ", "10:47", "449", []),
    (1474, "Поліщук Віктор", "+380 73 222 81 19", "Колонка Go Mini", "", "sent", "НП · Харків, №52", "у дорозі", "Rozetka", "АН", "10:05", "1 599", []),
    (1473, "Лисенко Юлія", "+380 99 731 04 66", "Кабель Lightning 2 м", "+1", "uns", "—", "", "Сайт", "", "09:41", "398", []),
    (1472, "Гнатюк Роман", "+380 67 880 15 72", "Павербанк Volt 20 000", "", "back", "НП · Київ, №201", "на складі", "Facebook", "ОЛ", "09:12", "1 599", []),
    (1471, "Данилюк Ольга", "+380 50 120 33 41", "Навушники TWS Pro", "", "ref", "—", "", "Лендинг", "АН", "08:55", "1 290", ["Чорний список"]),
]
OC = "26px 52px 1.5fr 1.4fr 166px 1.25fr 96px 64px 44px 82px"


def order_rows(n=12, sel=(1482, 1479, 1475), hover=None):
    out = [tr(OC, [cb(), "№", "Покупець", "Товар", "Статус", "Доставка", "Джерело", "Менеджер", "Час", '<span style="display:block;text-align:right">Сума</span>'], "h"),
           tr(OC, ["", "", f'<b>Сьогодні, 29 жовтня</b> · 10 замовлень · 12 316 ₴', "", "", "", "", "", "", ""], "g")]
    for k, (no, nm, ph, g, more, s, dl, dls, so, mg, t, sm, tags) in enumerate(ORD[:n]):
        if k == 10:
            out.append(tr(OC, ["", "", "<b>Учора, 28 жовтня</b> · 24 замовлення · 31 870 ₴", "", "", "", "", "", "", ""], "g"))
        tg = "".join(f' <span class="tg {"v" if x == "VIP" else "r" if x in ("Чорний список", "Дубль?") else ""}">{x}</span>' for x in tags)
        dcls = "wr" if dls in ("ТТН не створена", "4-й день") else "bd" if dls == "повертається" else "fa"
        dlv = f'<span class="t2"><span>{dl}</span><small class="{dcls}">{dls}</small></span>' if dls else '<span class="fa">не вибрано</span>'
        mgr = f'<span class="av {"g" if mg == "АН" else ""}" style="width:26px;height:26px;font-size:10.5px">{mg}</span>' if mg else '<span class="fa">—</span>'
        good = f'{g} <span class="fa">{more}</span>' if more else g
        last = f'<span class="sum" style="display:block">{sm} ₴</span>'
        cls = "sel" if no in sel else ("hv" if no == hover else "")
        if no == hover:
            last = f'<span class="ha"><span>{ic("phone", 14)}</span><span>{ic("tag", 14)}</span><span>{ic("eye", 14)}</span></span>'
        out.append(tr(OC, [cb(no in sel), f'<span class="n">{no}</span>', f'<span class="t2"><span>{nm}{tg}</span><small>{ph}</small></span>', good, st(s), dlv, src(so), mgr,
                           f'<span class="fa">{t}</span>', last], cls))
    return "".join(out)


def orders_tabs(active="Усі"):
    tabs = [("Несортовані", "a9"), ("Прийнятий", "31"), ("Відправлений", "57"), ("Очікує на отримання", "22"), ("Завершений", "96"),
            ("Відмова на пошті", "4"), ("Повернуто на склад", "3"), ("Відмова", "9"), ("Усі", "248")]
    return '<div class="tabs">' + "".join(
        f'<span class="tab {"on" if n == active else ""}">{n}<em class="{"a" if c.startswith("a") else ""}">{c.lstrip("a")}</em></span>' for n, c in tabs) + "</div>"


def orders(bg=False):
    bulk = "" if bg else f"""<div class="bulk"><span class="cnt">{cb(True)}Вибрано 3</span><span class="sep"></span><span class="bt s">Статус{ic("chevron-down", 13)}</span><span class="bt s">Менеджер{ic("chevron-down", 13)}</span>
<span class="bt s">{ic("tag", 14)}Наклейки</span><span class="bt s">{ic("list-checks", 14)}Реєстр НП</span><span class="bt s">{ic("receipt", 14)}Фіскалізувати</span><span class="bt s q">{ic("x", 14)}Зняти вибір</span>
<span class="sep"></span><span class="bt p">{ic("truck", 15)}Створити 3 ТТН</span></div>"""
    body = f"""{head("Продажі › Замовлення", "Замовлення", "<b>9</b> несортованих · <b>31</b> чекають відправки · <b>57</b> у дорозі",
                f'<span class="bt">{ic("rows-3", 15)}Колонки</span><span class="bt">{ic("file-text", 15)}Експорт</span>')}
{orders_tabs()}
<div class="fls"><span class="ch on">{ic("calendar", 13)}Сьогодні й учора{ic("x", 13)}</span><span class="ch">{ic("plus", 13)}Менеджер</span><span class="ch">{ic("plus", 13)}Джерело</span><span class="ch">{ic("plus", 13)}Юрособа</span>
<span class="ch">{ic("plus", 13)}Доставка</span><span class="ch">{ic("plus", 13)}Оплата</span><span class="ch">{ic("plus", 13)}Позначки</span><span class="in" style="margin-left:auto;width:250px;height:32px">{ic("search", 15)}<span class="fa">Пошук у списку</span></span></div>
<div class="tbl" style="flex:1">{order_rows(hover=None if bg else 1478)}</div>"""
    return shell("orders", body, fab=False, extra=bulk)


# ---------------------------------------------------------------- 3. Ліди
def lead_card(no, nm, g, sm, so, wait, wc, att, cbk=None, on=False):
    nm = nm
    w = f'<span class="tg {"r" if wc == "bd" else ""}" style="{"background:var(--warn2);color:#B45309" if wc == "wr" else ""}">{ic("clock", 12)}{wait}</span>'
    if cbk:
        w = f'<span class="tg" style="background:#F1ECFB;color:#6D28D9">{ic("phone", 12)}{cbk}</span>'
    return f"""<div class="c" style="padding:12px 14px;gap:7px;{'box-shadow:0 0 0 2px var(--acc3);border-color:var(--acc)' if on else ''}"><div style="display:flex;align-items:center;gap:8px"><span class="n" style="font:500 12px 'JB';color:var(--faint)">Л-{no}</span>{src(so)}<span style="margin-left:auto">{w}</span></div>
<b style="font-weight:600;font-size:14.5px">{nm}</b><div style="display:flex;align-items:center;gap:8px;font-size:12.5px"><span class="mu" style="flex:1">{g}</span><b style="font-weight:600;font-size:13px">{sm} ₴</b></div>
<div style="display:flex;align-items:center;gap:6px;border-top:1px solid var(--line);padding-top:8px;margin-top:2px"><span class="fa" style="font-size:12px">{att}</span><span style="margin-left:auto" class="bt s">{ic("phone", 13)}Подзвонити</span></div></div>"""


def leads():
    cols = [
        ("lnew", "Новий", "7", [("2047", "Іваненко Наталія", "Павербанк Volt 20 000", "1 599", "Instagram", "18 хв", "bd", "Спроба 1", None, True),
                                ("2046", "Руденко Максим", "Навушники TWS Pro", "1 290", "Лендинг", "11 хв", "wr", "Спроба 1", None),
                                ("2045", "Савченко Ірина", "Лампа настільна LED", "1 048", "TikTok", "6 хв", "wr", "Спроба 1", None),
                                ("2044", "Мороз Андрій", "Зарядка GaN 65 Вт", "749", "Facebook", "2 хв", "", "Спроба 1", None)]),
        ("lno", "Недодзвон", "4", [("2039", "Кузьменко Олег", "Смарт-годинник Fit 3", "2 398", "Instagram", "47 хв", "bd", "Спроба 3 · SMS", None),
                                    ("2041", "Петренко Алла", "Чохол MagSafe", "449", "Лендинг", "32 хв", "wr", "Спроба 2", None),
                                    ("2042", "Бойко Віталій", "Колонка Go Mini", "1 599", "TikTok", "25 хв", "wr", "Спроба 2", None)]),
        ("lcb", "Передзвонити", "3", [("2036", "Захарченко Інна", "Павербанк 10 000", "999", "Facebook", "", "", "Просила після обіду", "о 15:00"),
                                       ("2033", "Литвиненко Петро", "Набір кабелів USB-C", "649", "Instagram", "", "", "На роботі", "о 18:00"),
                                       ("2030", "Онищенко Дарина", "Навушники TWS Pro", "1 290", "Лендинг", "", "", "Думає", "завтра 10:00")]),
    ]
    board = ""
    for code, name, cnt, cards in cols:
        n, c = S[code]
        cs = "".join(lead_card(*x) for x in cards)
        board += f'<div class="col" style="background:var(--bg);border-radius:14px;padding:10px;gap:8px"><div style="display:flex;align-items:center;gap:8px;padding:2px 4px 4px">{st(code)}<span class="fa">{cnt}</span><span style="margin-left:auto" class="fa">{ic("ellipsis", 16)}</span></div>{cs}</div>'
    done = f"""<div class="col" style="gap:12px"><div class="c kpi ac"><small>{ic("circle-check-big", 15)}Створено замовлень сьогодні</small><span class="v">12</span><span class="d">з 19 оброблених лідів · конверсія <b>63%</b></span></div>
<div class="c" style="gap:10px"><h3>Сьогодні</h3><div class="kv" style="grid-template-columns:150px 1fr"><span>Середнє очікування</span><b>7 хв</b><span>Недодзвонів</span><b>4</b><span>Відмов ліда</span><b>3 · «не цікаво»</b><span>Дублів</span><b>1</b></div></div>
<div class="c" style="gap:10px"><h3>Пороги очікування</h3><div style="display:flex;flex-direction:column;gap:8px;font-size:12.5px"><span style="display:flex;gap:8px;align-items:center"><span class="tg">до 5 хв</span>звичайно</span>
<span style="display:flex;gap:8px;align-items:center"><span class="tg" style="background:var(--warn2);color:#B45309">5–15 хв</span>варто поспішити</span><span style="display:flex;gap:8px;align-items:center"><span class="tg r">понад 15 хв</span>лід холоне</span></div>
<span class="note">{ic("settings", 12)}Змінюються в налаштуваннях</span></div></div>"""
    body = f"""{head("Продажі › Ліди", "Ліди", "<b>7</b> нових чекають дзвінка · найдовше чекає <b style='color:var(--bad)'>18 хв</b>",
                f'<span class="seg"><span class="on">{ic("square-kanban", 14)}Дошка</span><span>{ic("list", 14)}Список</span><span>{ic("clock", 14)}Передзвони</span></span><span class="bt p" style="margin-left:6px">{ic("phone", 15)}Почати дзвонити</span>')}
<div class="fls"><span class="ch">{ic("plus", 13)}Джерело</span><span class="ch">{ic("plus", 13)}Товар</span><span class="ch on">{ic("user", 13)}Мої й нічиї{ic("x", 13)}</span><span class="fa" style="margin-left:auto;font-size:12.5px">Вгорі — хто чекає найдовше</span></div>
<div class="grid" style="grid-template-columns:1fr 1fr 1fr 290px;flex:1;align-items:start">{board}{done}</div>"""
    return shell("leads", body, fab=True)


# ---------------------------------------------------------------- 4. Вікно створення ТТН
def ttn():
    W, H = 1000, 720
    form = f"""<div class="c" style="gap:14px;flex:1">
<div class="grid" style="grid-template-columns:1fr 1fr"><div class="fld"><span class="lab">Відправник · ключ НП</span><span class="in"><span class="tg" style="background:#E5262B;color:#fff;height:18px;border-radius:4px">НП</span>ФОП Максимчук · Тульчин, №1<span class="cv">{ic("chevron-down", 14)}</span></span></div>
<div class="fld"><span class="lab">Отримувач</span><span class="in ro">{ic("user", 15)}Шевченко Тарас · +380 67 123 45 67</span></div></div>
<div class="fld"><span class="lab">Спосіб доставки</span><div class="fls"><span class="ch on" style="border-style:solid">{ic("store", 13)}Відділення</span><span class="ch" style="border-style:solid">{ic("package", 13)}Поштомат</span><span class="ch" style="border-style:solid">{ic("house", 13)}Кур'єр на адресу</span></div></div>
<div class="grid" style="grid-template-columns:1fr 1.5fr"><div class="fld"><span class="lab">Місто</span><span class="in">{ic("map-pin", 15)}Київ<small class="fa" style="margin-left:4px">Київська обл.</small></span></div>
<div class="fld" style="position:relative"><span class="lab">Відділення</span><span class="in fo">{ic("search", 15)}Межиг<span style="width:1px;height:16px;background:var(--ink)"></span></span>
<div class="dd"><div class="on">{ic("store", 15)}Відділення №12 · вул. Межигірська, 1<small>до 30 кг</small></div><div>{ic("store", 15)}Відділення №87 · вул. Межигірська, 54<small>до 30 кг</small></div><div>{ic("package", 15)}Поштомат №5521 · Межигірська, 22<small>до 20 кг</small></div></div></div></div>
<div class="fld"><span class="lab">Хто платить за доставку</span><div class="fls"><span class="ch on" style="border-style:solid">Отримувач</span><span class="ch" style="border-style:solid">Відправник</span><span class="ch" style="border-style:solid">Третя особа</span></div></div>
<div class="grid" style="grid-template-columns:1.3fr .8fr 1.2fr .6fr"><div class="fld"><span class="lab">Тип вантажу</span><span class="in">Посилка<span class="cv">{ic("chevron-down", 14)}</span></span></div>
<div class="fld"><span class="lab">Вага, кг</span><span class="in">{ic("weight", 15)}0,5</span></div><div class="fld"><span class="lab">Розміри, см</span><span class="in">{ic("ruler", 15)}20 × 15 × 5</span></div><div class="fld"><span class="lab">Місць</span><span class="in">1</span></div></div>
<div class="grid" style="grid-template-columns:1fr 1.4fr"><div class="fld"><span class="lab">Оголошена вартість</span><span class="in">1 797 ₴</span></div>
<div class="fld"><span class="lab">Післяплата · з оплати замовлення</span><span class="in ro">{ic("hand-coins", 15)}Контроль оплати · 1 597 ₴</span></div></div>
<div class="fld"><span class="lab">Опис</span><span class="in">Павербанк, кабель</span></div></div>"""
    side = f"""<div class="col" style="width:300px;flex:none"><div class="c kpi ac" style="gap:6px"><small>Вартість доставки</small><span class="v">≈ 85 ₴</span><span class="d">платить отримувач · за тарифом НП</span>
<div style="height:1px;background:var(--acc3);margin:6px 0"></div><div class="kv" style="grid-template-columns:1fr auto"><span>Комісія за контроль оплати</span><b>≈ 32 ₴</b><span>Очікувана доставка</span><b>пт, 30.10</b><span>Відправка</span><b>сьогодні до 18:00</b></div></div>
<div class="c" style="gap:11px"><h3>Одразу після створення</h3>
<div style="display:flex;align-items:center;gap:10px">{cb(True)}Друкувати наклейку</div><div style="display:flex;align-items:center;gap:10px">{cb(True)}Додати в реєстр на сьогодні</div>
<div style="display:flex;align-items:center;gap:10px">{cb(True)}SMS покупцю з номером ТТН</div><div style="display:flex;align-items:center;gap:10px">{cb()}Статус «Відправлений» одразу</div>
<span class="note">{ic("info", 12)}Типові значення беруться з ключа НП</span></div></div>"""
    win = f"""<div class="win" style="left:{(1440 - W) // 2}px;top:{(900 - H) // 2}px;width:{W}px;height:{H}px">
<div class="wh"><span class="rb" style="width:36px;height:36px;background:var(--acc2);border-color:var(--acc3);color:var(--acc)">{ic("truck", 17)}</span><div><h2>Нова ТТН</h2><small>Замовлення №1482 · Нова Пошта</small></div><div class="r"><span class="rb">{ic("x", 17)}</span></div></div>
<div style="flex:1;min-height:0;display:flex;gap:12px;padding:0 20px 16px">{form}{side}</div>
<div class="wf"><span class="note">{ic("circle-check-big", 13)}Адреса перевірена в довіднику НП</span><span style="margin-left:auto" class="bt">Скасувати</span><span class="bt p">{ic("truck", 15)}Створити ТТН<kbd>Ctrl ⏎</kbd></span></div></div>"""
    return _overlay(orders(bg=True), win)


def _overlay(page_html, win):
    assert page_html.endswith("</div>")
    return page_html[:-6] + '<div class="dim"></div>' + win + "</div>"


# ---------------------------------------------------------------- 5. Видаткові накладні
INV = [
    ("ФОП Максимчук О. В.", "168 накладних · 248 300 ₴", [
        ("РН-0168", "29.10", 1480, "Бондаренко Олег", "1 290", True, ""), ("РН-0167", "29.10", 1474, "Поліщук Віктор", "1 599", False, ""),
        ("РН-0166", "28.10", 1466, "Ковальчук Інна", "3 147", True, "chg"), ("РН-0165", "28.10", 1463, "Романенко Ігор", "749", False, ""),
        ("РН-0164", "28.10", 1460, "Сидоренко Лілія", "2 398", False, "ann"), ("РН-0163", "27.10", 1455, "Марченко Ольга", "1 048", True, "")]),
    ("ФОП Максимчук Д. О.", "46 накладних · 64 540 ₴", [
        ("ДМ-0046", "29.10", 1476, "Мельник Денис", "2 398", False, ""), ("ДМ-0045", "28.10", 1468, "ТОВ «Техно Плюс»", "12 450", True, ""),
        ("ДМ-0044", "27.10", 1452, "Гаврилюк Степан", "999", False, "")]),
]
IC = "26px 96px 62px 76px 1.4fr 96px 1.6fr"


def doc_btns(inv, pre=""):
    r = (f'<span class="bt s">{ic("receipt-text", 14)}Рахунок</span>' if inv else f'<span class="bt s off" title="Рахунок не виставлявся">{ic("receipt-text", 14)}Рахунок</span>')
    return f'<span style="display:flex;gap:5px;justify-content:flex-end">{pre}<span class="bt s">{ic("file-text", 14)}Накладна</span>{r}<span class="bt s">{ic("shield-check", 14)}Гарантія</span></span>'


def invoices():
    rows = [tr(IC, [cb(), "№ накладної", "Дата", "Замовлення", "Покупець", '<span style="display:block;text-align:right">Сума</span>', '<span style="display:block;text-align:right">Документи</span>'], "h")]
    for ent, meta, items in INV:
        rows.append(tr(IC, ["", "", f'<b>{ent}</b> · {meta}', "", "", "", ""], "g"))
        for no, d, o, c, s, inv, flag in items:
            num = f'<span class="n">{no}</span>'
            cust = c
            if flag == "ann":
                num = f'<span class="n" style="text-decoration:line-through;color:var(--faint)">{no}</span>'
                cust = f'{c} <span class="tg">Анульовано</span>'
            if flag == "chg":
                cust = f'{c} <span class="tg" style="background:var(--warn2);color:#B45309"><i style="width:6px;height:6px;border-radius:50%;background:var(--warn)"></i>Замовлення змінилось</span>'
            btns = doc_btns(inv, f'<span class="bt s k" title="Перевипустити">{ic("refresh-cw", 14)}</span>' if flag == "chg" else "")
            rows.append(tr(IC, [cb(), num, f'<span class="mu">{d}</span>', f'<span class="lk" style="color:var(--acc);font-weight:500">№{o}</span>', cust,
                               f'<span class="sum" style="display:block">{s} ₴</span>', btns]))
    body = f"""{head("Продажі › Видаткові накладні", "Видаткові накладні", "Жовтень 2026 · <b>214 накладних</b> · <b>312 840 ₴</b>",
                f'<span class="bt">{ic("calendar", 15)}Жовтень 2026{ic("chevron-down", 13)}</span><span class="bt">{ic("file-text", 15)}Експорт реєстру</span>')}
<div class="tabs"><span class="tab on">Усі<em>214</em></span><span class="tab">ФОП Максимчук О. В.<em>168</em></span><span class="tab">ФОП Максимчук Д. О.<em>46</em></span></div>
<div class="fls"><span class="ch">{ic("plus", 13)}Статус замовлення</span><span class="ch">{ic("plus", 13)}Є рахунок-фактура</span><span class="ch">{ic("plus", 13)}Покупець</span>
<span class="in" style="margin-left:auto;width:300px;height:32px">{ic("search", 15)}<span class="fa">№ накладної, замовлення або покупець</span></span></div>
<div class="tbl" style="flex:1">{"".join(rows)}</div>
<div class="note" style="flex:none">{ic("info", 12)}Неактивна кнопка «Рахунок» — рахунок-фактуру для цього замовлення не виставляли. Накладна й гарантійний талон створюються самі, коли замовлення стає «Відправленим».</div>"""
    return shell("invoices", body)


# ---------------------------------------------------------------- 6. Товари
PRODS = [("zap", "Павербанк Volt 20 000 мА·год", "PB-20", "1 599", 31, 6, "Павербанки", True), ("zap", "Павербанк Volt 10 000 мА·год", "PB-10", "999", 35, 3, "Павербанки", True),
         ("link", "Кабель USB-C → USB-C 1 м", "CB-C1", "198", 140, 2, "Кабелі", True), ("link", "Кабель Lightning 2 м", "CB-L2", "249", 4, 2, "Кабелі", True),
         ("bolt", "Зарядка GaN 65 Вт", "CH-65", "749", 22, 2, "Зарядки", True), ("signal", "Навушники TWS Pro", "TW-PRO", "1 290", 0, 3, "Навушники", False),
         ("shopping-bag", "Чохол MagSafe", "CS-MS", "449", 58, 8, "Чохли", True), ("sun", "Лампа настільна LED", "LM-01", "1 048", 9, 2, "Аксесуари", True),
         ("monitor", "Смарт-годинник Fit 3", "SW-F3", "2 398", 12, 4, "Аксесуари", True), ("wifi", "Колонка Go Mini", "SP-GM", "1 599", 17, 3, "Аксесуари", True)]
PC = "38px 2.4fr 70px 76px 1.2fr 50px"


def products():
    cats = [("Усі товари", "86", True), ("Павербанки", "12", False), ("Кабелі", "24", False), ("Зарядки", "15", False), ("Навушники", "9", False), ("Чохли", "18", False), ("Аксесуари", "8", False)]
    cat = "".join(f'<div class="it {"on" if on else ""}" style="height:34px;border-radius:99px;padding:0 12px;display:flex;align-items:center;{"background:var(--acc2);color:var(--acc);font-weight:500" if on else ""}">{n}<em style="margin-left:auto;font-style:normal;font-size:12px;color:var(--faint)">{k}</em></div>' for n, k, on in cats)
    rows = [tr(PC, ["", "Товар", "Артикул", '<span style="display:block;text-align:right">Ціна</span>', "Залишок", "Продаж"], "h")]
    for k, (i, n, sku, p, stock, vars_, c, on) in enumerate(PRODS):
        col = "var(--bad)" if stock == 0 else "var(--warn)" if stock < 10 else "var(--ok)"
        sl = f'<span class="pr"><span class="bar"><i style="width:{min(stock, 60) / 60 * 100}%;--c:{col}"></i></span><span style="width:42px;text-align:right;{"color:var(--bad);" if stock == 0 else ""}">{stock} шт</span></span>'
        rows.append(tr(PC, [f'<span class="im">{ic(i, 17)}</span>', f'<span class="t2"><span style="font-weight:500">{n}</span><small>{c} · {vars_} варіанти</small></span>', f'<span class="n">{sku}</span>',
                            f'<span class="sum" style="display:block">{p} ₴</span>', sl, f'<span class="sw {"on" if on else ""}"></span>'], "sel" if k == 0 else ""))
    var = [("Чорний", "#151515", "10 000", 24, 2), ("Чорний", "#151515", "20 000", 18, 3), ("Білий", "#F4F4F2", "20 000", 3, 1), ("Синій", "#2F5BEA", "20 000", 0, 0)]
    vr = "".join(f'<div style="display:flex;align-items:center;gap:8px;padding:7px 0;border-top:1px solid var(--line);font-size:12.5px"><i style="width:12px;height:12px;border-radius:4px;background:{c};box-shadow:inset 0 0 0 1px rgba(0,0,0,.15)"></i>{n} · {cap}<span style="margin-left:auto" class="{"bd" if s == 0 else "wr" if s < 5 else ""}">{s} шт</span><span class="fa" style="width:70px;text-align:right">резерв {r}</span></div>' for n, c, cap, s, r in var)
    panel = f"""<div class="c" style="width:310px;flex:none;gap:12px"><div style="display:flex;gap:12px;align-items:center"><span class="im l">{ic("zap", 28)}</span><div><b style="font-size:15.5px;line-height:1.3;display:block">Павербанк Volt 20 000 мА·год</b><span class="mu" style="font-size:12.5px">PB-20 · Павербанки</span></div></div>
<div class="tiles" style="grid-template-columns:repeat(3,1fr)"><div><b>1 599 ₴</b><small>Ціна</small></div><div><b>1 020 ₴</b><small>Собівартість</small></div><div><b>36%</b><small>Націнка</small></div></div>
<h3 style="margin-top:2px">Варіанти<small>6</small><span class="r"><span class="lk">Усі{ic("chevron-right", 14)}</span></span></h3><div>{vr}</div>
<div class="kv" style="grid-template-columns:140px 1fr"><span>Продано за 30 днів</span><b>142 шт</b><span>Викуп</span><b>81%</b><span>Допродаж</span><b>Кабель USB-C 1 м</b></div>
<div style="display:flex;gap:6px;margin-top:auto"><span class="bt k" style="flex:1;justify-content:center">{ic("pencil", 14)}Відкрити товар</span><span class="bt">{ic("copy", 14)}</span></div></div>"""
    body = f"""{head("Склад › Товари", "Товари", "<b>86</b> товарів · <b>214</b> варіантів · <b style='color:var(--warn)'>12</b> закінчуються",
                f'<span class="bt">{ic("palette", 15)}Атрибути</span><span class="bt">{ic("file-text", 15)}Імпорт</span>')}
<div class="fls"><span class="in" style="width:320px;height:32px">{ic("search", 15)}<span class="fa">Назва, артикул або штрихкод</span></span><span class="ch">{ic("plus", 13)}Наявність</span><span class="ch">{ic("plus", 13)}Ціна</span><span class="ch">{ic("plus", 13)}Атрибути</span>
<span style="margin-left:auto" class="seg"><span class="on">{ic("list", 14)}Список</span><span>{ic("layout-grid", 14)}Плитка</span></span></div>
<div style="display:flex;gap:12px;flex:1;min-height:0"><div style="width:168px;flex:none;display:flex;flex-direction:column;gap:2px">{cat}</div><div class="tbl" style="flex:1">{"".join(rows)}</div>{panel}</div>"""
    return shell("products", body, fab=False)


# ---------------------------------------------------------------- 7. Склад
def stock():
    rows_d = [("Навушники TWS Pro", "Чорний", "TW-PRO-BLK", 0, 0, 3.1, "закінчились", "bd"), ("Кабель Lightning 2 м", "Білий", "CB-L2-WHT", 4, 1, 2.4, "через 1 день", "bd"),
              ("Павербанк Volt 20 000", "Білий", "PB-20-WHT", 3, 1, 0.9, "через 2 дні", "bd"), ("Лампа настільна LED", "Тепле світло", "LM-01-WRM", 9, 2, 1.1, "через 6 днів", "wr"),
              ("Павербанк Volt 20 000", "Чорний", "PB-20-BLK", 18, 3, 1.7, "через 9 днів", "wr"), ("Смарт-годинник Fit 3", "Графіт", "SW-F3-GRY", 12, 0, 0.8, "через 15 днів", ""),
              ("Колонка Go Mini", "Синій", "SP-GM-BLU", 17, 1, 0.6, "через 27 днів", ""), ("Зарядка GaN 65 Вт", "Білий", "CH-65-WHT", 22, 2, 0.7, "через 29 днів", ""),
              ("Павербанк Volt 10 000", "Чорний", "PB-10-BLK", 24, 2, 0.6, "через 37 днів", ""), ("Чохол MagSafe", "Прозорий", "CS-MS-CLR", 58, 4, 1.2, "через 45 днів", "")]
    SC = "1.7fr 66px 60px 74px 66px 1.25fr 96px"
    rows = [tr(SC, ["Товар · варіант", '<span style="display:block;text-align:right">Залишок</span>', '<span style="display:block;text-align:right">Резерв</span>',
                    '<span style="display:block;text-align:right">Доступно</span>', '<span style="display:block;text-align:right">Шт/день</span>', "Прогноз", ""], "h")]
    for n, v, sku, s, r, d, f, c in rows_d:
        rows.append(tr(SC, [f'<span class="t2"><span style="font-weight:500">{n}</span><small>{v} · {sku}</small></span>', f'<span style="display:block;text-align:right">{s}</span>',
                            f'<span class="fa" style="display:block;text-align:right">{r}</span>', f'<b style="display:block;text-align:right;font-weight:600" class="{"bd" if s - r <= 0 else ""}">{s - r}</b>',
                            f'<span class="mu" style="display:block;text-align:right">{str(d).replace(".", ",")}</span>',
                            f'<span class="{c}" style="display:flex;align-items:center;gap:6px">{ic("circle-alert", 14) if c else ic("check", 14)}{f}</span>',
                            '<span class="bt s" style="float:right">Закупити</span>' if c else ""]))
    moves = [("+50", "Прихід · закупівля №27", "Чохол MagSafe · Прозорий", "15:10", "ok"), ("−1", "Продаж · №1480", "Навушники TWS Pro · Чорний", "14:58", ""),
             ("резерв 1", "Прийнятий · №1482", "Павербанк Volt 20 000 · Чорний", "14:52", "mu"), ("+1", "Повернуто на склад · №1472", "Павербанк Volt 20 000 · Чорний", "13:30", "ok"),
             ("−2", "Продаж · №1479", "Лампа настільна LED", "12:44", ""), ("−1", "Списання · брак", "Кабель Lightning 2 м", "11:05", "bd")]
    mv = "".join(f'<div style="display:flex;gap:10px;padding:9px 0;border-top:1px solid var(--line)"><b style="width:62px;flex:none;font-weight:600" class="{c}">{q}</b><span style="flex:1;line-height:1.3;min-width:0"><span style="display:block">{t}</span><small class="mu" style="font-size:12px">{g}</small></span><span class="fa" style="font-size:12px">{tm}</span></div>' for q, t, g, tm, c in moves)
    body = f"""{head("Склад › Залишки", "Склад", "Основний склад, Тульчин · оновлено щойно",
                f'<span class="bt">{ic("clipboard-list", 15)}Інвентаризація</span><span class="bt">{ic("package-plus", 15)}Прийняти товар</span>')}
<div class="grid" style="grid-template-columns:repeat(4,1fr);flex:none">
<div class="c kpi"><small>{ic("banknote", 15)}Вартість залишку</small><span class="v">312 400 ₴</span><span class="d">за собівартістю · 1 184 шт</span></div>
<div class="c kpi"><small>{ic("lock-open", 15)}У резерві</small><span class="v">23 шт</span><span class="d">31 200 ₴ у прийнятих замовленнях</span></div>
<div class="c kpi" style="background:var(--warn2);border-color:#F6DDBE"><small>{ic("circle-alert", 15)}Закінчуються за тиждень</small><span class="v" style="color:#B45309">12</span><span class="d">варіантів · закупити на ≈ 41 000 ₴</span></div>
<div class="c kpi"><small>{ic("x", 15)}Немає в наявності</small><span class="v">5</span><span class="d">продаж вимкнено автоматично</span></div></div>
<div class="grid" style="grid-template-columns:1fr 300px;flex:1">
<div class="col"><div class="fls"><span class="seg"><span class="on">Усі</span><span>Закінчуються</span><span>Немає</span><span>Неліквід</span></span><span class="in" style="margin-left:auto;width:260px;height:32px">{ic("search", 15)}<span class="fa">Товар або артикул</span></span></div>
<div class="tbl" style="flex:1">{"".join(rows)}</div></div>
<div class="c" style="gap:2px"><h3 style="margin-bottom:8px">Рухи сьогодні<span class="r"><span class="lk">Усі рухи{ic("chevron-right", 14)}</span></span></h3>{mv}</div></div>"""
    return shell("stock", body)


# ---------------------------------------------------------------- 8. Покупці
def customers():
    data = [("Шевченко Тарас", "+380 67 123 45 67", "VIP", 4, "5 840", 75, "сьогодні", ""), ("Коваленко Ірина", "+380 93 552 10 08", "Новий", 1, "649", None, "сьогодні", ""),
            ("Бондаренко Олег", "+380 50 771 23 90", "Повторний", 3, "3 870", 100, "сьогодні", ""), ("Ткаченко Марія", "+380 66 410 77 12", "Повторний", 6, "8 214", 83, "сьогодні", ""),
            ("Олійник Світлана", "+380 68 905 12 44", "Новий", 2, "1 998", 0, "сьогодні", "r"), ("Мельник Денис", "+380 63 118 90 05", "VIP", 9, "21 450", 89, "сьогодні", ""),
            ("Данилюк Ольга", "+380 50 120 33 41", "Новий", 3, "3 870", 0, "сьогодні", "bl"), ("Гнатюк Роман", "+380 67 880 15 72", "Повторний", 2, "3 198", 50, "вчора", ""),
            ("Захарченко Інна", "+380 96 412 70 18", "Повторний", 5, "6 120", 80, "26.10", ""), ("Литвиненко Петро", "+380 99 104 27 55", "Новий", 1, "649", 100, "24.10", "")]
    CC = "34px 2fr 92px 76px 92px 1fr 72px"
    rows = [tr(CC, ["", "Покупець", "Група", '<span style="display:block;text-align:right">Замовлень</span>', '<span style="display:block;text-align:right">Сума</span>', "Викуп", "Останнє"], "h")]
    avc = ["", "g", "o", "p"]
    for k, (n, p, g, o, s, b, last, fl) in enumerate(data):
        tag = {"VIP": "v", "Повторний": "a", "Новий": ""}[g]
        bo = '<span class="fa">ще не було</span>' if b is None else f'<span class="pr"><span class="bar" style="max-width:90px"><i style="width:{b}%;--c:{"var(--bad)" if b < 50 else "var(--warn)" if b < 70 else "var(--ok)"}"></i></span><span style="width:36px">{b}%</span></span>'
        nm = n + (' <span class="tg r">Чорний список</span>' if fl == "bl" else "")
        rows.append(tr(CC, [f'<span class="av {avc[k % 4]}" style="width:30px;height:30px;font-size:11px">{initials(n)}</span>', f'<span class="t2"><span style="font-weight:500">{nm}</span><small>{p}</small></span>',
                            f'<span class="tg {tag}">{g}</span>', f'<span style="display:block;text-align:right">{o}</span>', f'<span class="sum" style="display:block">{s} ₴</span>', bo, f'<span class="mu">{last}</span>'], "sel" if k == 5 else ""))
    hist = [(1476, "Смарт-годинник Fit 3 +1", "wait", "2 398"), (1431, "Павербанк Volt 20 000", "done", "1 599"), (1388, "Колонка Go Mini", "done", "1 599"), (1302, "Навушники TWS Pro", "ref", "1 290")]
    hs = "".join(f'<div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-top:1px solid var(--line);font-size:12.5px"><span class="n" style="font:500 12px \'JB\';color:var(--mut)">{n}</span><span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{g}</span>{st(s)}</div>' for n, g, s, m in hist)
    panel = f"""<div class="c" style="width:360px;flex:none;gap:12px"><div style="display:flex;gap:12px;align-items:center"><span class="av p l">МД</span><div style="flex:1"><b style="font-size:18px;letter-spacing:-.01em">Мельник Денис</b><div class="mu" style="font-size:12.5px">покупець з березня 2025 · Тульчин</div></div><span class="rb" style="width:34px;height:34px">{ic("x", 16)}</span></div>
<div style="display:flex;gap:6px;align-items:center"><span class="bt" style="flex:1">{ic("phone", 15)}+380 63 118 90 05</span><span class="rb" style="width:36px;height:36px">{ic("message-circle", 16)}</span><span class="rb" style="width:36px;height:36px">{ic("send", 16)}</span><span class="rb" style="width:36px;height:36px">{ic("message-square", 16)}</span></div>
<div style="display:flex;gap:5px"><span class="tg v">VIP</span><span class="tg">Instagram</span><span class="tg">Подарунки</span></div>
<div class="tiles"><div><b>9</b><small>Замовлень</small></div><div><b>89%</b><small>Викуп</small></div><div><b>1</b><small>Відмов</small></div><div><b>21 450</b><small>Сума, ₴</small></div></div>
<h3>Замовлення<span class="r"><span class="lk">Усі 9{ic("chevron-right", 14)}</span></span></h3><div style="margin-top:-6px">{hs}</div>
<div class="kv" style="grid-template-columns:110px 1fr"><span>Остання SMS</span><b>ТТН 2045…8365 · 29.10</b><span>Коментар</span><b>Дзвонити після 18:00</b></div>
<div style="display:flex;gap:6px;margin-top:auto"><span class="bt k" style="flex:1;justify-content:center">{ic("plus", 15)}Нове замовлення</span><span class="bt d">{ic("lock-open", 14)}У чорний список</span></div></div>"""
    body = f"""{head("Продажі › Покупці", "Покупці", "<b>3 412</b> покупців · <b>28</b> нових за тиждень · <b>14</b> у чорному списку", f'<span class="bt">{ic("file-text", 15)}Експорт</span>')}
<div class="fls"><span class="in" style="width:300px;height:32px">{ic("search", 15)}<span class="fa">Ім'я, телефон або email</span></span><span class="ch on">Група: VIP і повторні{ic("x", 13)}</span><span class="ch">{ic("plus", 13)}Викуп</span><span class="ch">{ic("plus", 13)}Джерело</span><span class="ch">{ic("plus", 13)}Чорний список</span></div>
<div style="display:flex;gap:12px;flex:1;min-height:0"><div class="tbl" style="flex:1">{"".join(rows)}</div>{panel}</div>"""
    return shell("customers", body, fab=False)


# ---------------------------------------------------------------- 9. Статистика
def stats():
    import math
    cur = [22, 25, 19, 27, 31, 18, 15, 24, 26, 23, 29, 33, 20, 17, 25, 28, 24, 30, 32, 21, 16, 26, 29, 27, 31, 34, 22, 19, 28, 18, 0]
    prev = [20, 21, 18, 23, 26, 17, 14, 22, 23, 21, 25, 27, 19, 15, 22, 24, 23, 26, 28, 19, 15, 23, 25, 24, 27, 29, 20, 17, 24, 22]
    W, H, mx, x0 = 760, 210, 40, 34
    step = (W - x0 - 10) / 31
    bars = "".join(f'<rect x="{x0 + k * step + 3:.1f}" y="{H - 24 - v / mx * (H - 40):.1f}" width="{step - 6:.1f}" height="{v / mx * (H - 40):.1f}" rx="3" fill="{"#2E6BE6" if k != 28 else "#1F4FB8"}"/>' for k, v in enumerate(cur[:30]))
    line = " ".join(f"{x0 + k * step + step / 2:.1f},{H - 24 - v / mx * (H - 40):.1f}" for k, v in enumerate(prev))
    gl = "".join(f'<line x1="{x0}" x2="{W}" y1="{H - 24 - t / mx * (H - 40):.1f}" y2="{H - 24 - t / mx * (H - 40):.1f}" stroke="#F0F0ED"/><text x="{x0 - 8}" y="{H - 20 - t / mx * (H - 40):.1f}" font-size="11" fill="#A3A29D" text-anchor="end">{t}</text>' for t in (0, 10, 20, 30, 40))
    xl = "".join(f'<text x="{x0 + (d - 1) * step + step / 2:.1f}" y="{H - 6}" font-size="11" fill="#A3A29D" text-anchor="middle">{d}</text>' for d in (1, 5, 10, 15, 20, 25, 30))
    tip = f'<g transform="translate({x0 + 28 * step - 150:.1f},14)"><rect width="160" height="44" rx="10" fill="#fff" stroke="#ECECE9"/><text x="12" y="19" font-size="12" font-weight="600" fill="#1F1F1C">29 жовтня · 28 замовлень</text><text x="12" y="35" font-size="11.5" fill="#6F6E69">40 870 ₴ · у вересні 24</text></g>'
    chart = f'<svg viewBox="0 0 {W} {H}" width="100%" height="{H}">{gl}{bars}<polyline points="{line}" fill="none" stroke="#B9B8B3" stroke-width="1.75" stroke-dasharray="4 3"/>{xl}{tip}</svg>'
    srcs = [("Rozetka", 88, 132), ("Prom", 84, 61), ("Instagram", 81, 214), ("Лендинг", 76, 168), ("Facebook", 69, 97), ("TikTok", 63, 70)]
    sb = "".join(f'<div style="display:grid;grid-template-columns:86px 1fr 40px 40px;gap:10px;align-items:center;font-size:12.5px">{src(n)}<span class="bar" style="height:8px"><i style="width:{v}%;--c:{"#2E6BE6" if v >= 75 else "#8FB0EE"}"></i></span><b style="text-align:right;font-weight:600">{v}%</b><span class="fa" style="text-align:right">{k}</span></div>' for n, v, k in srcs)
    MC = "1.4fr 70px 110px 80px 70px 110px"
    mg = [("Олена Литвин", "ОЛ", "", 214, "68%", 402, "81%", "587 300 ₴"), ("Андрій Нечай", "АН", "g", 176, "59%", 291, "76%", "412 700 ₴"), ("Ірина Гуменюк", "ІГ", "o", 61, "52%", 49, "71%", "84 300 ₴")]
    mrows = tr(MC, ["Менеджер", '<span style="display:block;text-align:right">Ліди</span>', '<span style="display:block;text-align:right">У замовлення</span>', '<span style="display:block;text-align:right">Замовлень</span>',
                    '<span style="display:block;text-align:right">Викуп</span>', '<span style="display:block;text-align:right">Виручка</span>'], "h") + "".join(
        tr(MC, [f'<span class="pr"><span class="av {c}" style="width:26px;height:26px;font-size:10.5px">{i}</span>{n}</span>', f'<span style="display:block;text-align:right">{l}</span>',
                f'<span style="display:block;text-align:right">{cv}</span>', f'<span style="display:block;text-align:right">{o}</span>', f'<span style="display:block;text-align:right">{b}</span>',
                f'<span class="sum" style="display:block">{r}</span>']) for n, i, c, l, cv, o, b, r in mg)
    body = f"""{head("Гроші й аналітика › Статистика", "Статистика", "Жовтень 2026 порівняно з вереснем · усі відділи",
                f'<span class="seg"><span>Тиждень</span><span class="on">Місяць</span><span>Квартал</span></span><span class="bt" style="margin-left:6px">{ic("file-text", 15)}Експорт CSV</span>')}
<div class="fls"><span class="ch on">{ic("calendar", 13)}1–29 жовтня{ic("x", 13)}</span><span class="ch">{ic("plus", 13)}Відділ</span><span class="ch">{ic("plus", 13)}Джерело</span><span class="ch">{ic("plus", 13)}Менеджер</span><span class="ch">{ic("plus", 13)}Товар</span></div>
<div class="grid" style="grid-template-columns:repeat(4,1fr);flex:none">
<div class="c kpi"><small>Замовлень</small><span class="v">742</span><span class="d"><b>+12%</b> до вересня</span></div><div class="c kpi"><small>Виручка</small><span class="v">1 084 300 ₴</span><span class="d"><b>+9%</b> до вересня</span></div>
<div class="c kpi"><small>Викуп</small><span class="v">78%</span><span class="d"><b class="n">−2 п.</b> до вересня</span></div><div class="c kpi"><small>Середній чек</small><span class="v">1 461 ₴</span><span class="d"><b class="n">−3%</b> до вересня</span></div></div>
<div class="grid" style="grid-template-columns:1fr 360px;flex:1">
<div class="col"><div class="c" style="flex:none;gap:6px"><h3>Замовлення по днях<small>жовтень — стовпці, вересень — пунктир</small></h3>{chart}</div>
<div class="tbl" style="flex:1">{mrows}</div></div>
<div class="c" style="gap:13px"><h3>Викуп за джерелами<small>% · замовлень</small></h3>{sb}
<div style="height:1px;background:var(--line);margin:4px 0"></div><h3>Причини відмов</h3>
<div class="kv" style="grid-template-columns:1fr auto"><span>Не забрав з пошти</span><b>41</b><span>Передумав до відправки</span><b>23</b><span>Дубль або помилка</span><b>12</b><span>Дорога доставка</span><b>8</b></div></div></div>"""
    return shell("stats", body)


# ---------------------------------------------------------------- 10. Налаштування
def settings():
    W, H = 1180, 780
    secs = [("Загальні", "sliders-horizontal", True), ("Статуси", "list-checks", False), ("Довідники", "layers", False), ("Юрособи", "landmark", False),
            ("Нова Пошта", "truck", False), ("Checkbox", "receipt", False), ("Маркетплейси", "store", False), ("SMS і Viber", "message-square", False),
            ("Telegram", "send", False), ("Документи", "file-text", False), ("Покупці", "users", False), ("Користувачі", "key-round", False)]
    nav = "".join(f'<div class="it {"on" if on else ""}" style="height:34px">{ic(i, 16)}{n}</div>' for n, i, on in secs)
    leads_card = f"""<div class="c" style="border-color:var(--acc3);gap:14px"><div style="display:flex;gap:14px;align-items:flex-start"><span class="rb" style="width:40px;height:40px;background:var(--acc2);border-color:var(--acc3);color:var(--acc)">{ic("inbox", 18)}</span>
<div style="flex:1"><b style="font-size:15px">Розділ «Ліди»</b><div class="mu" style="font-size:13px;margin-top:2px;max-width:600px">Заявки з лендингів і форм спершу потрапляють у «Ліди»: менеджер дзвонить і створює замовлення кнопкою. Вимкніть, якщо замовлення приходять уже готовими — тоді вони одразу йдуть у «Несортовані».</div></div><span class="sw on" style="margin-top:4px"></span></div>
<div class="grid" style="grid-template-columns:1fr 1fr 1fr;padding-left:54px"><div class="fld"><span class="lab">Лід чекає довго після</span><span class="in">5 хв</span></div><div class="fld"><span class="lab">Лід холоне після</span><span class="in">15 хв</span></div>
<div class="fld"><span class="lab">Нагадати після недодзвону через</span><span class="in">30 хв<span class="cv">{ic("chevron-down", 14)}</span></span></div></div>
<div style="padding-left:54px" class="note">{ic("info", 12)}Якщо вимкнути розділ з відкритими лідами, CRM запропонує перенести їх у «Несортовані».</div></div>"""
    comp = f"""<div class="c" style="gap:14px"><b style="font-size:15px">Компанія</b><div class="grid" style="grid-template-columns:1.4fr 1fr 1fr"><div class="fld"><span class="lab">Назва в CRM і SMS</span><span class="in">mdmy</span></div>
<div class="fld"><span class="lab">Часовий пояс</span><span class="in">Київ, UTC+2<span class="cv">{ic("chevron-down", 14)}</span></span></div><div class="fld"><span class="lab">Валюта</span><span class="in">Гривня, ₴<span class="cv">{ic("chevron-down", 14)}</span></span></div></div></div>
<div class="c" style="gap:14px"><b style="font-size:15px">Замовлення</b><div class="grid" style="grid-template-columns:1fr 1fr 1.4fr"><div class="fld"><span class="lab">Наступний номер</span><span class="in">1483</span></div>
<div class="fld"><span class="lab">Резерв товару</span><span class="in">у статусі «Прийнятий»<span class="cv">{ic("chevron-down", 14)}</span></span></div><div class="fld"><span class="lab">Відділ для нових замовлень</span><span class="in">Інтернет-магазин<span class="cv">{ic("chevron-down", 14)}</span></span></div></div>
<div style="display:flex;align-items:center;gap:12px"><span class="sw on"></span><span>Шукати дублі за телефоном за останні 14 днів</span></div><div style="display:flex;align-items:center;gap:12px"><span class="sw"></span><span>Відкривати наступне замовлення після збереження</span></div></div>"""
    win = f"""<div class="win" style="left:{(1440 - W) // 2}px;top:{(900 - H) // 2}px;width:{W}px;height:{H}px;flex-direction:row;background:#fff">
<div style="width:240px;flex:none;background:var(--bg);padding:16px 12px;display:flex;flex-direction:column;gap:2px" class="sb"><b style="font-size:17px;padding:2px 8px 12px">Налаштування</b>
<span class="in" style="height:34px;margin-bottom:8px">{ic("search", 15)}<span class="fa">Знайти налаштування</span></span>{nav}</div>
<div style="flex:1;display:flex;flex-direction:column;min-width:0"><div class="wh" style="padding:22px 26px 8px"><div><h2 style="font-size:22px">Загальні</h2><small>Як працює CRM для всієї команди: розділи, нумерація, дублі.</small></div><div class="r"><span class="rb">{ic("x", 17)}</span></div></div>
<div style="flex:1;padding:10px 26px;display:flex;flex-direction:column;gap:12px;overflow:hidden">{leads_card}{comp}</div>
<div class="wf" style="padding:12px 26px"><span class="note" style="color:var(--warn)">{ic("circle-dot", 12)}Є незбережені зміни</span><span style="margin-left:auto" class="bt">Скасувати</span><span class="bt p">{ic("check", 15)}Зберегти зміни</span></div></div></div>"""
    return _overlay(home(bg=True).replace('class="it on"', 'class="it"').replace('Налаштування</div>', 'Налаштування</div>'), win)


PAGES = [("01-home", "1 · Головна", home), ("02-orders", "2 · Замовлення · вибрано 3", orders), ("03-leads", "3 · Ліди · дошка", leads),
         ("04-ttn", "4 · Вікно створення ТТН", ttn), ("05-invoices", "5 · Видаткові накладні", invoices), ("06-products", "6 · Товари", products),
         ("07-stock", "7 · Склад", stock), ("08-customers", "8 · Покупці", customers), ("09-stats", "9 · Статистика", stats), ("10-settings", "10 · Налаштування · Загальні", settings)]


def build():
    return page("Варіант 14 — 10 сторінок CRM", CSS, [(k, n, f(), None, None) for k, n, f in PAGES], cols=2)
