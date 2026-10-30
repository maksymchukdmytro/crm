"""Варіант 15 — обрана картка (v13) з компактними товарами: рядок товару в один рівень, варіант — списком-пігулкою."""
from common import *
import v11_clean as V
import v12_mix as M
import v13_final as F

CSS = F.CSS + """
.b10 .btn{border-radius:99px}.b10 .btn.sq{border-radius:50%}.b10 .ph .pp{border-radius:99px}.b10 .ph .rc{border-radius:50%}
.b10 .gr{display:flex;align-items:center;gap:10px;height:46px;border:1px solid var(--line);border-radius:10px;padding:0 10px 0 6px}
.b10 .gr .im{width:34px;height:34px;border-radius:8px;background:var(--soft);display:grid;place-items:center;color:var(--mut);flex:none}
.b10 .gr .t{flex:1;min-width:0;display:flex;align-items:center;gap:8px;white-space:nowrap}
.b10 .gr .t b{font-weight:500;font-size:13.5px;overflow:hidden;text-overflow:ellipsis}
.b10 .gr .vr{height:26px;padding:0 8px 0 9px;border-radius:99px;border:1px solid var(--acc3);background:var(--acc2);color:var(--acc);display:inline-flex;align-items:center;gap:5px;font-size:12px;font-weight:500;flex:none}
.b10 .gr .sk{font-size:12px;color:var(--faint);flex:none}
.b10 .gr .q{height:28px;padding:0 4px;border-radius:99px;border:1px solid var(--line);display:inline-flex;align-items:center;gap:8px;font-weight:500;flex:none}
.b10 .gr .q i{width:20px;height:20px;border-radius:50%;display:grid;place-items:center;color:var(--mut);font-style:normal}
.b10 .gr .s{width:72px;text-align:right;font-weight:600;flex:none}
.b10 .gr .x{color:#C9C8C3;flex:none}
.b10 .gr.up{margin-left:26px;background:var(--soft);border-color:transparent;height:40px}.b10 .gr.up .im{width:28px;height:28px;background:#fff}
.b10 .sw{width:9px;height:9px;border-radius:3px;background:var(--c);box-shadow:inset 0 0 0 1px rgba(0,0,0,.2)}
.b10 .sg{display:flex;align-items:center;gap:10px;border:1px dashed #D6D5D0;border-radius:10px;padding:0 10px;height:42px;font-size:12.5px}
.b10 .sg .k{margin-left:auto;height:28px;padding:0 11px;border-radius:99px;background:var(--acc2);color:var(--acc);display:inline-flex;align-items:center;gap:5px;font-weight:500}
"""


def goods():
    q = f'<span class="q"><i>−</i>1<i>+</i></span>'
    return f"""<div class="c"><h4>Товари<small>2 позиції</small><span class="r"><span class="btn s">{ic("plus", 14)}Товар</span><span class="btn s">{ic("sparkles", 14)}Допродаж</span></span></h4>
<div class="gr"><span class="im">{ic("zap", 18)}</span><span class="t"><b>Павербанк Volt 20 000 мА·год</b><span class="vr"><i class="sw" style="--c:#151515"></i>Чорний{ic("chevron-down", 12)}</span><span class="sk">PB-20-BLK · 18 шт</span></span>{q}<span class="s">1 599 ₴</span><span class="x">{ic("x", 15)}</span></div>
<div class="gr up"><span class="im">{ic("link", 15)}</span><span class="t"><b>Кабель USB-C → USB-C 1 м</b><span class="sk">допродаж · CB-C1-WHT</span></span>{q}<span class="s">198 ₴</span><span class="x">{ic("x", 15)}</span></div>
<div class="in" style="flex:none;height:36px">{ic("search", 15)}<span style="color:var(--faint)">Додати товар: назва, артикул або штрихкод</span></div>
<div class="sg"><span style="color:var(--acc);display:flex">{ic("sparkles", 15)}</span><span>Часто беруть разом: <b style="font-weight:500">Чохол для павербанка · 249 ₴</b></span><span class="k">{ic("plus", 13)}Додати</span></div>
<div class="tl" style="margin-top:2px"><span>Товари</span><b>1 797 ₴</b><span>Знижка</span><b>0 ₴</b><span>Собівартість · прибуток</span><b>1 020 ₴ · 777 ₴</b></div></div>"""


def scr():
    g = f"""<div class="grid" style="grid-template-columns:4fr 8fr"><div class="col">{V.customer()}{M.payment()}{F.delivery(False)}</div>
<div class="col">{goods()}<div style="display:grid;grid-template-columns:1.25fr 1fr;gap:12px;flex:1;min-height:0">{V.details(grow=True)}{F.summary(False)}</div></div></div>"""
    return M.frame(M.header() + g, "<b>Картка замовлення · компактні товари.</b> Рядок товару — 46 px: фото, назва, варіант списком-пігулкою, артикул і залишок, кількість, сума.")


def build():
    return page("Варіант 15 — картка з компактними товарами", CSS, [("card", "Картка замовлення", scr(), None, None)], cols=1)
