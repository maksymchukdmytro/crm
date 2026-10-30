"""Варіант 11 — 5 схем (стиль «Чистого аркуша», підсумок акцентний, без чорного); вікна замовлення в нашому стилі (не LP-CRM): блоки-картки (бенто), шрифт і спокій «Чистого аркуша»,
великий ПІБ і плитки покупця, чорний блок «До сплати», доріжка статусів, трекер доставки, акцентна лише головна кнопка.
Обмеження власника: товар праворуч, оплата під покупцем, доставка може бути під товаром; 2 схеми з нижньою панеллю, 3 без."""
from common import *

CSS = """
.b10{--ink:#1F1F1C;--mut:#6F6E69;--faint:#A3A29D;--line:#ECECE9;--soft:#F7F7F5;--bg:#F7F7F5;--acc:#2E6BE6;--acc2:#EAF1FD;--acc3:#C9DBFA;--ok:#16A34A;--warn:#D97706;
  font:400 13.5px/1.45 'Onest',sans-serif;color:var(--ink);width:100%;height:100%;position:relative;background:#DCDCD8;overflow:hidden}
.b10 .lbl{position:absolute;left:40px;top:14px;z-index:9;background:#fff;color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:7px 12px;font-size:13px}
.b10 .lbl b{font-weight:600}
.b10 .win{position:absolute;left:40px;right:40px;top:58px;bottom:18px;background:var(--bg);border-radius:16px;box-shadow:0 30px 70px -24px rgba(0,0,0,.3);display:flex;flex-direction:column;overflow:hidden;padding:12px;gap:12px}
.b10 .hd{display:flex;align-items:center;gap:8px;flex:none;height:36px}
.b10 .rb{width:34px;height:34px;border-radius:8px;background:#fff;border:1px solid var(--line);display:grid;place-items:center;color:var(--mut);flex:none;position:relative}
.b10 .rb em{position:absolute;top:-5px;right:-5px;font-style:normal;font-size:10px;font-weight:600;background:var(--acc);color:#fff;border-radius:99px;padding:0 5px;line-height:16px}
.b10 .trk{display:flex;align-items:center;gap:6px}.b10 .trk span{height:30px;padding:0 11px;border-radius:7px;background:#fff;border:1px solid var(--line);display:inline-flex;align-items:center;gap:5px;font-size:12.5px;white-space:nowrap;color:var(--mut)}
.b10 .trk span.dn{background:transparent;border-color:transparent;color:var(--faint)}.b10 .trk span.on{background:var(--acc2);border-color:var(--acc3);color:var(--acc);font-weight:500}.b10 .trk i{width:10px;height:1px;background:#D6D5D0}
.b10 .trk span.more{padding:0 8px}
.b10 .hd .r{margin-left:auto;display:flex;align-items:center;gap:6px}
.b10 .btn{height:34px;padding:0 12px;border-radius:8px;background:#fff;border:1px solid var(--line);display:inline-flex;align-items:center;gap:6px;font-weight:500;font-size:13px;white-space:nowrap;color:var(--ink)}
.b10 .btn.p{background:var(--acc);border-color:var(--acc);color:#fff}.b10 .btn.k{border-color:var(--acc3);color:var(--acc);background:#fff}.b10 .btn.s{height:30px;padding:0 10px;font-size:12.5px}
.b10 .grid{flex:1;min-height:0;display:grid;gap:12px}
.b10 .col{display:flex;flex-direction:column;gap:12px;min-height:0;min-width:0}
.b10 .c{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 16px;display:flex;flex-direction:column;gap:10px;min-width:0;overflow:hidden}
.b10 .c h4{font-size:15px;font-weight:600;display:flex;align-items:center;gap:8px}.b10 .c h4 small{font-weight:400;font-size:12.5px;color:var(--faint)}
.b10 .c h4 .r{margin-left:auto;display:flex;gap:6px;font-weight:500}
.b10 .meta{font-size:12.5px;color:var(--faint);display:flex;align-items:center;gap:6px}
.b10 .nm{font-size:23px;font-weight:600;letter-spacing:-.015em;line-height:1.2}
.b10 .ph{display:flex;align-items:center;gap:6px}.b10 .ph .pp{height:34px;padding:0 12px;border-radius:8px;border:1px solid var(--line);display:inline-flex;align-items:center;gap:8px;font-weight:500}
.b10 .ph .rc{width:34px;height:34px;border-radius:8px;border:1px solid var(--line);display:grid;place-items:center;color:var(--mut)}
.b10 .flag{display:inline-flex;flex-direction:column;width:18px;height:13px;border-radius:3px;overflow:hidden}.b10 .flag i{flex:1;background:#2F6BD8}.b10 .flag i+i{background:#F6CF3D}
.b10 .tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.b10 .tiles div{background:var(--soft);border-radius:8px;padding:8px 10px}
.b10 .tiles b{display:block;font-size:17px;font-weight:600}.b10 .tiles small{font-size:11.5px;color:var(--mut)}
.b10 .chips{display:flex;gap:6px;flex-wrap:wrap}.b10 .chips span{height:30px;padding:0 10px;border-radius:7px;border:1px solid var(--line);display:inline-flex;align-items:center;gap:6px;font-size:12.5px;white-space:nowrap}
.b10 .chips span.on{background:var(--acc2);border-color:var(--acc3);color:var(--acc);font-weight:500}
.b10 .fl{display:flex;gap:8px;align-items:center}.b10 .in{height:34px;border-radius:8px;border:1px solid var(--line);background:#fff;display:flex;align-items:center;gap:7px;padding:0 10px;flex:1;min-width:0;white-space:nowrap;overflow:hidden}
.b10 .in .i{color:var(--faint)}.b10 .in .ch{margin-left:auto;color:var(--faint)}.b10 .in.sm{flex:none}
.b10 .hint{font-size:12px;color:var(--acc);display:flex;align-items:center;gap:5px}
.b10 .ok{color:var(--ok)}.b10 .pill{height:22px;padding:0 8px;border-radius:6px;font-size:12px;font-weight:500;display:inline-flex;align-items:center;gap:5px;background:#E9F6EE;color:#15803D}
.b10 .pill.w{background:#FDF1E3;color:#B45309}
.b10 .kv{display:grid;grid-template-columns:96px 1fr;gap:7px 10px;font-size:13px}.b10 .kv span{color:var(--mut)}.b10 .kv b{font-weight:500}
.b10 .gi{display:flex;align-items:center;gap:12px;border:1px solid var(--line);border-radius:10px;padding:9px 12px}
.b10 .gi .im{width:46px;height:46px;border-radius:8px;background:var(--soft);display:grid;place-items:center;color:var(--mut);flex:none}
.b10 .gi .im.lt{width:38px;height:38px}
.b10 .gi .t{flex:1;min-width:0}.b10 .gi .t b{display:block;font-weight:500;font-size:14px}.b10 .gi .t small{font-size:12px;color:var(--mut)}
.b10 .gi .q{height:28px;padding:0 9px;border-radius:7px;border:1px solid var(--line);display:inline-flex;align-items:center;gap:10px;font-weight:500}
.b10 .gi .s{width:80px;text-align:right;font-weight:600;font-size:14px}
.b10 .gi.up{margin-left:30px;background:var(--soft);border-color:transparent}
.b10 .vs{display:flex;gap:4px;margin-top:4px}.b10 .vs span{height:20px;padding:0 6px;border-radius:5px;border:1px solid var(--line);font-size:11px;display:inline-flex;align-items:center;gap:4px}
.b10 .vs span.on{background:var(--acc2);border-color:var(--acc3);color:var(--acc)}.b10 .vs span.no{color:#C4C3BE;text-decoration:line-through}.b10 .sw{width:8px;height:8px;border-radius:2px;background:var(--c);box-shadow:inset 0 0 0 1px rgba(0,0,0,.2)}
.b10 .sug{display:flex;align-items:center;gap:10px;border:1px dashed #D6D5D0;border-radius:10px;padding:9px 12px}
.b10 .sug .ic{width:30px;height:30px;border-radius:8px;background:var(--acc2);color:var(--acc);display:grid;place-items:center;flex:none}.b10 .sug b{font-weight:500;display:block}.b10 .sug small{color:var(--mut);font-size:12px}
.b10 .tl{display:grid;grid-template-columns:1fr auto;gap:4px 12px;font-size:13px;color:var(--mut)}.b10 .tl b{color:var(--ink);font-weight:500;text-align:right}
.b10 .ttn{font:500 19px 'JB',monospace;letter-spacing:.02em}
.b10 .prog{display:grid;grid-template-columns:repeat(4,1fr);gap:5px}.b10 .prog i{height:5px;border-radius:99px;background:#ECEBE7}.b10 .prog i.on{background:var(--acc)}
.b10 .prog span{font-size:11px;color:var(--faint)}
.b10 .dk{background:var(--acc2);border:1px solid var(--acc3);color:var(--ink);border-radius:12px;padding:14px 16px;display:flex;flex-direction:column;gap:6px}
.b10 .dk small{color:var(--mut);font-size:12.5px}.b10 .dk .big{font-size:34px;font-weight:600;letter-spacing:-.02em;line-height:1.05;color:var(--acc)}.b10 .dk .big u{text-decoration:none;font-size:22px;margin-left:4px}
.b10 .dk .l{display:flex;justify-content:space-between;font-size:13px;color:var(--mut)}.b10 .dk .l b{color:var(--ink);font-weight:500}
.b10 .dk .ln{height:1px;background:var(--acc3);margin:4px 0}
.b10 .td{display:flex;align-items:center;gap:9px;font-size:13px}.b10 .td .cb{width:17px;height:17px;border-radius:50%;border:1.5px solid #CFCEC9;display:grid;place-items:center;flex:none}
.b10 .td .cb.on{background:var(--ok);border-color:var(--ok);color:#fff}.b10 .td.dn span{color:var(--faint);text-decoration:line-through}.b10 .td .a{margin-left:auto;color:var(--acc);font-weight:500;font-size:12.5px}
.b10 .bar{flex:none;height:56px;background:#fff;border:1px solid var(--line);border-radius:12px;display:flex;align-items:center;gap:6px;padding:0 10px;box-shadow:0 8px 20px -14px rgba(0,0,0,.25)}
.b10 .bar .bb{height:36px;padding:0 12px;border-radius:8px;border:1px solid var(--line);display:inline-flex;align-items:center;gap:6px;font-size:13px;font-weight:500;white-space:nowrap}
.b10 .bar .sep{width:1px;height:22px;background:var(--line);margin:0 4px}.b10 .bar .sv{margin-left:auto;color:var(--faint);font-size:12.5px;display:flex;align-items:center;gap:6px}
.b10 .bar .bb.p{background:var(--acc);border-color:var(--acc);color:#fff}
.b10 .fab{position:absolute;right:28px;bottom:28px;z-index:6;display:flex;flex-direction:column;align-items:flex-end;gap:8px}
.b10 .fab .m{background:#fff;border:1px solid var(--line);border-radius:12px;padding:5px;display:flex;flex-direction:column;gap:1px;box-shadow:0 18px 34px -14px rgba(0,0,0,.3)}
.b10 .fab .m div{display:flex;align-items:center;gap:10px;padding:8px 11px;border-radius:7px;font-size:13px;white-space:nowrap}.b10 .fab .m div:first-child{background:var(--soft)}.b10 .fab .m .i{color:var(--mut)}
.b10 .fab .m kbd{margin-left:22px;font:500 11px 'Onest';color:var(--faint)}
.b10 .fab .bt{width:52px;height:52px;border-radius:50%;background:var(--acc);color:#fff;display:grid;place-items:center;box-shadow:0 12px 24px -10px rgba(46,107,230,.8)}
.b10 .strip{background:var(--acc2);border:1px solid var(--acc3);border-radius:12px;padding:12px 18px;display:flex;align-items:center;gap:26px;flex:none}
.b10 .strip small{display:block;color:var(--mut);font-size:12px}.b10 .strip .big{font-size:30px;font-weight:600;letter-spacing:-.02em;line-height:1;color:var(--acc)}
.b10 .strip .it b{font-weight:500;font-size:13.5px}.b10 .strip .vl{width:1px;align-self:stretch;background:var(--acc3)}
"""


def flag():
    return '<span class="flag"><i></i><i></i></span>'


def track(more=True):
    return f"""<div class="trk"><span class="dn">{ic("check", 14)}Несортоване</span><i></i><span class="on">{ic("check", 14)}Прийнятий</span><i></i><span>Відправлений</span><i></i><span>Очікує на отримання</span><i></i><span>Завершений</span>{f'<span class="more">{ic("ellipsis", 16)}</span>' if more else ""}</div>"""


def header(actions=""):
    return f"""<div class="hd"><span class="rb">{ic("chevron-left", 18)}</span>{track()}<div class="r">{actions}<span class="rb">{ic("clock-fading", 17)}<em>5</em></span><span class="rb">{ic("x", 18)}</span></div></div>"""


def customer(tiles=True):
    t = """<div class="tiles"><div><b>4</b><small>Замовлень</small></div><div><b>75%</b><small>Викуп</small></div><div><b>1</b><small>Відмов</small></div><div><b>5 840 ₴</b><small>Сума</small></div></div>""" if tiles else ""
    return f"""<div class="c"><div class="meta">Замовлення №1482 · 29.10.2026, 14:32 · Instagram</div>
<div class="nm">Шевченко Тарас<br>Григорович</div>
<div class="ph"><span class="pp">{flag()}+380 67 123 45 67</span><span class="rc">{ic("phone", 16)}</span><span class="rc">{ic("message-circle", 16)}</span><span class="rc">{ic("send", 16)}</span><span class="rc">{ic("message-square", 16)}</span></div>
<div class="meta">{ic("landmark", 14)}ФОП Максимчук О. В. · каса й ключ НП</div>{t}</div>"""


def payment(fiscal=False):
    fb = f'<span class="btn s">{ic("receipt", 14)}Чек</span>' if fiscal else '<span class="pill">Чек: передоплата ✓</span>'
    return f"""<div class="c"><h4>Оплата<span class="r">{fb}</span></h4>
<div class="chips"><span>Накладений</span><span class="on">Контроль оплати НП</span><span>Передоплата</span><span>Повна</span><span>{ic("ellipsis", 14)}</span></div>
<div class="fl"><span class="in sm" style="width:110px">{ic("hand-coins", 15)}200 ₴</span><span class="in">Monobank<span class="ch">{ic("chevron-down", 14)}</span></span><span class="ok" style="display:flex;gap:4px;align-items:center;font-size:12.5px">{ic("circle-check-big", 15)}надійшла</span></div>
<div class="hint">{ic("arrow-up-right", 13)}У ТТН піде: контроль оплати · 1 597 ₴</div></div>"""


def goods(compact=False, totals=True):
    tot = """<div class="tl"><span>Товари</span><b>1 797 ₴</b><span>Знижка</span><b>0 ₴</b><span>Собівартість · прибуток</span><b>1 020 ₴ · 777 ₴</b></div>""" if totals else ""
    sug = "" if compact else f"""<div class="sug"><span class="ic">{ic("sparkles", 16)}</span><span><b>Часто беруть разом</b><small>Чохол для павербанка · 249 ₴</small></span><span class="btn k" style="margin-left:auto;height:34px">{ic("plus", 15)}Додати</span></div>"""
    return f"""<div class="c" style="flex:1"><h4>Товари<span class="r"><span class="btn s">{ic("plus", 14)}Товар</span><span class="btn s">{ic("sparkles", 14)}Допродаж</span></span></h4>
<div class="gi"><span class="im">{ic("zap", 20)}</span><span class="t"><b>Павербанк Volt 20 000 мА·год</b><span class="vs"><span class="on"><i class="sw" style="--c:#151515"></i>Чорний</span><span><i class="sw" style="--c:#F4F4F2"></i>Білий</span><span class="no"><i class="sw" style="--c:#2F5BEA"></i>Синій</span></span><small>PB-20-BLK · 18 шт на складі</small></span><span class="q">− 1 +</span><span class="s">1 599 ₴</span></div>
<div class="gi up"><span class="im lt">{ic("link", 16)}</span><span class="t"><b>Кабель USB-C → USB-C 1 м</b><small>Допродаж · CB-C1-WHT</small></span><span class="q">− 1 +</span><span class="s">198 ₴</span></div>
<div class="in" style="flex:none;background:#fff;border:1.5px solid var(--line)">{ic("search", 15)}<span style="color:var(--faint)">Знайти товар, артикул або штрихкод</span></div>
{sug}<div style="flex:1"></div>{tot}</div>"""


def delivery(ttn_btn=True, grow=False):
    b = f'<span class="btn s">{ic("truck", 14)}ТТН{ic("chevron-down", 13)}</span>' if ttn_btn else ""
    return f"""<div class="c" style="{'flex:1' if grow else ''}"><h4>Доставка<small>· Нова Пошта</small><span class="r"><span class="pill w">● Прямує до відділення</span></span></h4>
<div class="ttn">2045 0913 9983 65</div><div class="meta" style="margin-top:-6px">очікується 30.10, після 13:00</div>
<div class="kv"><span>Куди</span><b>Київ, відділення №12</b><span>Післяплата</span><b>1 597 ₴ · контроль оплати <span style="color:var(--faint);font-weight:400">з оплати</span></b><span>Платник</span><b>Отримувач · 85 ₴</b><span>Ключ НП</span><b>ФОП Максимчук · Тульчин</b></div>
<div><div class="prog"><i class="on"></i><i class="on"></i><i></i><i></i></div><div class="prog" style="margin-top:4px"><span>Створено</span><span>У дорозі</span><span>У відділенні</span><span>Отримано</span></div></div>
<div class="fl">{b}<span class="btn s">{ic("refresh-cw", 14)}Оновити</span><span class="btn s">{ic("copy", 14)}Копіювати</span></div></div>"""


def details(grow=False):
    return f"""<div class="c" style="{'flex:1' if grow else ''}"><h4>Деталі</h4><div class="kv"><span>Менеджер</span><b>Олена Литвин</b><span>Відділ</span><b>Інтернет-магазин</b><span>Джерело</span><b>Instagram</b>
<span>Позначки</span><b><span class="pill" style="background:var(--soft);color:var(--ink)">VIP</span> <span class="pill" style="background:var(--soft);color:var(--ink)">Подарунок</span></b><span>Коментар</span><b>Зателефонувати після 18:00</b></div></div>"""


def summary(grow=False):
    return f"""<div class="dk" style="{'flex:1' if grow else ''}"><small>До сплати при отриманні</small><div class="big">1 597<u>₴</u></div><div class="ln"></div>
<div class="l"><span>Товари</span><b>1 797 ₴</b></div><div class="l"><span>Передоплата · Monobank</span><b>−200 ₴</b></div><div class="l"><span>Оплата</span><b>Контроль оплати НП</b></div><div class="l"><span>Чек</span><b>Передоплата ✓</b></div></div>"""


TODO = [("Товар зарезервовано", True, ""), ("Передоплата надійшла", True, ""), ("Чек на передоплату", True, ""),
        ("Наклейку надруковано", False, "Друкувати"), ("У реєстрі НП", False, "Додати"), ("SMS з ТТН", False, "Надіслати")]


def todo(grow=False):
    it = "".join(f'<div class="td {"dn" if d else ""}"><span class="cb {"on" if d else ""}">{ic("check", 11, 3) if d else ""}</span><span>{t}</span>{f"<span class=a>{a}</span>" if a else ""}</div>' for t, d, a in TODO)
    return f'<div class="c" style="{"flex:1" if grow else ""}"><h4>Що лишилось<small>· 3 з 6</small></h4>{it}</div>'


def bar():
    return f"""<div class="bar"><span class="bb">{ic("printer", 16)}Друк{ic("chevron-down", 13)}</span><span class="bb">{ic("tag", 16)}Наклейка</span><span class="bb">{ic("receipt", 16)}Фіскалізувати</span><span class="sep"></span>
<span class="bb">{ic("phone", 16)}Дзвінок</span><span class="bb">{ic("message-square", 16)}SMS</span><span class="bb">{ic("message-circle", 16)}Viber</span><span class="bb">{ic("copy", 16)}Дублювати</span>
<span class="sv">{ic("circle-check-big", 15)}Збережено щойно</span><span class="bb p">{ic("check", 16)}Зберегти</span></div>"""


def frame(inner, note, extra=""):
    return f'<div class="b10"><div class="lbl">{note}</div><div class="win">{inner}</div>{extra}</div>'


def s1():
    g = f"""<div class="grid" style="grid-template-columns:4fr 3.6fr 4.4fr"><div class="col">{customer()}{payment()}</div>
<div class="col">{delivery()}{details(grow=True)}</div><div class="col">{goods(compact=True)}{summary()}</div></div>"""
    return frame(header() + g + bar(), "<b>1 · Три колонки + нижня панель.</b> Покупець і оплата → доставка й деталі → товари з акцентним підсумком під ними.")


def s2():
    g = f"""<div class="grid" style="grid-template-columns:5fr 7fr"><div class="col">{customer()}{payment()}{details(grow=True)}</div>
<div class="col">{goods(compact=True)}<div style="display:grid;grid-template-columns:1.35fr 1fr;gap:12px">{delivery()}{summary()}</div></div></div>"""
    return frame(header() + g + bar(), "<b>2 · Дві колонки + нижня панель.</b> Зліва покупець, оплата, деталі. Справа товари, під ними доставка поруч з акцентним підсумком.")


def s3():
    acts = f'<span class="btn">{ic("printer", 15)}Друк{ic("chevron-down", 13)}</span><span class="btn">{ic("receipt", 15)}Чек</span><span class="btn p">{ic("check", 15)}Зберегти</span>'
    g = f"""<div class="grid" style="grid-template-columns:4fr 8fr"><div class="col">{customer()}{payment()}{todo(grow=True)}</div>
<div class="col">{goods()}<div style="display:grid;grid-template-columns:1.5fr 1fr;gap:12px">{delivery()}{summary()}</div></div></div>"""
    return frame(header(acts) + g, "<b>3 · Без панелі: дії в шапці.</b> Друк, чек і «Зберегти» — угорі праворуч. Зліва ще й «Що лишилось».")


def s4():
    fab = f"""<div class="fab"><div class="m"><div>{ic("truck", 16)}Створити ТТН<kbd>Ctrl ⏎</kbd></div><div>{ic("printer", 16)}Друк документів</div><div>{ic("tag", 16)}Наклейка</div>
<div>{ic("receipt", 16)}Фіскалізувати</div><div>{ic("message-square", 16)}SMS / Viber</div><div>{ic("copy", 16)}Дублювати</div></div><span class="bt">{ic("plus", 26, 2.2)}</span></div>"""
    g = f"""<div class="grid" style="grid-template-columns:4fr 4.6fr 3.4fr"><div class="col">{customer()}{payment(fiscal=True)}</div>
<div class="col">{goods(compact=True)}{details()}</div><div class="col">{summary()}{delivery(grow=True)}</div></div>"""
    return frame(header() + g, "<b>4 · Без панелі: кнопка «+» зі швидкими діями.</b> Дії — у меню, що розкривається з «+» при наведенні. Чек — біля оплати, ТТН — у доставці.", fab)


def s5():
    strip = f"""<div class="strip"><div><small>До сплати при отриманні</small><div class="big">1 597 ₴</div></div><div class="vl"></div>
<div class="it"><small>Оплата</small><b>Контроль оплати НП · передоплата 200 ₴</b></div><div class="it"><small>Чек</small><b>Передоплата ✓</b></div><div class="vl"></div>
<div style="display:flex;gap:16px">{"".join(f'<div class="td {"dn" if d else ""}"><span class="cb {"on" if d else ""}">{ic("check", 11, 3) if d else ""}</span><span>{t}</span></div>' for t, d, a in TODO[2:5])}</div>
<span class="btn p" style="margin-left:auto">{ic("check", 15)}Зберегти</span></div>"""
    g = f"""<div class="grid" style="grid-template-columns:4fr 8fr"><div class="col">{customer()}{payment()}</div>
<div class="col">{goods(totals=False)}<div style="display:grid;grid-template-columns:1.4fr 1fr;gap:12px">{delivery()}{details()}</div></div></div>"""
    return frame(header(f'<span class="btn">{ic("printer", 15)}Друк{ic("chevron-down", 13)}</span>') + strip + g,
                 "<b>5 · Без панелі: головне смугою зверху.</b> Акцентна смуга під статусами: сума до сплати, оплата, чек і що лишилось. Нижче — покупець і оплата зліва, товари й доставка справа.")


def build():
    return page("Варіант 11 — схеми вікна, чистий стиль", CSS, [
        ("1-bar3", "1 · Три колонки + нижня панель", s1(), None, None), ("2-bar2", "2 · Дві колонки + нижня панель", s2(), None, None),
        ("3-head", "3 · Без панелі: дії в шапці", s3(), None, None), ("4-fab", "4 · Без панелі: «+» зі швидкими діями", s4(), None, None),
        ("5-strip", "5 · Без панелі: головне смугою зверху", s5(), None, None)], cols=1)
