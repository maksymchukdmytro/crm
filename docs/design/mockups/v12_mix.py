"""Варіант 12 — 5 схем за вибором власника:
підсумок — світло-синій (як у схемі 11-1), шапка — пігулки статусів і дії, як у 10-3, оплата й доставка — формами з іконками, як у 9-4;
у оплаті видно, куди надійшли кошти; «Створити ТТН» — окрема кнопка, решта дій ТТН — у меню «⋯»."""
from common import *
import v11_clean as V

CSS = V.CSS + """
/* шапка як у 10-3: пігулки */
.b10 .hd{height:40px}
.b10 .rb{width:38px;height:38px;border-radius:50%;border:0;background:#fff;color:var(--ink)}
.b10 .trk span{height:34px;padding:0 14px;border-radius:99px;border:0;background:#fff;color:var(--ink);font-size:13px}
.b10 .trk span.dn{background:#E6E6E2;color:var(--mut)}.b10 .trk span.on{background:#1F1F1C;color:#fff;font-weight:500}.b10 .trk i{width:12px;background:#CFCEC9}
.b10 .hd .btn{height:38px;padding:0 15px;border-radius:99px;border:0}
/* форми з іконками як у 9-4 */
.b10 .rw{display:flex;align-items:center;gap:8px;min-height:34px;position:relative}
.b10 .rw>.i:first-child{color:var(--mut);flex:none;width:18px}
.b10 .f{flex:1;min-width:0;height:34px;border:1px solid var(--line);border-radius:8px;display:flex;align-items:center;gap:6px;padding:0 10px;background:#fff;white-space:nowrap;overflow:hidden}
.b10 .f .ch{margin-left:auto;color:var(--faint)}.b10 .f.ph{color:var(--faint)}.b10 .f.ro{background:var(--soft);color:var(--mut)}.b10 .f.sm{flex:none}
.b10 .np{background:#E5262B;color:#fff;border-radius:4px;font-size:10px;font-weight:700;padding:1px 4px}
.b10 .cap{font-size:11.5px;color:var(--mut);padding-left:26px;margin-top:-4px;display:flex;gap:5px;align-items:center}
.b10 .cap .ok{display:inline-flex;gap:4px;align-items:center}
.b10 .btn.ttnb{background:var(--acc2);border-color:var(--acc3);color:var(--acc);height:36px;padding:0 14px;font-weight:600}
.b10 .btn.sq{width:36px;height:36px;padding:0;justify-content:center}
.b10 .menu{position:absolute;z-index:5;right:0;top:40px;background:#fff;border:1px solid var(--line);border-radius:10px;box-shadow:0 16px 30px -12px rgba(0,0,0,.25);padding:4px;width:200px;font-size:12.5px}
.b10 .menu div{display:flex;align-items:center;gap:8px;padding:7px 9px;border-radius:6px}.b10 .menu .i{color:var(--mut)}
.b10 .lab{font-size:11px;color:var(--faint);margin:-2px 0 -6px 26px}
"""


def flag():
    return '<span class="flag"><i></i><i></i></span>'


def header():
    acts = f'<span class="btn">{ic("printer", 15)}Друк{ic("chevron-down", 13)}</span><span class="btn">{ic("receipt", 15)}Чек</span><span class="btn p">{ic("check", 15)}Зберегти</span>'
    return V.header(acts)


def payment():
    return f"""<div class="c"><h4>Оплата<span class="r"><span class="pill">Чек: передоплата ✓</span></span></h4>
<div class="rw">{ic("wallet", 16)}<span class="f">Контроль оплати НП<span class="ch">{ic("chevron-down", 14)}</span></span><span class="btn s" style="height:34px">{ic("receipt", 14)}Чек</span></div>
<div class="lab">Передоплата · куди надійшли кошти</div>
<div class="rw">{ic("hand-coins", 16)}<span class="f sm" style="width:96px">200 ₴</span><span class="f">{ic("landmark", 14)}Monobank · ФОП Максимчук<span class="ch">{ic("chevron-down", 14)}</span></span><span class="ok" style="display:flex">{ic("circle-check-big", 17)}</span></div>
<div class="cap"><span class="ok">{ic("check", 12)}надійшла 29.10, 14:50</span> · підтвердила Олена</div>
<div class="hint">{ic("arrow-up-right", 13)}У ТТН піде: контроль оплати · 1 597 ₴</div></div>"""


def delivery(created=False, menu=False, grow=False, wide=False):
    m = f"""<div class="menu"><div>{ic("tag", 15)}Друк наклейки</div><div>{ic("list-checks", 15)}Додати в реєстр</div><div>{ic("refresh-cw", 15)}Оновити статус</div>
<div>{ic("copy", 15)}Копіювати ТТН</div><div>{ic("pencil", 15)}Змінити / видалити ТТН</div></div>""" if menu else ""
    if created:
        ttn = f'<div class="rw">{ic("scan-barcode", 16)}<span class="f" style="font:500 13.5px \'JB\',monospace">20450913998365</span></div><div class="cap" style="color:var(--warn)">{ic("circle-dot", 12)}Прямує до відділення · очікується 30.10</div>'
        btns = f'<div class="rw" style="padding-left:26px"><span class="btn ttnb" style="flex:1;justify-content:center">{ic("tag", 15)}Друк наклейки</span><span class="btn sq">{ic("ellipsis", 16)}</span>{m}</div>'
    else:
        ttn = f'<div class="rw">{ic("scan-barcode", 16)}<span class="f ph">ТТН з\'явиться після створення</span></div>'
        btns = f'<div class="rw" style="padding-left:26px"><span class="btn ttnb" style="flex:1;justify-content:center">{ic("truck", 15)}Створити ТТН<span style="opacity:.6;font-weight:500;font-size:11.5px">Ctrl ⏎</span></span><span class="btn sq">{ic("ellipsis", 16)}</span>{m}</div>'
    fields = [(f'{ic("truck", 16)}<span class="f"><span class="np">НП</span>Нова Пошта<span class="ch">{ic("chevron-down", 14)}</span></span>'),
              (f'{ic("map-pin", 16)}<span class="f">Київ</span>'),
              (f'{ic("store", 16)}<span class="f">Відділення №12 · Межигірська, 1<span class="ch">{ic("chevron-down", 14)}</span></span>'),
              (f'{ic("banknote", 16)}<span class="f">Платник: отримувач<span class="ch">{ic("chevron-down", 14)}</span></span>'),
              (f'{ic("hand-coins", 16)}<span class="f ro">Післяплата 1 597 ₴ · з оплати</span>')]
    if wide:
        rows = '<div style="display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:8px 12px">' + "".join(f'<div class="rw">{x}</div>' for x in fields) + f'<div>{ttn}</div></div>'
        return f'<div class="c" style="{"flex:1" if grow else ""}"><h4>Доставка</h4>{rows}{btns}</div>'
    rows = "".join(f'<div class="rw">{x}</div>' for x in fields)
    return f'<div class="c" style="{"flex:1" if grow else ""}"><h4>Доставка</h4>{rows}{ttn}{btns}</div>'


def bar():
    return f"""<div class="bar"><span class="bb">{ic("tag", 16)}Наклейка</span><span class="bb">{ic("printer", 16)}Документи{ic("chevron-down", 13)}</span><span class="sep"></span>
<span class="bb">{ic("phone", 16)}Дзвінок</span><span class="bb">{ic("message-square", 16)}SMS</span><span class="bb">{ic("message-circle", 16)}Viber</span><span class="bb">{ic("copy", 16)}Дублювати</span>
<span class="sv">{ic("circle-check-big", 15)}Збережено щойно</span></div>"""


def frame(inner, note):
    return f'<div class="b10"><div class="lbl">{note}</div><div class="win">{inner}</div></div>'


def v1():
    g = f"""<div class="grid" style="grid-template-columns:4fr 3.6fr 4.4fr"><div class="col">{V.customer()}{payment()}</div>
<div class="col">{delivery()}{V.details(grow=True)}</div><div class="col">{V.goods(compact=True)}{V.summary()}</div></div>"""
    return frame(header() + g, "<b>1 · Три колонки.</b> Покупець і оплата → доставка й деталі → товари й підсумок. «Створити ТТН» — окрема кнопка, решта — в «⋯».")


def v2():
    g = f"""<div class="grid" style="grid-template-columns:4.4fr 7.6fr"><div class="col">{V.customer()}{payment()}{V.details(grow=True)}</div>
<div class="col">{V.goods(compact=True)}<div style="display:grid;grid-template-columns:1.25fr 1fr;gap:12px;flex:1;min-height:0">{delivery(wide=False)}<div class="col">{V.summary(grow=True)}</div></div></div></div>"""
    return frame(header() + g, "<b>2 · Дві колонки, доставка під товаром.</b> Зліва покупець, оплата й деталі; справа товари, під ними доставка поруч із підсумком.")


def v3():
    g = f"""<div class="grid" style="grid-template-columns:4fr 8fr"><div class="col">{V.customer()}{payment()}{V.todo(grow=True)}</div>
<div class="col">{V.goods(compact=True)}<div style="display:grid;grid-template-columns:1.7fr 1fr;gap:12px">{delivery(wide=True)}{V.summary()}</div></div></div>"""
    return frame(header() + g, "<b>3 · Доставка широким блоком під товаром.</b> Поля доставки у дві колонки, кнопка «Створити ТТН» на всю ширину. Зліва ще й «Що лишилось».")


def v4():
    g = f"""<div class="grid" style="grid-template-columns:4fr 3.6fr 4.4fr"><div class="col">{V.customer()}{payment()}</div>
<div class="col">{delivery(created=True, menu=True, grow=True)}</div><div class="col">{V.goods(compact=True)}{V.summary()}</div></div>"""
    return frame(header() + g + bar(), "<b>4 · Три колонки + нижня панель.</b> ТТН уже створена: окрема кнопка тепер «Друк наклейки». Дзвінок, SMS, Viber, документи — у панелі знизу.")


def v5():
    g = f"""<div class="grid" style="grid-template-columns:4.4fr 7.6fr"><div class="col">{V.customer()}{payment()}{V.details(grow=True)}</div>
<div class="col">{V.summary()}{V.goods(compact=True, totals=False)}{delivery(wide=True)}</div></div>"""
    return frame(header() + g + bar(), "<b>5 · Підсумок зверху справа + нижня панель.</b> Сума до сплати — перше, що видно справа; під нею товари й доставка.")


def build():
    return page("Варіант 12 — вибрані елементи", CSS, [
        ("1", "1 · Три колонки", v1(), None, None), ("2", "2 · Дві колонки, доставка під товаром", v2(), None, None),
        ("3", "3 · Доставка широким блоком", v3(), None, None), ("4", "4 · Три колонки + нижня панель", v4(), None, None),
        ("5", "5 · Підсумок зверху + нижня панель", v5(), None, None)], cols=1)
