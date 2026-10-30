"""Варіант 13 — обрана схема 3 з правками власника: доставка ліворуч під оплатою (лише перевізник, післяплата, ТТН і кнопка),
місто, відділення й платник вводяться у вікні створення ТТН; праворуч під товарами — деталі й підсумок."""
from common import *
import v11_clean as V
import v12_mix as M

CSS = M.CSS + """
.b10 .dk .todo{margin-top:6px;padding-top:8px;border-top:1px solid var(--acc3);display:flex;align-items:center;gap:6px;font-size:12.5px;color:var(--mut);flex-wrap:wrap}
.b10 .dk .todo b{color:var(--ink);font-weight:500}.b10 .dk .todo a{color:var(--acc);font-weight:500;margin-left:auto;text-decoration:none}
.b10 .note{font-size:11.5px;color:var(--faint);display:flex;gap:5px;align-items:center;padding-left:26px}
"""


def delivery(created=False):
    head = f'<h4>Доставка{"<span class=r><span class=\'pill w\'>● Прямує до відділення</span></span>" if created else ""}</h4>'
    carrier = f'<div class="rw">{ic("truck", 16)}<span class="f"><span class="np">НП</span>Нова Пошта · ФОП Максимчук<span class="ch">{ic("chevron-down", 14)}</span></span></div>'
    cod = f'<div class="rw">{ic("hand-coins", 16)}<span class="f ro">Післяплата 1 597 ₴ · контроль оплати · з оплати</span></div>'
    if created:
        body = f"""{carrier}<div class="rw">{ic("scan-barcode", 16)}<span class="f" style="font:500 13.5px 'JB',monospace">20450913998365</span></div>
<div class="note" style="color:var(--mut)">{ic("map-pin", 12)}Київ, відділення №12 · платник отримувач · 85 ₴ · очікується 30.10</div>{cod}
<div class="rw" style="padding-left:26px"><span class="btn ttnb" style="flex:1;justify-content:center">{ic("tag", 15)}Друк наклейки</span><span class="btn sq">{ic("ellipsis", 16)}</span></div>"""
    else:
        body = f"""{carrier}{cod}<div class="rw">{ic("scan-barcode", 16)}<span class="f ph">ТТН з'явиться після створення</span></div>
<div class="rw" style="padding-left:26px"><span class="btn ttnb" style="flex:1;justify-content:center">{ic("truck", 15)}Створити ТТН<span style="opacity:.6;font-weight:500;font-size:11.5px">Ctrl ⏎</span></span><span class="btn sq">{ic("ellipsis", 16)}</span></div>
<div class="note">{ic("info", 12)}Місто, відділення й платник — у вікні створення ТТН</div>"""
    return f'<div class="c">{head}{body}</div>'


def summary(created=False):
    left = "Наклейка · реєстр · SMS" if created else "ТТН · наклейка · реєстр · SMS"
    return f"""<div class="dk" style="flex:1"><small>До сплати при отриманні</small><div class="big">1 597<u>₴</u></div><div class="ln"></div>
<div class="l"><span>Товари</span><b>1 797 ₴</b></div><div class="l"><span>Передоплата · Monobank</span><b>−200 ₴</b></div><div class="l"><span>Оплата</span><b>Контроль оплати НП</b></div><div class="l"><span>Чек</span><b>Передоплата ✓</b></div>
<div style="flex:1"></div><div class="todo">{ic("list-checks", 14)}Лишилось: <b>{left}</b><a>Показати</a></div></div>"""


def scr(created):
    g = f"""<div class="grid" style="grid-template-columns:4fr 8fr"><div class="col">{V.customer()}{M.payment()}{delivery(created)}</div>
<div class="col">{V.goods(compact=True)}<div style="display:grid;grid-template-columns:1.25fr 1fr;gap:12px">{V.details()}{summary(created)}</div></div></div>"""
    note = ("<b>Обрана схема · до створення ТТН.</b> Доставка під оплатою: лише перевізник, післяплата з оплати і кнопка «Створити ТТН». Праворуч під товарами — деталі й підсумок."
            if not created else "<b>Обрана схема · після створення ТТН.</b> У доставці з'явилися номер, адреса й стан; окрема кнопка тепер «Друк наклейки».")
    return M.frame(M.header() + g, note)


def build():
    return page("Варіант 13 — обрана схема", CSS, [("1-before", "До створення ТТН", scr(False), None, None), ("2-after", "Після створення ТТН", scr(True), None, None)], cols=1)
