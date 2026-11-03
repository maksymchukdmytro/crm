"""Варіант 9 — 5 схем вікна замовлення в порядку роботи менеджера (за підказками власника й зразком LP-CRM).
Порядок введення: телефон (прапорець = маска, юрособа видно) → ПІБ → оплата → доставка (перевізник, ТТН-меню, чек) → товари справа → коментар → поле 1 (звідки).
Іконки замість підписів, підпис — при наведенні. Інформація — сіра, не акцентна."""
from common import *

CSS = """
.o9{--ink:#1F1F1C;--mut:#6F6E69;--faint:#A3A29D;--line:#E7E6E2;--side:#F7F7F5;--acc:#2E6BE6;--acc2:#EAF1FD;--night:#17171C;--ok:#16A34A;--warn:#D97706;
  font:400 13px/1.4 'Onest',sans-serif;color:var(--ink);width:100%;height:100%;position:relative;background:#D9D9D5;overflow:hidden}
.o9 .bgl{position:absolute;inset:0;padding:22px 40px;display:flex;flex-direction:column;gap:8px;filter:blur(1.2px);opacity:.55}
.o9 .bgl i{display:block;height:34px;border-radius:8px;background:#fff}
.o9 .win{position:absolute;left:40px;right:40px;top:64px;bottom:20px;background:#fff;border-radius:16px;box-shadow:0 30px 70px -20px rgba(0,0,0,.35);display:flex;flex-direction:column;overflow:hidden}
.o9 .wh{height:52px;flex:none;display:flex;align-items:center;gap:10px;padding:0 18px;border-bottom:1px solid var(--line)}
.o9 .wh b{font-weight:600;font-size:16px}.o9 .wh .g{color:var(--faint);font-size:12px}.o9 .wh .r{margin-left:auto;display:flex;gap:6px;align-items:center}
.o9 .ib{width:32px;height:32px;border-radius:8px;display:grid;place-items:center;color:var(--mut);position:relative}.o9 .ib.bd{border:1px solid var(--line)}
.o9 .ib em{position:absolute;top:2px;right:2px;font-style:normal;font-size:9.5px;font-weight:600;background:var(--acc);color:#fff;border-radius:99px;padding:0 4px;line-height:14px}
.o9 .stp{display:inline-flex;align-items:center;gap:6px;height:26px;padding:0 10px;border-radius:7px;font-size:12px;font-weight:500;background:#E7F6EC;color:#15803D}
.o9 .stp i{width:6px;height:6px;border-radius:50%;background:#16A34A}
.o9 .btn{display:inline-flex;align-items:center;gap:6px;height:32px;padding:0 11px;border-radius:8px;border:1px solid var(--line);background:#fff;font-weight:500;font-size:12.5px;white-space:nowrap;color:var(--ink)}
.o9 .btn.p{background:var(--acc);border-color:var(--acc);color:#fff}.o9 .btn.dk{background:#2A2A31;border-color:#2A2A31;color:#fff}
.o9 .wb{flex:1;min-height:0;display:grid;gap:0}
.o9 .col{padding:12px 16px;display:flex;flex-direction:column;gap:7px;min-width:0;overflow:hidden}.o9 .col+.col{border-left:1px solid var(--line)}
.o9 .sec{display:flex;align-items:center;gap:10px;color:var(--faint);font-size:12.5px;margin:4px 0 1px}.o9 .sec:before,.o9 .sec:after{content:"";flex:1;height:1px;background:var(--line)}
.o9 .sec .i{color:var(--faint)}
.o9 .rw{display:flex;align-items:center;gap:7px;min-height:30px;position:relative}
.o9 .rw>.i:first-child,.o9 .rw>.lead{color:var(--mut);flex:none;width:18px}
.o9 .f{flex:1;min-width:0;height:30px;border:1px solid var(--line);border-radius:7px;display:flex;align-items:center;gap:6px;padding:0 9px;background:#fff;white-space:nowrap;overflow:hidden}
.o9 .f.u{border-width:0 0 1px;border-radius:0;padding:0 2px}.o9 .f .i{color:var(--faint)}.o9 .f .ch{margin-left:auto;color:var(--faint)}
.o9 .f.ph{color:var(--faint)}.o9 .f.foc{border-color:var(--acc);box-shadow:0 0 0 3px var(--acc2)}
.o9 .f.sm{flex:none}.o9 .mono{font:500 12.5px 'JB',monospace}
.o9 .flag{display:inline-flex;flex-direction:column;width:20px;height:14px;border-radius:3px;overflow:hidden;flex:none;box-shadow:0 0 0 1px rgba(0,0,0,.08)}.o9 .flag i{flex:1;background:#2F6BD8}.o9 .flag i+i{background:#F6CF3D}
.o9 .mi{width:24px;height:28px;border-radius:7px;display:grid;place-items:center;color:var(--mut);flex:none}.o9 .mi.vb{color:#7360F2}.o9 .mi.tg{color:#2AABEE}
.o9 .hint{font-size:11.5px;color:var(--acc);display:flex;align-items:center;gap:5px;padding-left:26px}
.o9 .hint.g{color:var(--mut)}
.o9 .chips{display:flex;gap:5px;flex-wrap:wrap}.o9 .chips span{height:26px;padding:0 9px;border:1px solid var(--line);border-radius:7px;display:inline-flex;align-items:center;gap:5px;font-size:12px;color:var(--ink)}
.o9 .chips span.on{border-color:var(--acc);background:var(--acc2);color:var(--acc);font-weight:500}
.o9 .ta{border:1px solid var(--line);border-radius:8px;padding:8px 10px;min-height:54px;font-size:12.5px;color:var(--ink)}
.o9 .xf{display:flex;align-items:center;gap:8px;min-height:24px;font-size:12.5px}.o9 .xf sub{font-size:9px;color:var(--faint);margin-left:-6px}.o9 .xf .i{color:var(--faint)}
.o9 .xf a{color:var(--ink);text-decoration:none}.o9 .xf .e{color:var(--faint)}
.o9 .info .rw{min-height:24px;color:var(--faint);font-size:12px}.o9 .info .rw>.i:first-child{color:#C8C7C2}
.o9 .utm{display:flex;gap:4px}.o9 .utm span{font:500 10.5px 'JB',monospace;color:var(--faint);border:1px solid var(--line);border-radius:5px;padding:1px 4px}
.o9 .ttn{display:flex;align-items:center;gap:6px}
.o9 .menu{position:absolute;z-index:5;background:#fff;border:1px solid var(--line);border-radius:10px;box-shadow:0 16px 30px -12px rgba(0,0,0,.25);padding:4px;width:210px;font-size:12.5px}
.o9 .menu div{display:flex;align-items:center;gap:8px;padding:7px 9px;border-radius:6px}.o9 .menu div.on{background:var(--side)}.o9 .menu .i{color:var(--mut)}.o9 .menu kbd{margin-left:auto;font:500 10.5px 'Onest';color:var(--faint)}
.o9 .tip{position:absolute;z-index:6;background:var(--night);color:#fff;font-size:11.5px;padding:4px 8px;border-radius:6px;white-space:nowrap;box-shadow:0 6px 14px -6px rgba(0,0,0,.4)}
.o9 .tip:after{content:"";position:absolute;left:10px;top:-4px;border:4px solid transparent;border-top:0;border-bottom-color:var(--night)}
/* товари */
.o9 .gh{display:grid;align-items:center;gap:8px;color:var(--faint);height:28px;border-bottom:1px solid var(--line)}
.o9 .gr{display:grid;align-items:center;gap:8px;padding:7px 0;border-bottom:1px solid #F1F0EC}
.o9 .gr .ph{width:34px;height:34px;border-radius:8px;background:#1F1F1C;color:#fff;display:grid;place-items:center}.o9 .gr .ph.lt{background:var(--side);color:var(--mut)}
.o9 .gr b{font-weight:500;display:block}.o9 .gr small{font-size:11.5px;color:var(--mut)}.o9 .gr .n{text-align:right;font-variant-numeric:tabular-nums}
.o9 .gr .q{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--line);border-radius:7px;height:26px;padding:0 7px;justify-self:center}
.o9 .gr .x{color:#C8C7C2;justify-self:end}.o9 .gr.up{padding-left:0}.o9 .gr.up .ph{width:28px;height:28px}
.o9 .vs{display:flex;gap:4px;margin-top:3px}.o9 .vs span{height:20px;padding:0 6px;border-radius:5px;border:1px solid var(--line);font-size:11px;display:inline-flex;align-items:center;gap:4px}
.o9 .vs span.on{border-color:var(--acc);background:var(--acc2);color:var(--acc)}.o9 .vs span.no{color:#C8C7C2;text-decoration:line-through}
.o9 .sw{width:8px;height:8px;border-radius:2px;background:var(--c);box-shadow:inset 0 0 0 1px rgba(0,0,0,.15)}
.o9 .add{display:flex;align-items:center;gap:8px;height:34px;border:1px dashed #D6D5D0;border-radius:8px;padding:0 10px;color:var(--faint)}
.o9 .ups{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--mut)}.o9 .ups b{color:var(--ink);font-weight:500}.o9 .ups .a{margin-left:auto;color:var(--acc);font-weight:500}
.o9 .tot{display:grid;grid-template-columns:1fr auto;gap:3px 18px;font-size:12.5px;color:var(--mut);justify-self:end;min-width:230px}.o9 .tot b{color:var(--ink);font-weight:500;text-align:right}
.o9 .dk{background:var(--night);color:#fff;border-radius:12px;padding:12px 14px;display:flex;flex-direction:column;gap:4px}
.o9 .dk small{color:#A1A1AD;font-size:11.5px}.o9 .dk .big{font-size:28px;font-weight:600;letter-spacing:-.02em;line-height:1.1}
.o9 .dk .l{display:flex;justify-content:space-between;font-size:12px;color:#A1A1AD}.o9 .dk .l b{color:#fff;font-weight:500}
/* нижня панель */
.o9 .bar{flex:none;margin:0 12px 12px;height:54px;background:var(--night);border-radius:12px;display:flex;align-items:center;gap:6px;padding:0 10px;color:#fff}
.o9 .bar .bb{display:inline-flex;align-items:center;gap:6px;height:34px;padding:0 11px;border-radius:8px;background:#26262D;font-size:12.5px;font-weight:500;white-space:nowrap}
.o9 .bar .sep{width:1px;height:22px;background:#3A3A42;margin:0 4px}.o9 .bar .sv{margin-left:auto;color:#A1A1AD;font-size:12px;display:flex;align-items:center;gap:5px}
.o9 .bar .bb.p{background:var(--acc)}
.o9 .foot{flex:none;display:flex;align-items:center;gap:8px;padding:10px 16px;border-top:1px solid var(--line)}
.o9 .foot .sv{color:var(--faint);font-size:12px;display:flex;align-items:center;gap:5px}
/* рейка дій праворуч (L5) */
.o9 .rail{width:56px;flex:none;border-left:1px solid var(--line);display:flex;flex-direction:column;align-items:center;gap:6px;padding:12px 0;background:var(--side)}
.o9 .rail .ib{background:#fff;border:1px solid var(--line);width:38px;height:38px}.o9 .rail .ib.p{background:var(--acc);border-color:var(--acc);color:#fff}
.o9 .rail .sp{flex:1}
.o9 .lbl{position:absolute;left:40px;top:14px;z-index:9;background:var(--night);color:#fff;border-radius:10px;padding:8px 12px;font-size:13px;max-width:1100px;box-shadow:0 10px 24px -10px rgba(0,0,0,.5)}
.o9 .lbl b{font-weight:600}
"""


def flag():
    return '<span class="flag"><i></i><i></i></span>'


def sec(title, icon=None):
    return f'<div class="sec">{ic(icon, 14) if icon else ""}{title}</div>'


def tip(text, left, top):
    return f'<span class="tip" style="left:{left}px;top:{top}px">{text}</span>'


def contact(tips=False, compact=False):
    t = tip("Юрособа: каса й ключ НП", 150, -2) if tips else ""
    return f"""{sec("Контакт", "contact")}
<div class="rw">{ic("landmark", 16)}<span class="f u" style="font-size:12px;color:var(--mut)">ФОП Максимчук О. В.<span class="ch">{ic("chevron-down", 14)}</span></span>{t}</div>
<div class="rw"><span class="lead" style="display:flex;align-items:center;gap:2px;width:auto">{flag()}{ic("chevron-down", 12)}</span><span class="f foc">+380 67 123 45 67</span>
<span class="mi" title="Подзвонити">{ic("phone", 16)}</span><span class="mi vb">{ic("message-circle", 16)}</span><span class="mi tg">{ic("send", 16)}</span><span class="mi">{ic("mail", 16)}</span></div>
<div class="rw">{ic("user", 16)}<span class="f">Шевченко Тарас Григорович</span></div>
{"" if compact else f'<div class="hint g">{ic("contact", 12)}4 замовлення · викуп 75% · 5 840 ₴</div>'}
<div class="rw">{ic("at-sign", 16)}<span class="f u ph">email — за потреби</span></div>"""


def payment(tips=False, fiscal=False):
    t = tip("Передоплата", 0, 32) if tips else ""
    fb = f'<span class="btn" style="height:30px">{ic("receipt", 14)}Чек</span>' if fiscal else ""
    return f"""{sec("Оплата", "wallet")}
<div class="rw">{ic("wallet", 16)}<span class="f">Контроль оплати НП<span class="ch">{ic("chevron-down", 14)}</span></span>{fb}</div>
<div class="rw">{ic("hand-coins", 16)}{t}<span class="f sm" style="width:92px">200 ₴</span><span class="f">Monobank<span class="ch">{ic("chevron-down", 14)}</span></span><span class="mi" style="color:var(--ok)">{ic("circle-check-big", 16)}</span></div>
<div class="hint">{ic("arrow-up-right", 12)}У ТТН піде: контроль оплати · 1 597 ₴</div>"""


def status():
    return f'<div class="rw">{ic("circle-dot", 16)}<span class="f u"><span class="stp" style="height:22px"><i></i>Прийнятий</span><span class="ch">{ic("chevron-down", 14)}</span></span></div>'


def comment(h=54):
    return f"""<div class="rw" style="align-items:flex-start">{ic("message-square", 16)}<div class="ta" style="flex:1;min-height:{h}px">Зателефонувати після 18:00, подарункове пакування</div></div>"""


def extra():
    return f"""{sec("Додаткові поля")}
<div class="xf">{ic("pencil", 15)}<sub>1</sub><a>Instagram (stories / powerbank)</a><span style="margin-left:auto;color:var(--faint)">{ic("arrow-up-right", 14)}</span></div>
<div class="xf">{ic("pencil", 15)}<sub>2</sub><span class="e">—</span></div><div class="xf">{ic("pencil", 15)}<sub>3</sub><span class="e">—</span></div>"""


def delivery(menu=False, fiscal=True, wide=False):
    m = ""
    pos = "bottom:36px" if wide else "top:36px"
    if menu:
        m = f"""<div class="menu" style="right:0;{pos}"><div class="on">{ic("truck", 15)}Створити ТТН<kbd>Ctrl ⏎</kbd></div><div>{ic("tag", 15)}Друк наклейки</div>
<div>{ic("list-checks", 15)}Додати в реєстр</div><div>{ic("refresh-cw", 15)}Оновити статус</div><div>{ic("copy", 15)}Копіювати ТТН</div></div>"""
    fb = f'<span class="btn" style="height:30px">{ic("receipt", 14)}Чек{ic("chevron-down", 13)}</span>' if fiscal else ""
    if wide:
        return f"""{sec("Доставка", "truck")}
<div style="display:grid;grid-template-columns:1fr 1fr 1.4fr;gap:8px">
<div class="rw">{ic("truck", 16)}<span class="f"><span style="background:#E5262B;color:#fff;border-radius:4px;font-size:10px;font-weight:700;padding:1px 4px">НП</span>Нова Пошта<span class="ch">{ic("chevron-down", 14)}</span></span></div>
<div class="rw">{ic("map-pin", 16)}<span class="f">Київ</span></div><div class="rw">{ic("store", 16)}<span class="f">№12 · Межигірська, 1</span></div></div>
<div style="display:grid;grid-template-columns:1fr 1fr 1.4fr;gap:8px">
<div class="rw">{ic("banknote", 16)}<span class="f">Отримувач<span class="ch">{ic("chevron-down", 14)}</span></span></div>
<div class="rw">{ic("hand-coins", 16)}<span class="f" style="color:var(--mut)">1 597 ₴ · з оплати</span></div>
<div class="rw" style="position:relative">{ic("scan-barcode", 16)}<span class="f mono">20450913998365</span><span class="btn" style="height:30px">{ic("truck", 14)}ТТН{ic("chevron-down", 13)}</span>{fb}{m}</div></div>"""
    return f"""{sec("Доставка", "truck")}
<div class="rw">{ic("truck", 16)}<span class="f"><span style="background:#E5262B;color:#fff;border-radius:4px;font-size:10px;font-weight:700;padding:1px 4px">НП</span>Нова Пошта<span class="ch">{ic("chevron-down", 14)}</span></span></div>
<div class="rw">{ic("map-pin", 16)}<span class="f">Київ</span></div>
<div class="rw">{ic("store", 16)}<span class="f">Відділення №12 · Межигірська, 1<span class="ch">{ic("chevron-down", 14)}</span></span></div>
<div class="rw">{ic("banknote", 16)}<span class="f">Платник: отримувач<span class="ch">{ic("chevron-down", 14)}</span></span></div>
<div class="rw">{ic("hand-coins", 16)}<span class="f" style="color:var(--mut)">Післяплата 1 597 ₴ · з оплати</span></div>
<div class="rw">{ic("scan-barcode", 16)}<span class="f mono">20450913998365</span></div>
<div class="rw ttn" style="position:relative;justify-content:flex-end;padding-left:26px"><span class="btn" style="height:30px;flex:1;justify-content:center">{ic("truck", 14)}ТТН{ic("chevron-down", 13)}</span>{fb}{m}</div>
<div class="hint g" style="color:var(--warn)">{ic("circle-dot", 12)}Прямує до відділення · очікується 30.10</div>"""


def info():
    return f"""<div class="info">{sec("Інформація", "info")}
<div class="rw">{ic("user-round", 15)}Олена Литвин · менеджер</div><div class="rw">{ic("calendar", 15)}29.10.2026, 14:32</div>
<div class="rw">{ic("globe", 15)}mdmy.me/powerbank</div><div class="rw">{ic("monitor", 15)}91.225.4.226 {ic("lock-open", 13)}</div>
<div class="rw">{ic("link", 15)}<span class="utm"><span>S instagram</span><span>M stories</span><span>C pb-20</span></span></div></div>"""


def info_line():
    return f"""<div class="info" style="display:flex;gap:16px;flex-wrap:wrap;color:var(--faint);font-size:12px;border-top:1px solid var(--line);padding-top:8px">
<span>{ic("user-round", 14)} Олена Литвин</span><span>{ic("calendar", 14)} 29.10, 14:32</span><span>{ic("globe", 14)} mdmy.me/powerbank</span><span>{ic("monitor", 14)} 91.225.4.226</span><span class="utm"><span>S instagram</span><span>M stories</span></span></div>"""


GCOLS = "26px 38px 1fr 60px 84px 86px 84px 16px"


def goods(dark=False, totals=True, tipq=False, title=True):
    hd = "".join(f"<span>{ic(i, 15)}</span>" for i in ["hash", "image", "package"]) + f'<span>{ic("boxes", 15)}</span><span style="text-align:right">{ic("banknote", 15)}</span><span style="text-align:center">{ic("list-ordered", 15)}</span><span style="text-align:right">{ic("wallet", 15)}</span><span></span>'
    t = tip("Залишок на складі", 140, 26) if tipq else ""
    rows = f"""<div class="gr" style="grid-template-columns:{GCOLS}"><span style="color:var(--faint)">1</span><span class="ph">{ic("zap", 17)}</span>
<span><b>Павербанк Volt 20 000 мА·год</b><span class="vs"><span class="on"><i class="sw" style="--c:#151515"></i>Чорний</span><span><i class="sw" style="--c:#F4F4F2"></i>Білий</span><span class="no"><i class="sw" style="--c:#2F5BEA"></i>Синій</span></span></span>
<span style="color:var(--ok);font-size:12px">18 шт</span><span class="n">1 599</span><span class="q">− <b>1</b> +</span><span class="n"><b>1 599</b></span><span class="x">{ic("x", 14)}</span></div>
<div class="gr up" style="grid-template-columns:{GCOLS}"><span></span><span class="ph lt">{ic("link", 14)}</span><span><b>↳ Кабель USB-C → USB-C 1 м</b><small>допродаж · CB-C1-WHT</small></span>
<span style="color:var(--ok);font-size:12px">64 шт</span><span class="n">198</span><span class="q">− <b>1</b> +</span><span class="n"><b>198</b></span><span class="x">{ic("x", 14)}</span></div>"""
    tot = ""
    if totals and not dark:
        tot = f'<div class="tot"><span>Товари, 2 шт</span><b>1 797 ₴</b><span>Знижка</span><b>0 ₴</b><span>Передоплата</span><b>−200 ₴</b><span style="color:var(--ink);font-weight:600">До сплати</span><b style="font-size:17px;font-weight:600">1 597 ₴</b></div>'
    if dark:
        tot = f"""<div class="dk" style="margin-top:auto"><small>До сплати при отриманні</small><span class="big">1 597 ₴</span>
<div class="l"><span>Товари, 2 шт</span><b>1 797 ₴</b></div><div class="l"><span>Передоплата · Monobank</span><b>−200 ₴</b></div><div class="l"><span>Чек Checkbox</span><b>Передоплата ✓</b></div></div>"""
    head = sec("Товар", "package") if title else ""
    return f"""{head}<div style="position:relative"><div class="gh" style="grid-template-columns:{GCOLS}">{hd}</div>{t}</div>{rows}
<div class="add">{ic("search", 15)}Знайти товар, артикул або штрихкод<span style="margin-left:auto">{ic("plus", 15)}</span></div>
<div class="ups">{ic("sparkles", 14)}Часто беруть разом: <b>чохол для павербанка · 249 ₴</b><span class="a">+ Додати</span></div>
<div style="flex:1"></div>{tot}"""


def head(actions=""):
    return f"""<div class="wh"><span class="ib bd">{ic("chevron-left", 16)}</span><b>Замовлення №1482</b><span class="stp"><i></i>Прийнятий{ic("chevron-down", 13)}</span>
<span class="g">29.10.2026, 14:32 · Instagram</span><span class="r">{actions}<span class="ib" title="Історія">{ic("clock-fading", 17)}<em>5</em></span><span class="ib">{ic("x", 18)}</span></span></div>"""


def bar(variant=1):
    left = f"""<span class="bb">{ic("printer", 15)}Друк{ic("chevron-down", 13)}</span><span class="bb">{ic("tag", 15)}Наклейка</span><span class="bb">{ic("receipt", 15)}Фіскалізувати</span><span class="sep"></span>
<span class="bb">{ic("phone", 15)}Дзвінок</span><span class="bb">{ic("message-square", 15)}SMS</span><span class="bb">{ic("message-circle", 15)}Viber</span>"""
    if variant == 2:
        left = f"""<span class="bb">{ic("truck", 15)}ТТН{ic("chevron-down", 13)}</span><span class="bb">{ic("printer", 15)}Друк{ic("chevron-down", 13)}</span><span class="bb">{ic("receipt", 15)}Чек</span><span class="sep"></span>
<span class="bb">{ic("phone", 15)}</span><span class="bb">{ic("message-square", 15)}</span><span class="bb">{ic("message-circle", 15)}</span><span class="bb">{ic("copy", 15)}Дублювати</span>"""
    return f"""<div class="bar">{left}<span class="sv">{ic("circle-check-big", 14)}Збережено щойно</span><span class="bb p">{ic("check", 15)}Зберегти<span style="opacity:.7;font-size:11px">Ctrl S</span></span></div>"""


def frame(inner, note):
    bg = '<div class="bgl">' + "".join("<i></i>" for _ in range(18)) + "</div>"
    return f'<div class="o9">{bg}<div class="win">{inner}</div><div class="lbl">{note}</div></div>'


# ---------------------------------------------------------------- 5 схем
def l1():
    body = f"""{head()}<div class="wb" style="grid-template-columns:340px 300px 1fr">
<div class="col">{contact(tips=True)}{payment()}{status()}{comment()}{extra()}</div>
<div class="col">{delivery(menu=True)}{info()}</div>
<div class="col">{goods(dark=True, tipq=True)}</div></div>{bar(1)}"""
    return frame(body, "<b>1 · Три колонки + нижня панель.</b> Як у LP-CRM: контакт і оплата → доставка → товар справа. Друк, чек і зв'язок — у панелі знизу, ТТН — меню біля номера.")


def l2():
    body = f"""{head()}<div class="wb" style="grid-template-columns:380px 1fr">
<div class="col">{contact()}{payment(tips=True)}{delivery(fiscal=False)}</div>
<div class="col">{goods(totals=True)}<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;border-top:1px solid var(--line);padding-top:6px">
<div style="display:flex;flex-direction:column;gap:6px">{status()}{comment(44)}{extra()}</div>{info()}</div></div></div>{bar(2)}"""
    return frame(body, "<b>2 · Дві колонки + нижня панель.</b> Зліва все, що вводиться (контакт → оплата → доставка), справа товар; під товаром коментар, поле 1 і сіра інформація.")


def l3():
    acts = f'<span class="btn">{ic("printer", 15)}Друк{ic("chevron-down", 13)}</span><span class="btn">{ic("receipt", 15)}Чек</span><span class="btn p">{ic("check", 15)}Зберегти</span>'
    body = f"""{head(acts)}<div class="wb" style="grid-template-columns:360px 1fr">
<div class="col">{contact()}{payment()}{status()}{comment()}{extra()}</div>
<div class="col">{goods(totals=True)}{delivery(wide=True, menu=True)}{info_line()}</div></div>"""
    return frame(body, "<b>3 · Без панелі: доставка під товаром.</b> Товар справа вгорі, доставка широкою смугою під ним. Дії — кнопками в шапці, «Зберегти» — єдина акцентна.")


def l4():
    body = f"""{head(f'<span class="btn">{ic("printer", 15)}Друк{ic("chevron-down", 13)}</span>')}<div class="wb" style="grid-template-columns:330px 300px 1fr">
<div class="col">{contact()}{payment(fiscal=True)}{status()}{comment()}{extra()}</div>
<div class="col">{delivery(fiscal=False, menu=True)}{info()}</div>
<div class="col">{goods(dark=True)}</div></div>
<div class="foot"><span class="sv">{ic("circle-check-big", 14)}Збережено щойно · зміни зберігаються самі</span><span style="margin-left:auto"></span><span class="btn">{ic("copy", 15)}Дублювати</span><span class="btn p">{ic("check", 15)}Зберегти й закрити</span></div>"""
    return frame(body, "<b>4 · Без панелі: дії там, де вони потрібні.</b> Чек — біля оплати, ТТН — біля номера в доставці, друк — у шапці. Внизу лише «Зберегти й закрити».")


def l5():
    rail = f"""<div class="rail"><span class="ib p">{ic("check", 18)}</span><span class="ib">{ic("truck", 18)}</span><span class="ib">{ic("printer", 18)}</span><span class="ib">{ic("receipt", 18)}</span>
<span class="sp"></span><span class="ib">{ic("phone", 18)}</span><span class="ib">{ic("message-square", 18)}</span><span class="ib">{ic("message-circle", 18)}</span><span class="ib">{ic("copy", 18)}</span></div>"""
    t = '<span class="tip" style="right:62px;top:96px">Створити ТТН · Ctrl ⏎</span>'
    body = f"""{head()}<div style="flex:1;min-height:0;display:flex;position:relative"><div class="wb" style="flex:1;grid-template-columns:330px 1fr">
<div class="col">{contact(compact=True)}{payment()}{status()}{sec("Коментар")}{comment(40)}{extra()}</div>
<div class="col">{goods(totals=True)}<div style="display:grid;grid-template-columns:1.15fr 1fr;gap:16px;border-top:1px solid var(--line);padding-top:4px">
<div style="display:flex;flex-direction:column;gap:6px">{delivery(fiscal=False)}</div>{info()}</div></div></div>{rail}{t}</div>"""
    return frame(body, "<b>5 · Без панелі: рейка дій праворуч.</b> Максимум місця: усі дії — значками на вузькій рейці, підпис і клавіша — при наведенні.")


def build():
    return page("Варіант 9 — схеми вікна замовлення", CSS, [
        ("1-bar3", "1 · Три колонки + нижня панель", l1(), None, None), ("2-bar2", "2 · Дві колонки + нижня панель", l2(), None, None),
        ("3-wide", "3 · Без панелі: доставка під товаром", l3(), None, None), ("4-inplace", "4 · Без панелі: дії в блоках", l4(), None, None),
        ("5-rail", "5 · Без панелі: рейка дій праворуч", l5(), None, None)], cols=1)
