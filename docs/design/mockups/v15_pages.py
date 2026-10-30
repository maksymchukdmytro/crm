"""Варіант 15 — правки власника до 10 сторінок: щільні списки (як стрічка Notion), головна під наш функціонал,
ліди списком і компактною дошкою, юрособа в рядку накладної, вікна товару й покупця як у картки замовлення, статистика з усіма полями."""
from common import *
import v14_pages as P
from v14_pages import S, SRC, st, src, cb, shell, tr, _overlay

CSS = P.CSS + """
.tbl>.tr{flex:none}.tr.dn{height:31px;font-size:12.5px;gap:10px;padding:0 12px}.tr.dn .cb{width:15px;height:15px}
.tr.dn.h{height:32px}.tr.g.dn{height:30px}
.tr.dn .st{height:20px;font-size:11.5px;padding:0 8px 0 7px}.tr.dn .src,.tr.dn .pay{font-size:12.5px}
.tr.dn .av{width:20px;height:20px;font-size:9px}
.mono{font:500 12px 'JB',monospace;color:var(--mut)}
.ph.cm{align-items:center}.ph.cm h1{font-size:22px}.ph.cm .sub{margin:0 0 0 12px;align-self:flex-end;padding-bottom:3px}
.pay{display:inline-flex;align-items:center;gap:6px;color:var(--mut)}.pay i{width:8px;height:8px;border-radius:50%;background:var(--c)}
.tm{display:inline-flex;align-items:center;gap:4px;font-weight:500}
.att{display:grid;grid-template-columns:repeat(7,1fr);gap:0;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#fff;flex:none}
.att>div{padding:12px 14px;border-left:1px solid var(--line);display:flex;flex-direction:column;gap:3px}
.att>div:first-child{border-left:0}.att b{font-size:22px;font-weight:600;letter-spacing:-.02em;line-height:1.1}.att small{font-size:12px;color:var(--mut);line-height:1.3}
.att .ic{display:flex;align-items:center;justify-content:space-between;color:var(--mut)}.att .hot b{color:var(--bad)}.att .hot .ic{color:var(--bad)}.att .wrn b{color:#B45309}
.ring{display:flex;align-items:center;gap:12px}.ring svg{flex:none}
.mini{display:flex;flex-direction:column;gap:2px}.mini small{font-size:12px;color:var(--mut)}.mini b{font-size:20px;font-weight:600}
.wd{position:absolute;z-index:9;left:40px;right:40px;top:24px;bottom:24px;background:var(--bg);border-radius:18px;box-shadow:0 40px 80px -30px rgba(0,0,0,.45);display:flex;flex-direction:column;padding:12px;gap:12px;overflow:hidden}
.wd .hd{display:flex;align-items:center;gap:10px;flex:none;height:40px}
.wd .hd .r{margin-left:auto;display:flex;gap:6px;align-items:center}
.wd .hd h2{font-size:19px;font-weight:600;letter-spacing:-.01em}
.f2{display:grid;gap:10px 12px}.f2 .fld{min-width:0}
.ta{border:1px solid var(--line);border-radius:8px;padding:8px 10px;font-size:13px;color:var(--ink);line-height:1.45;background:#fff}
.ph1{width:118px;height:118px;border-radius:12px;background:linear-gradient(145deg,#ECEFF5,#DCE2EC);display:grid;place-items:center;color:#5A6B8A;flex:none}
.th{width:54px;height:54px;border-radius:10px;background:var(--soft);display:grid;place-items:center;color:var(--mut)}
.th.add{border:1px dashed #D6D5D0;background:#fff;color:var(--faint)}
.vt{display:grid;grid-template-columns:1.4fr 88px 70px 56px 40px;gap:8px;align-items:center;height:34px;border-top:1px solid var(--line);font-size:12.5px;white-space:nowrap}
.vt.h{border-top:0;height:26px;color:var(--faint);font-size:11.5px}
.sm{display:flex;align-items:center;gap:8px;font-size:12.5px}
.leg{display:flex;flex-direction:column;gap:2px;width:236px;flex:none}
.leg div{display:grid;grid-template-columns:10px 40px 34px 1fr;gap:8px;align-items:center;height:24px;font-size:12.5px;padding:0 8px;border-radius:99px}
.leg div i{width:9px;height:9px;border-radius:3px;background:var(--c)}.leg div.off{opacity:.4}.leg div.all{background:var(--bg)}
.kst{display:grid;grid-template-columns:repeat(6,1fr);border:1px solid var(--line);border-radius:14px;background:#fff;flex:none}
.kst>div{padding:10px 14px;border-left:1px solid var(--line)}.kst>div:first-child{border-left:0}
.kst small{display:block;font-size:12px;color:var(--mut)}.kst b{font-size:19px;font-weight:600}.kst em{font-style:normal;font-size:11.5px;margin-left:6px}
.kst span{display:block;font-size:11.5px;color:var(--faint)}
.t4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;flex:none}
.t4 .c{padding:12px 16px;gap:6px}.t4 .top{display:flex;align-items:baseline;gap:8px}.t4 .top b{font-size:24px;font-weight:600;letter-spacing:-.02em}
.t4 .rw{display:flex;justify-content:space-between;font-size:12.5px;color:var(--mut)}.t4 .rw b{color:var(--ink);font-weight:500}
.up{color:var(--ok)}.dw{color:var(--bad)}
"""

PAY = {"cod": ("Контроль оплати", "#2E6BE6"), "np": ("Накладений", "#2E6BE6"), "card": ("Передоплата", "#16A34A"), "full": ("Повна оплата", "#16A34A"),
       "roz": ("Rozetka Pay", "#00A046"), "—": ("—", "#D6D5D0")}


def pay(k):
    n, c = PAY[k]
    return f'<span class="pay" style="--c:{c}"><i></i>{n}</span>'


# ------------------------------------------------------------- 1. Головна (під наш функціонал)
def home():
    days = [31, 28, 35, 40, 26, 22, 30, 38, 41, 36, 33, 29, 24, 27, 39, 44, 37, 35, 42, 30, 25, 33, 40, 45, 38, 41, 34, 36, 40]
    sums = [d * 1.45 for d in days]
    W, H, x0 = 720, 176, 40
    mx = 70
    step = (W - x0) / 31
    bars = "".join(f'<rect x="{x0 + k * step + 2.5:.1f}" y="{H - 22 - v / mx * (H - 36):.1f}" width="{step - 5:.1f}" height="{v / mx * (H - 36):.1f}" rx="3" fill="{"#2E6BE6" if k == 28 else "#9DBAF2"}"/>' for k, v in enumerate(sums))
    prev = " ".join(f"{x0 + k * step + step / 2:.1f},{H - 22 - (v * 1.32) / mx * (H - 36):.1f}" for k, v in enumerate([28, 27, 31, 34, 25, 21, 27, 33, 36, 32, 31, 27, 22, 25, 34, 38, 33, 31, 37, 28, 23, 30, 35, 39, 34, 36, 31, 32, 35, 33, 29]))
    gl = "".join(f'<line x1="{x0}" x2="{W}" y1="{H - 22 - t / mx * (H - 36):.1f}" y2="{H - 22 - t / mx * (H - 36):.1f}" stroke="#F0F0ED"/><text x="{x0 - 8}" y="{H - 18 - t / mx * (H - 36):.1f}" font-size="11" fill="#A3A29D" text-anchor="end">{t}к</text>' for t in (0, 20, 40, 60))
    xl = "".join(f'<text x="{x0 + (d - 1) * step + step / 2:.1f}" y="{H - 4}" font-size="11" fill="#A3A29D" text-anchor="middle">{d}</text>' for d in (1, 5, 10, 15, 20, 25, 29))
    chart = f'<svg viewBox="0 0 {W} {H}" width="100%" height="{H}">{gl}{bars}<polyline points="{prev}" fill="none" stroke="#B9B8B3" stroke-width="1.6" stroke-dasharray="4 3"/>{xl}</svg>'

    def ring(v, c="#2E6BE6"):
        r, L = 16, 2 * 3.14159 * 16
        return f'<svg width="42" height="42" viewBox="0 0 42 42"><circle cx="21" cy="21" r="{r}" fill="none" stroke="#EEEEEA" stroke-width="5"/><circle cx="21" cy="21" r="{r}" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round" stroke-dasharray="{L * v / 100:.1f} {L:.1f}" transform="rotate(-90 21 21)"/></svg>'
    qual = "".join(f'<div class="ring">{ring(v, c)}<span class="mini" style="flex-direction:row;align-items:baseline;gap:10px;flex:1"><small style="width:66px;font-size:13px;color:var(--ink)">{n}</small><b>{v}%</b><small class="{dc}" style="margin-left:auto">{d}</small></span></div>' for n, v, c, d, dc in
                   [("Апрув", 72, "#2E6BE6", "+3 п. до вересня", "up"), ("Викуп", 78, "#16A34A", "−2 п. до вересня", "dw"), ("Допродаж", 31, "#7C3AED", "+5 п. до вересня", "up")])
    att = [("inbox", "7", "нових лідів", "hot"), ("package", "14", "чекають відправки", "wrn"), ("map-pin", "22", "чекають на пошті", "wrn"), ("bell", "3", "нагадування зараз", "hot"),
           ("truck", "57", "у дорозі", ""), ("hand-coins", "84 300 ₴", "очікуємо післяплату", ""), ("boxes", "12", "товарів закінчуються", "hot")]
    att_h = '<div class="att">' + "".join(f'<div class="{t}"><span class="ic">{ic(i, 16)}{ic("chevron-right", 14)}</span><b>{n}</b><small>{l}</small></div>' for i, n, l, t in att) + "</div>"
    top = [("Павербанк Volt 20 000", 142, "227 058", 100), ("Чохол MagSafe", 118, "52 982", 83), ("Навушники TWS Pro", 64, "82 560", 45), ("Зарядка GaN 65 Вт", 51, "38 199", 36), ("Кабель USB-C 1 м", 49, "9 702", 34)]
    TC = "1.6fr 1fr 50px 84px"
    top_h = tr(TC, ["Товар", "", '<span style="display:block;text-align:right">Шт</span>', '<span style="display:block;text-align:right">Сума, ₴</span>'], "h dn") + "".join(
        tr(TC, [n, f'<span class="bar"><i style="width:{w}%"></i></span>', f'<span style="display:block;text-align:right">{q}</span>', f'<b style="display:block;text-align:right;font-weight:600">{s}</b>'], "dn") for n, q, s, w in top)
    team = [("Олена Литвин", "ОЛ", "", 14, 9, "78%", "12 940"), ("Андрій Нечай", "АН", "g", 11, 6, "64%", "8 210"), ("Ірина Гуменюк", "ІГ", "o", 5, 3, "60%", "3 166")]
    MC = "1.5fr 56px 70px 60px 84px"
    team_h = tr(MC, ["Менеджер", '<span style="display:block;text-align:right">Лідів</span>', '<span style="display:block;text-align:right">Замовлень</span>', '<span style="display:block;text-align:right">Апрув</span>', '<span style="display:block;text-align:right">Сума, ₴</span>'], "h dn") + "".join(
        tr(MC, [f'<span class="pr"><span class="av {c}">{i}</span>{n}</span>', f'<span style="display:block;text-align:right">{l}</span>', f'<span style="display:block;text-align:right">{o}</span>', f'<span style="display:block;text-align:right">{a}</span>', f'<b style="display:block;text-align:right;font-weight:600">{s}</b>'], "dn") for n, i, c, l, o, a, s in team)
    body = f"""<div class="ph cm"><h1>Головна</h1><span class="sub">Четвер, 29 жовтня · відділ «Інтернет-магазин»</span><div class="r"><span class="seg"><span class="on">Жовтень</span><span>Вересень</span><span>Свій період</span></span></div></div>
<div class="t4">
<div class="c"><small class="mu" style="font-size:12.5px;display:flex;gap:6px;align-items:center">{ic("circle-dot", 14)}Сьогодні</small><div class="top"><b>24 316 ₴</b><small class="up" style="font-weight:500">+11%</small></div><div class="rw"><span>18 замовлень · сер. чек</span><b>1 351 ₴</b></div><div class="rw"><span>Учора</span><b>21 905 ₴</b></div></div>
<div class="c"><small class="mu" style="font-size:12.5px;display:flex;gap:6px;align-items:center">{ic("calendar", 14)}Жовтень</small><div class="top"><b>1 084 300 ₴</b><small class="up" style="font-weight:500">+9%</small></div><div class="rw"><span>742 замовлення · сер. чек</span><b>1 461 ₴</b></div><div class="rw"><span>1–29 вересня</span><b>994 800 ₴</b></div></div>
<div class="c"><small class="mu" style="font-size:12.5px;display:flex;gap:6px;align-items:center">{ic("users", 14)}Покупці</small><div class="top"><b>3 412</b></div><div class="rw"><span>Повторні</span><b>27%</b></div><div class="rw"><span>У чорному списку</span><b>14</b></div></div>
<div class="c"><small class="mu" style="font-size:12.5px;display:flex;gap:6px;align-items:center">{ic("user-round", 14)}Нові покупці</small><div class="top"><b>+128</b><small class="up" style="font-weight:500">+6%</small></div><div class="rw"><span>за жовтень · сьогодні</span><b>+9</b></div><div class="rw"><span>1–29 вересня</span><b>+121</b></div></div></div>
<div><div class="mu" style="font-size:12.5px;margin:0 0 6px 2px">Потребує уваги — клік відкриває відфільтрований список</div>{att_h}</div>
<div class="grid" style="grid-template-columns:1fr 340px;flex:none">
<div class="c" style="gap:4px;padding-bottom:10px"><h3>Продажі за жовтень<small>сума по днях · пунктир — вересень · без скасованих і дублів</small></h3>{chart}</div>
<div class="c" style="gap:10px"><h3>Якість продажів<small>жовтень</small></h3>{qual}<span class="note">{ic("info", 12)}Апрув — підтверджені; викуп — отримані серед отриманих і відмов</span></div></div>
<div class="grid" style="grid-template-columns:1fr 1fr;flex:1">
<div class="c" style="padding:14px 0 0;gap:6px"><h3 style="padding:0 18px">Топ товарів жовтня<span class="r"><span class="lk">Статистика{ic("chevron-right", 14)}</span></span></h3><div>{top_h}</div></div>
<div class="c" style="padding:14px 0 0;gap:6px"><h3 style="padding:0 18px">Команда сьогодні<small>видно адміністратору</small></h3><div>{team_h}</div></div></div>"""
    return shell("home", body)


# ------------------------------------------------------------- 2. Замовлення — щільна стрічка
NAMES = ["Шевченко Тарас", "Коваленко Ірина", "Бондаренко Олег", "Ткаченко Марія", "Кравченко Андрій", "Олійник Світлана", "Мельник Денис", "Шевчук Анна",
         "Поліщук Віктор", "Лисенко Юлія", "Гнатюк Роман", "Данилюк Ольга", "Руденко Максим", "Савченко Ірина", "Мороз Андрій", "Кузьменко Олег",
         "Петренко Алла", "Бойко Віталій", "Захарченко Інна", "Литвиненко Петро", "Онищенко Дарина", "Іваненко Наталія", "Романенко Ігор", "Марченко Ольга"]
GOODS = ["Павербанк Volt 20 000", "Набір кабелів USB-C", "Навушники TWS Pro", "Лампа настільна LED", "Зарядка GaN 65 Вт", "Павербанк Volt 10 000", "Смарт-годинник Fit 3",
         "Чохол MagSafe", "Колонка Go Mini", "Кабель Lightning 2 м"]
STS = ["acc", "uns", "sent", "acc", "done", "pref", "wait", "acc", "sent", "uns", "back", "ref", "sent", "wait", "done", "done", "sent", "acc", "done", "wait", "sent", "done", "done", "sent"]
SRCS = ["Instagram", "Сайт", "Rozetka", "Facebook", "Prom", "Instagram", "TikTok", "Лендинг", "Rozetka", "Сайт", "Facebook", "Лендинг"]
PAYS = ["cod", "—", "roz", "card", "np", "cod", "cod", "full", "roz", "—", "cod", "np"]
DLV = {"acc": ("НП · Київ, №12", "ТТН не створена", "wr"), "uns": ("—", "", ""), "sent": ("НП · Львів, №4", "у дорозі", "fa"), "done": ("НП · Одеса, №31", "отримано", "ok"),
       "pref": ("НП · Дніпро, №7", "повертається", "bd"), "wait": ("НП · Тульчин, №1", "4-й день", "wr"), "back": ("НП · Київ, №201", "на складі", "fa"), "ref": ("—", "", "")}
SUMS = ["1 797", "649", "1 290", "1 048", "749", "999", "2 398", "449", "1 599", "398", "1 599", "1 290", "2 047", "1 048", "749", "2 398", "449", "1 599", "999", "1 290", "649", "1 599", "749", "1 048"]


def orders():
    OC = "22px 42px 1.45fr 122px 1.5fr 150px 122px 1.35fr 88px 24px 40px 66px"
    rows = [tr(OC, [cb(), "№", "Покупець", "Телефон", "Товар", "Статус", "Оплата", "Доставка", "Джерело", "", "Час", '<span style="display:block;text-align:right">Сума</span>'], "h dn"),
            tr(OC, ["", "", "<b>Сьогодні, 29 жовтня</b> · 10 замовлень · 12 316 ₴"], "g dn")]
    for k in range(24):
        if k == 10:
            rows.append(tr(OC, ["", "", "<b>Учора, 28 жовтня</b> · 24 замовлення · 31 870 ₴"], "g dn"))
        s = STS[k]
        d, ds, dc = DLV[s]
        dl = f'{d} <span class="{dc}" style="font-size:12px">· {ds}</span>' if ds else '<span class="fa">не вибрано</span>'
        tg = ' <span class="tg v">VIP</span>' if k == 0 else (' <span class="tg r">Дубль?</span>' if k == 1 else (' <span class="tg r">Чорний список</span>' if k == 11 else ""))
        mg = "" if s == "uns" else f'<span class="av {"g" if k % 2 else ""}">{"АН" if k % 2 else "ОЛ"}</span>'
        tm = f"{14 - k // 2:02d}:{(52 - k * 7) % 60:02d}" if k < 10 else f"{20 - (k - 10) // 2:02d}:{(41 + k * 13) % 60:02d}"
        more = ' <span class="fa">+1</span>' if k in (0, 3, 6, 13) else ""
        rows.append(tr(OC, [cb(k in (0, 3, 7)), f'<span class="mono">{1482 - k}</span>', f'{NAMES[k]}{tg}', f'<span class="mu">+380 {67 + k % 30} {100 + k * 37 % 900} {10 + k * 3 % 90} {20 + k * 7 % 80}</span>',
                            f'{GOODS[k % 10]}{more}', st(s), pay(PAYS[k % 12]), dl, src(SRCS[k % 12]), mg, f'<span class="fa">{tm}</span>', f'<b style="display:block;text-align:right;font-weight:600">{SUMS[k]} ₴</b>'],
                      "dn sel" if k in (0, 3, 7) else ("dn hv" if k == 5 else "dn")))
    bulk = f"""<div class="bulk" style="height:50px"><span class="cnt">{cb(True)}Вибрано 3</span><span class="sep"></span><span class="bt s">Статус{ic("chevron-down", 13)}</span><span class="bt s">Менеджер{ic("chevron-down", 13)}</span>
<span class="bt s">{ic("tag", 14)}Наклейки</span><span class="bt s">{ic("list-checks", 14)}Реєстр НП</span><span class="bt s">{ic("receipt", 14)}Фіскалізувати</span><span class="bt s q">{ic("x", 14)}Зняти</span>
<span class="sep"></span><span class="bt p s" style="height:34px">{ic("truck", 15)}Створити 3 ТТН</span></div>"""
    body = f"""<div class="ph cm"><h1>Замовлення</h1><span class="sub"><b>9</b> несортованих · <b>31</b> чекають відправки · <b>57</b> у дорозі</span>
<div class="r"><span class="seg"><span class="on">{ic("rows-3", 14)}Стрічка</span><span>{ic("square-kanban", 14)}Дошка</span></span><span class="bt s">{ic("rows-3", 14)}Колонки</span><span class="bt s">{ic("file-text", 14)}Експорт</span></div></div>
{P.orders_tabs()}
<div class="fls"><span class="ch on">{ic("calendar", 13)}Сьогодні й учора{ic("x", 13)}</span><span class="ch">{ic("plus", 13)}Менеджер</span><span class="ch">{ic("plus", 13)}Джерело</span><span class="ch">{ic("plus", 13)}Юрособа</span>
<span class="ch">{ic("plus", 13)}Доставка</span><span class="ch">{ic("plus", 13)}Оплата</span><span class="ch">{ic("plus", 13)}Позначки</span><span class="in" style="margin-left:auto;width:230px;height:32px">{ic("search", 15)}<span class="fa">Пошук у списку</span></span></div>
<div class="tbl" style="flex:1">{"".join(rows)}</div>"""
    return shell("orders", body.replace('class="pg', 'class="pg'), fab=False, extra=bulk)


# ------------------------------------------------------------- 3. Ліди — список і компактна дошка
LEADS = [("2047", "Іваненко Наталія", "Павербанк Volt 20 000", "1 599", "lnew", "18 хв", "bd", 1, "Instagram", "", ""), ("2046", "Руденко Максим", "Навушники TWS Pro", "1 290", "lnew", "11 хв", "wr", 1, "Лендинг", "", ""),
         ("2045", "Савченко Ірина", "Лампа настільна LED", "1 048", "lnew", "6 хв", "wr", 1, "TikTok", "", ""), ("2044", "Мороз Андрій", "Зарядка GaN 65 Вт", "749", "lnew", "2 хв", "", 1, "Facebook", "", ""),
         ("2043", "Ковальчук Інна", "Чохол MagSafe", "449", "lnew", "1 хв", "", 1, "Лендинг", "", ""), ("2048", "Демченко Юрій", "Колонка Go Mini", "1 599", "lnew", "щойно", "", 1, "Instagram", "", ""),
         ("2042", "Гуцул Леся", "Павербанк Volt 10 000", "999", "lnew", "1 хв", "", 1, "Сайт", "", ""),
         ("2039", "Кузьменко Олег", "Смарт-годинник Fit 3", "2 398", "lno", "47 хв", "bd", 3, "Instagram", "ОЛ", "SMS надіслано"), ("2041", "Петренко Алла", "Чохол MagSafe", "449", "lno", "32 хв", "wr", 2, "Лендинг", "АН", ""),
         ("2040", "Бойко Віталій", "Колонка Go Mini", "1 599", "lno", "25 хв", "wr", 2, "TikTok", "ОЛ", ""), ("2038", "Ярема Тетяна", "Кабель Lightning 2 м", "249", "lno", "21 хв", "wr", 2, "Facebook", "АН", ""),
         ("2036", "Захарченко Інна", "Павербанк Volt 10 000", "999", "lcb", "о 15:00", "cb", 1, "Facebook", "ОЛ", "Просила після обіду"), ("2033", "Литвиненко Петро", "Набір кабелів USB-C", "649", "lcb", "о 18:00", "cb", 1, "Instagram", "ОЛ", "На роботі"),
         ("2030", "Онищенко Дарина", "Навушники TWS Pro", "1 290", "lcb", "завтра 10:00", "cb", 2, "Лендинг", "АН", "Думає")]


def tmr(t, c):
    if c == "cb":
        return f'<span class="tm" style="color:#6D28D9">{ic("phone", 13)}{t}</span>'
    col = {"bd": "var(--bad)", "wr": "#B45309"}.get(c, "var(--mut)")
    return f'<span class="tm" style="color:{col}">{ic("clock", 13)}{t}</span>'


def leads_list():
    LC = "22px 52px 1.4fr 118px 1.6fr 66px 112px 132px 92px 24px 86px"
    rows = [tr(LC, [cb(), "№", "Ім'я", "Телефон", "Товар з форми", '<span style="display:block;text-align:right">Сума</span>', "Статус", "Чекає · спроба", "Джерело", "", ""], "h dn")]
    for k, (no, nm, g, sm, s, w, wc, a, so, mg, note) in enumerate(LEADS):
        mgh = f'<span class="av {"g" if mg == "АН" else ""}">{mg}</span>' if mg else '<span class="fa">—</span>'
        act = f'<span class="bt s" style="height:26px;padding:0 9px">{ic("phone", 13)}Дзвонити</span>' if k in (0,) else ""
        rows.append(tr(LC, [cb(), f'<span class="mono">Л-{no}</span>', nm, f'<span class="mu">+380 {67 + k} {210 + k * 41 % 700} {11 + k * 7 % 80} {30 + k * 3 % 60}</span>', f'<span class="mu">{g}</span>',
                            f'<b style="display:block;text-align:right;font-weight:600">{sm} ₴</b>', st(s), tmr(w, wc) + (f' <span class="fa">· {a}</span>' if a > 1 else ""), src(so), mgh, act], "dn hv" if k == 0 else "dn"))
    tabs = '<div class="tabs">' + "".join(f'<span class="tab {"on" if n == "Відкриті" else ""}">{n}<em class="{"a" if c.startswith("a") else ""}">{c.lstrip("a")}</em></span>' for n, c in
                                          [("Відкриті", "14"), ("Нові", "a7"), ("Недодзвон", "4"), ("Передзвонити", "3"), ("Дублі", "1"), ("Відмова ліда", "3"), ("Створено замовлення", "12"), ("Усі", "212")]) + "</div>"
    body = f"""<div class="ph cm"><h1>Ліди</h1><span class="sub"><b>7</b> нових чекають дзвінка · найдовше чекає <b style="color:var(--bad)">18 хв</b> · сьогодні створено <b>12</b> замовлень</span>
<div class="r"><span class="seg"><span class="on">{ic("rows-3", 14)}Стрічка</span><span>{ic("square-kanban", 14)}Дошка</span><span>{ic("clock", 14)}Передзвони</span></span><span class="bt p" style="margin-left:4px">{ic("phone", 15)}Почати дзвонити</span></div></div>
{tabs}
<div class="fls"><span class="ch on">{ic("user", 13)}Мої й нічиї{ic("x", 13)}</span><span class="ch">{ic("plus", 13)}Джерело</span><span class="ch">{ic("plus", 13)}Товар</span><span class="ch">{ic("plus", 13)}Менеджер</span><span class="ch">{ic("plus", 13)}Дата</span>
<span class="fa" style="margin-left:auto;font-size:12.5px">Вгорі — хто чекає найдовше</span></div>
<div class="tbl" style="flex:1">{"".join(rows)}</div>"""
    return shell("leads", body)


def leads_board():
    def card(no, nm, g, sm, s, w, wc, a, so, mg, note, on=False):
        return f"""<div class="c" style="padding:9px 11px;gap:4px;{'box-shadow:0 0 0 2px var(--acc3);border-color:var(--acc)' if on else ''}"><div style="display:flex;align-items:center;gap:8px"><b style="font-weight:600;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{nm}</b><b style="font-weight:600;font-size:13px">{sm} ₴</b></div>
<div style="display:flex;align-items:center;gap:8px;font-size:12px"><span class="src" style="--c:{SRC[so]};font-size:12px"><i></i></span><span class="mu" style="flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{g}</span>{tmr(w, wc)}{f'<span class="fa">· {a}</span>' if a > 1 else ''}</div></div>"""
    cols = [("lnew", [x for x in LEADS if x[4] == "lnew"]), ("lno", [x for x in LEADS if x[4] == "lno"]), ("lcb", [x for x in LEADS if x[4] == "lcb"])]
    board = ""
    for code, items in cols:
        cs = "".join(card(*x, on=(x[0] == "2047")) for x in items)
        board += f'<div class="col" style="background:var(--bg);border-radius:14px;padding:8px;gap:6px"><div style="display:flex;align-items:center;gap:8px;padding:2px 4px 2px">{st(code)}<span class="fa">{len(items)}</span><span style="margin-left:auto" class="fa">{ic("plus", 15)}</span></div>{cs}</div>'
    dup = f'<div class="col" style="background:var(--bg);border-radius:14px;padding:8px;gap:6px"><div style="display:flex;align-items:center;gap:8px;padding:2px 4px">{st("uns").replace("Несортований", "Дубль")}<span class="fa">1</span></div>' + \
          card("2035", "Шевченко Тарас", "Павербанк Volt 20 000", "1 599", "", "→ №1482", "", 1, "Instagram", "", "") + "</div>"
    body = f"""<div class="ph cm"><h1>Ліди</h1><span class="sub"><b>7</b> нових чекають дзвінка · найдовше чекає <b style="color:var(--bad)">18 хв</b></span>
<div class="r"><span class="seg"><span>{ic("rows-3", 14)}Стрічка</span><span class="on">{ic("square-kanban", 14)}Дошка</span><span>{ic("clock", 14)}Передзвони</span></span><span class="bt p" style="margin-left:4px">{ic("phone", 15)}Почати дзвонити</span></div></div>
<div class="fls"><span class="ch on">{ic("user", 13)}Мої й нічиї{ic("x", 13)}</span><span class="ch">{ic("plus", 13)}Джерело</span><span class="ch">{ic("plus", 13)}Товар</span><span class="fa" style="margin-left:auto;font-size:12.5px">Картка — 58 px: ім'я, сума, джерело, товар, час очікування</span></div>
<div class="grid" style="grid-template-columns:repeat(4,1fr);flex:1;align-items:start">{board}{dup}</div>"""
    return shell("leads", body)


# ------------------------------------------------------------- 5. Видаткові накладні — юрособа в рядку
def invoices():
    data = [("РН-0168", "29.10", 1480, "Бондаренко Олег", "ФОП Максимчук О. В.", "1 290", True, ""), ("ДМ-0046", "29.10", 1476, "Мельник Денис", "ФОП Максимчук Д. О.", "2 398", False, ""),
            ("РН-0167", "29.10", 1474, "Поліщук Віктор", "ФОП Максимчук О. В.", "1 599", False, ""), ("РН-0166", "28.10", 1466, "Ковальчук Інна", "ФОП Максимчук О. В.", "3 147", True, "chg"),
            ("ДМ-0045", "28.10", 1468, "ТОВ «Техно Плюс»", "ФОП Максимчук Д. О.", "12 450", True, ""), ("РН-0165", "28.10", 1463, "Романенко Ігор", "ФОП Максимчук О. В.", "749", False, ""),
            ("РН-0164", "28.10", 1460, "Сидоренко Лілія", "ФОП Максимчук О. В.", "2 398", False, "ann"), ("РН-0163", "27.10", 1455, "Марченко Ольга", "ФОП Максимчук О. В.", "1 048", True, ""),
            ("ДМ-0044", "27.10", 1452, "Гаврилюк Степан", "ФОП Максимчук Д. О.", "999", False, ""), ("РН-0162", "27.10", 1450, "Ярема Тетяна", "ФОП Максимчук О. В.", "249", False, ""),
            ("РН-0161", "27.10", 1447, "Демченко Юрій", "ФОП Максимчук О. В.", "1 599", False, ""), ("ДМ-0043", "26.10", 1441, "Гуцул Леся", "ФОП Максимчук Д. О.", "999", True, ""),
            ("РН-0160", "26.10", 1438, "Онищенко Дарина", "ФОП Максимчук О. В.", "1 290", False, ""), ("РН-0159", "26.10", 1436, "Захарченко Інна", "ФОП Максимчук О. В.", "999", False, "")]
    ENT = {"ФОП Максимчук О. В.": "#2E6BE6", "ФОП Максимчук Д. О.": "#0E9F6E"}
    IC = "22px 82px 50px 62px 1.3fr 1.2fr 82px 336px"

    def docs(inv, chg):
        r = f'<span class="bt s">{ic("receipt-text", 13)}Рахунок</span>' if inv else f'<span class="bt s off">{ic("receipt-text", 13)}Рахунок</span>'
        pre = f'<span class="bt s k" style="padding:0 8px">{ic("refresh-cw", 13)}</span>' if chg else ""
        return f'<span style="display:flex;gap:4px;justify-content:flex-end">{pre}<span class="bt s">{ic("file-text", 13)}Накладна</span>{r}<span class="bt s">{ic("shield-check", 13)}Гарантія</span></span>'
    rows = [tr(IC, [cb(), "№ накладної", "Дата", "Замовл.", "Покупець", "Юрособа", '<span style="display:block;text-align:right">Сума</span>', '<span style="display:block;text-align:right">Документи</span>'], "h dn")]
    for no, d, o, c, e, s, inv, fl in data:
        num = f'<span class="mono" style="{"text-decoration:line-through;color:var(--faint)" if fl == "ann" else ""}">{no}</span>'
        cust = c + (' <span class="tg">Анульовано</span>' if fl == "ann" else "") + (' <span class="tg" style="background:var(--warn2);color:#B45309">змінилось</span>' if fl == "chg" else "")
        ent = f'<span class="src" style="--c:{ENT[e]};color:var(--ink)"><i></i>{e}</span>'
        rows.append(tr(IC, [cb(), num, f'<span class="mu">{d}</span>', f'<span style="color:var(--acc);font-weight:500">№{o}</span>', cust, ent, f'<b style="display:block;text-align:right;font-weight:600">{s} ₴</b>', docs(inv, fl == "chg")], "dn").replace("height:34px", ""))
    css_fix = '<style>.ivt .tr.dn{height:38px}</style>'
    body = f"""{css_fix}<div class="ph cm"><h1>Видаткові накладні</h1><span class="sub">Жовтень 2026 · <b>214 накладних</b> · <b>312 840 ₴</b></span>
<div class="r"><span class="bt s">{ic("calendar", 14)}Жовтень 2026{ic("chevron-down", 13)}</span><span class="bt s">{ic("file-text", 14)}Експорт реєстру</span></div></div>
<div class="tabs"><span class="tab on">Усі юрособи<em>214</em></span><span class="tab">ФОП Максимчук О. В.<em>168</em></span><span class="tab">ФОП Максимчук Д. О.<em>46</em></span></div>
<div class="fls"><span class="ch">{ic("plus", 13)}Статус замовлення</span><span class="ch">{ic("plus", 13)}Є рахунок-фактура</span><span class="ch">{ic("plus", 13)}Покупець</span>
<span class="in" style="margin-left:auto;width:300px;height:32px">{ic("search", 15)}<span class="fa">№ накладної, замовлення або покупець</span></span></div>
<div class="tbl ivt" style="flex:1">{"".join(rows)}</div>
<div class="note" style="flex:none">{ic("info", 12)}Юрособа — у кожному рядку й кольоровою міткою; вкладки зверху лише звужують список. Неактивний «Рахунок» — рахунок-фактуру не виставляли.</div>"""
    return shell("invoices", body)


# ------------------------------------------------------------- 6. Вікно товару
def _blk(title, inner, extra="", r=""):
    return f'<div class="c" style="{extra}"><h3>{title}<span class="r">{r}</span></h3>{inner}</div>'


def fld(lab, val, cls="", w=""):
    return f'<div class="fld" style="{w}"><span class="lab">{lab}</span><span class="in {cls}">{val}</span></div>'


def product_win():
    main = _blk("Основне", f"""<div style="display:flex;gap:12px"><div class="ph1">{ic("zap", 40, 1.5)}</div><div style="display:grid;grid-template-columns:repeat(2,54px);gap:8px;align-content:start">
<span class="th">{ic("zap", 18)}</span><span class="th">{ic("battery-full", 18)}</span><span class="th">{ic("image", 18)}</span><span class="th add">{ic("plus", 18)}</span></div></div>
<div class="f2" style="grid-template-columns:1fr">{fld("Назва", "Павербанк Volt 20 000 мА·год")}</div>
<div class="f2" style="grid-template-columns:1fr 1fr">{fld("Артикул (SKU)", '<span class="mono" style="color:var(--ink)">PB-20</span>')}{fld("Категорія", f'Павербанки<span class="cv">{ic("chevron-down", 14)}</span>')}
{fld("Виробник", f'Volt<span class="cv">{ic("chevron-down", 14)}</span>')}{fld("Модель", "VL20 PD")}</div>
<div class="fld"><span class="lab">Країни продажу</span><div class="fls"><span class="ch on" style="border-style:solid;height:28px">🇺🇦 Україна{ic("x", 12)}</span><span class="ch" style="height:28px">{ic("plus", 12)}Країна</span></div></div>""".replace("🇺🇦 ", ""), "flex:none")
    desc = _blk("Опис", '<div class="ta" style="min-height:76px">20 000 мА·год, швидка зарядка PD 22,5 Вт, два USB-A і USB-C. У комплекті кабель USB-C 30 см і чохол.</div>', "flex:1")
    prices = _blk("Ціни", f"""<div class="f2" style="grid-template-columns:1fr 1fr">{fld("Ціна продажу, ₴", "<b style='font-weight:600'>1 599</b>")}{fld("Акційна ціна, ₴", '<span class="fa">—</span>')}
{fld("Оптова ціна, ₴", "1 290")}{fld("Собівартість, ₴", "1 020")}</div><div class="sm"><span class="tg g">Маржа 579 ₴ · 36%</span><span class="fa">рахується сама</span></div>""")
    stockb = _blk("Склад", f"""<div class="tiles" style="grid-template-columns:repeat(3,1fr)"><div><b>31</b><small>На складі</small></div><div><b>6</b><small>Резерв</small></div><div><b style="color:var(--ok)">25</b><small>Доступно</small></div></div>
<div class="f2" style="grid-template-columns:1fr auto;align-items:end">{fld("Мінімальний залишок — сповістити", "5 шт")}<span class="bt">{ic("package-plus", 15)}Прийняти / списати</span></div>""", r=f'<span class="lk">Рухи{ic("chevron-right", 14)}</span>')
    ship = _blk("Доставка й гарантія", f"""<div class="f2" style="grid-template-columns:.8fr 1.6fr .8fr">{fld("Вага, кг", "0,45")}{fld("Розміри Д × Ш × В, см", "15 × 8 × 3")}{fld("Гарантія, міс.", "12")}</div>
{fld("Опис відправлення для Нової Пошти", "Павербанк")}""", "flex:1")
    var = [("Чорний", "#151515", "10 000", "PB-10-BLK", "999", 24, True), ("Чорний", "#151515", "20 000", "PB-20-BLK", "1 599", 18, True), ("Білий", "#F4F4F2", "10 000", "PB-10-WHT", "999", 11, True),
           ("Білий", "#F4F4F2", "20 000", "PB-20-WHT", "1 599", 3, True), ("Синій", "#2F5BEA", "20 000", "PB-20-BLU", "1 649", 0, False)]
    vt = '<div class="vt h"><span>Варіант</span><span>Артикул</span><span style="text-align:right">Ціна</span><span style="text-align:right">Залишок</span><span></span></div>' + "".join(
        f'<div class="vt"><span class="sm"><i style="width:11px;height:11px;border-radius:4px;background:{c};box-shadow:inset 0 0 0 1px rgba(0,0,0,.15)"></i>{n} · {cap}</span><span class="mono">{sku}</span><span style="text-align:right">{p}</span><span style="text-align:right" class="{"bd" if s == 0 else "wr" if s < 5 else ""}">{s}</span><span class="sw {"on" if on else ""}" style="transform:scale(.8)"></span></div>'
        for n, c, cap, sku, p, s, on in var)
    attrs = f"""<div class="sm" style="flex-wrap:wrap"><span class="mu" style="width:66px">Колір</span><span class="tg" style="height:24px;padding:0 9px">Чорний</span><span class="tg" style="height:24px;padding:0 9px">Білий</span><span class="tg" style="height:24px;padding:0 9px">Синій</span><span class="tg a" style="height:24px">{ic("plus", 11)}</span></div>
<div class="sm"><span class="mu" style="width:66px">Ємність</span><span class="tg" style="height:24px;padding:0 9px">10 000</span><span class="tg" style="height:24px;padding:0 9px">20 000</span><span class="tg a" style="height:24px">{ic("plus", 11)}</span></div>"""
    variants = _blk("Варіанти<small>5 з 6 можливих</small>", attrs + f"<div>{vt}</div>", "flex:none", r=f'<span class="bt s k">{ic("sparkles", 13)}Скласти варіанти</span>')
    ups = _blk("Допродаж", f"""<div style="display:flex;align-items:center;gap:10px"><span class="sw"></span><span>Цей товар — допродаж до інших</span></div>
<div class="fld"><span class="lab">Пропонувати разом з цим товаром</span><div class="fls" style="flex-wrap:wrap"><span class="ch on" style="border-style:solid;height:28px">Кабель USB-C 1 м{ic("x", 12)}</span><span class="ch on" style="border-style:solid;height:28px">Чохол для павербанка{ic("x", 12)}</span><span class="ch" style="height:28px">{ic("plus", 12)}Товар</span></div></div>""", "flex:none")
    summ = f"""<div class="c kpi ac" style="gap:6px;flex:1"><small>Продано за 30 днів</small><span class="v">142 шт · 227 058 ₴</span>
<div style="height:1px;background:var(--acc3);margin:4px 0"></div><div class="kv" style="grid-template-columns:1fr auto"><span>Маржа</span><b>82 218 ₴</b><span>Викуп</span><b>81%</b><span>З допродажем</span><b>38%</b><span>Продано позицій усього</span><b>1 206</b></div></div>"""
    hd = f"""<div class="hd"><span class="rb">{ic("chevron-left", 18)}</span><h2>Павербанк Volt 20 000 мА·год</h2><span class="tg g" style="height:26px;padding:0 10px;font-size:12px">{ic("circle-check-big", 13)}У продажу</span>
<div class="r"><span class="bt">{ic("copy", 15)}Дублювати</span><span class="bt d">{ic("trash", 15)}Видалити</span><span class="bt p">{ic("check", 15)}Зберегти<kbd>Ctrl S</kbd></span><span class="rb">{ic("clock-fading", 17)}</span><span class="rb">{ic("x", 18)}</span></div></div>"""
    g = f"""<div class="grid" style="grid-template-columns:1fr 1fr 1.15fr;flex:1"><div class="col">{main}{desc}</div><div class="col">{prices}{stockb}{ship}</div><div class="col">{variants}{ups}{summ}</div></div>"""
    return _overlay(P.products().replace('class="tr sel"', 'class="tr"'), f'<div class="wd">{hd}{g}</div>')


# ------------------------------------------------------------- 7. Вікно покупця
def customer_win():
    prof = _blk("Профіль", f"""<div style="display:flex;gap:12px;align-items:center"><span class="av p l">МД</span><div><div style="font-size:21px;font-weight:600;letter-spacing:-.015em">Мельник Денис</div><div class="mu" style="font-size:12.5px">покупець з березня 2025 · перше замовлення з TikTok</div></div></div>
<div style="display:flex;gap:6px;align-items:center"><span class="bt" style="flex:1">{ic("phone", 15)}+380 63 118 90 05</span><span class="rb">{ic("message-circle", 16)}</span><span class="rb">{ic("send", 16)}</span><span class="rb">{ic("message-square", 16)}</span></div>
<div class="f2" style="grid-template-columns:1fr 1fr">{fld("Ім'я", "Мельник Денис")}{fld("Email", "denys.m@gmail.com")}{fld("Група", f'VIP<span class="cv">{ic("chevron-down", 14)}</span>')}{fld("Додатковий телефон", '<span class="fa">—</span>')}</div>
<div class="fld"><span class="lab">Коментар</span><div class="ta">Дзвонити після 18:00. Любить подарункове пакування.</div></div>
<div class="tiles"><div><b>9</b><small>Замовлень</small></div><div><b>89%</b><small>Викуп</small></div><div><b>1</b><small>Відмов</small></div><div><b>21 450</b><small>Сума, ₴</small></div></div>""", "flex:1")
    black = _blk("Чорний список", f"""<div style="display:flex;align-items:center;gap:10px"><span class="sw"></span><span>Не в чорному списку</span></div><span class="note">{ic("info", 12)}Нові замовлення з цього номера отримають позначку й попередження</span>""", "flex:none")
    hist = [(1476, "29.10", "Смарт-годинник Fit 3 +1", "wait", "cod", "НП · Тульчин, №1", "2 398"), (1431, "12.10", "Павербанк Volt 20 000", "done", "card", "НП · Тульчин, №1", "1 599"),
            (1388, "21.09", "Колонка Go Mini", "done", "cod", "НП · Тульчин, №1", "1 599"), (1302, "02.09", "Навушники TWS Pro", "ref", "np", "НП · Вінниця, №3", "1 290"),
            (1255, "18.08", "Чохол MagSafe ×2", "done", "full", "НП · Тульчин, №1", "898"), (1190, "30.07", "Зарядка GaN 65 Вт", "done", "cod", "Укрпошта · Тульчин", "749"),
            (1104, "11.06", "Смарт-годинник Fit 3", "done", "cod", "НП · Тульчин, №1", "2 398"), (1012, "02.05", "Павербанк Volt 10 000 +1", "done", "card", "НП · Тульчин, №1", "1 197")]
    HC = "52px 50px 1.5fr 160px 120px 1.2fr 76px"
    hr = tr(HC, ["№", "Дата", "Товари", "Статус", "Оплата", "Доставка", '<span style="display:block;text-align:right">Сума</span>'], "h dn") + "".join(
        tr(HC, [f'<span class="mono" style="color:var(--acc)">{n}</span>', f'<span class="mu">{d}</span>', g, st(s), pay(p), f'<span class="mu">{dl}</span>', f'<b style="display:block;text-align:right;font-weight:600">{sm} ₴</b>'], "dn") for n, d, g, s, p, dl, sm in hist)
    orders_b = f'<div class="c" style="padding:14px 0 0;gap:6px;flex:none"><h3 style="padding:0 18px">Замовлення<small>9 · клік відкриває замовлення в цьому ж вікні</small><span class="r"><span class="lk">Усі 9{ic("chevron-right", 14)}</span></span></h3><div>{hr}</div></div>'
    comm = [("message-square", "SMS · ТТН 2045…8365", "29.10, 15:21", "доставлено"), ("phone", "Дзвінок · Олена · 2:14", "29.10, 14:40", "підтвердив"), ("message-circle", "Viber · «Дякуємо за замовлення»", "12.10, 11:02", "прочитано"),
            ("phone", "Дзвінок · Андрій · не відповів", "02.09, 10:15", "недодзвон")]
    cm = "".join(f'<div style="display:flex;gap:10px;align-items:center;padding:8px 0;border-top:1px solid var(--line);font-size:12.5px"><span class="mu" style="display:flex">{ic(i, 15)}</span><span style="flex:1">{t}</span><span class="fa">{w}</span><span class="tg">{r}</span></div>' for i, t, w, r in comm)
    comm_b = _blk("Комунікації", f"<div>{cm}</div>", "flex:1;gap:4px")
    addr = _blk("Адреси доставки", f"""<div class="kv" style="grid-template-columns:1fr auto"><span style="color:var(--ink)">НП · Тульчин, відділення №1</span><b>6 разів</b><span style="color:var(--ink)">НП · Вінниця, відділення №3</span><b>1 раз</b><span style="color:var(--ink)">Укрпошта · Тульчин, 23600</span><b>1 раз</b></div>
<div class="sm" style="flex-wrap:wrap"><span class="mu">Позначки</span><span class="tg v">VIP</span><span class="tg">Подарунки</span><span class="tg a">{ic("plus", 11)}</span></div>
<div class="sm"><span class="mu">Джерела</span>{src("TikTok")}{src("Instagram")}</div>""", "flex:1")
    hd = f"""<div class="hd"><span class="rb">{ic("chevron-left", 18)}</span><h2>Покупець</h2><span class="tg v" style="height:26px;padding:0 10px;font-size:12px">VIP</span>
<div class="r"><span class="bt k">{ic("plus", 15)}Нове замовлення</span><span class="bt d">{ic("lock-open", 15)}У чорний список</span><span class="bt p">{ic("check", 15)}Зберегти</span><span class="rb">{ic("clock-fading", 17)}</span><span class="rb">{ic("x", 18)}</span></div></div>"""
    g = f"""<div class="grid" style="grid-template-columns:4fr 8fr;flex:1"><div class="col">{prof}{black}</div><div class="col">{orders_b}<div class="grid" style="grid-template-columns:1fr 1fr;flex:1">{comm_b}{addr}</div></div></div>"""
    return _overlay(P.customers().replace('class="tr sel"', 'class="tr"'), f'<div class="wd">{hd}{g}</div>')


# ------------------------------------------------------------- 9. Статистика — усі наші поля компактно
def stats():
    stat_cols = [("acc", "#2E6BE6"), ("sent", "#6D5BD0"), ("wait", "#D97706"), ("done", "#16A34A"), ("pref", "#E11D48"), ("ref", "#DC2626")]
    import random
    random.seed(4)
    W, H, x0 = 700, 196, 32
    days = 29
    step = (W - x0) / days
    mx = 40
    bars, tot = "", []
    for d in range(days):
        y = H - 20
        t = 0
        for (code, c), share in zip(stat_cols, (0.08, 0.14, 0.09, 0.55, 0.06, 0.08)):
            v = max(0, (22 + random.randint(-6, 9)) * share)
            h = v / mx * (H - 34)
            y -= h
            t += v
            bars += f'<rect x="{x0 + d * step + 3:.1f}" y="{y:.1f}" width="{step - 6:.1f}" height="{h:.1f}" fill="{c}"/>'
        tot.append(t)
    line = " ".join(f"{x0 + d * step + step / 2:.1f},{H - 20 - (t + 2) / mx * (H - 34):.1f}" for d, t in enumerate(tot))
    gl = "".join(f'<line x1="{x0}" x2="{W}" y1="{H - 20 - t / mx * (H - 34):.1f}" y2="{H - 20 - t / mx * (H - 34):.1f}" stroke="#F0F0ED"/><text x="{x0 - 6}" y="{H - 16 - t / mx * (H - 34):.1f}" font-size="11" fill="#A3A29D" text-anchor="end">{t}</text>' for t in (0, 10, 20, 30))
    xl = "".join(f'<text x="{x0 + (d - 1) * step + step / 2:.1f}" y="{H - 4}" font-size="11" fill="#A3A29D" text-anchor="middle">{d}</text>' for d in (1, 5, 10, 15, 20, 25, 29))
    chart = f'<svg viewBox="0 0 {W} {H}" width="100%" height="{H}">{gl}{bars}<polyline points="{line}" fill="none" stroke="#1F1F1C" stroke-width="1.5"/>{xl}</svg>'
    legend = [("Усі", "#1F1F1C", "100%", "742", "all"), ("Несортований", "#7C7B76", "1%", "9", "off"), ("Прийнятий", "#2E6BE6", "4%", "31", ""), ("Відправлений", "#6D5BD0", "8%", "57", ""),
              ("Очікує на отримання", "#D97706", "3%", "22", ""), ("Завершений", "#16A34A", "61%", "455", ""), ("Відмова на пошті", "#E11D48", "6%", "45", ""),
              ("Повернуто на склад", "#64748B", "3%", "23", "off"), ("Відмова", "#DC2626", "13%", "100", "")]
    lg = '<div class="leg">' + "".join(f'<div class="{cl}" style="--c:{c}"><i></i><b style="font-weight:600">{p}</b><span class="fa">{n}</span><span style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{nm}</span></div>' for nm, c, p, n, cl in legend) + "</div>"
    tiles = [("Замовлення", "742", "+12%", "up", [("Основні", "742"), ("З допродажем", "231")]), ("Товари", "1 024 шт", "+15%", "up", [("Основні", "783"), ("Допродаж", "241")]),
             ("Маржа", "389 600 ₴", "+7%", "up", [("Основні", "331 200 ₴"), ("Допродаж", "58 400 ₴")]), ("Сума", "1 084 300 ₴", "+9%", "up", [("Основні", "961 700 ₴"), ("Допродаж", "122 600 ₴")])]
    t4 = '<div class="t4">' + "".join(f'<div class="c"><small class="mu" style="font-size:12.5px">{n}</small><div class="top"><b>{v}</b><small class="{dc}" style="font-weight:500">{d}</small></div>' + "".join(f'<div class="rw"><span>{a}</span><b>{b}</b></div>' for a, b in rows) + "</div>" for n, v, d, dc, rows in tiles) + "</div>"
    kst = [("Апрув", "72%", "+3 п.", "up", "534 підтверджено"), ("Викуп", "78%", "−2 п.", "dw", "455 отримано · 128 відмов"), ("Відправлено", "611", "+10%", "up", "82% від замовлень"),
           ("Середній чек", "1 461 ₴", "−3%", "dw", "маржа 525 ₴"), ("Час підтвердження", "14 хв", "−4 хв", "up", "від додавання до апруву"), ("Дублі", "9", "", "", "не псують апрув")]
    ks = '<div class="kst">' + "".join(f'<div><small>{n}</small><b>{v}</b><em class="{dc}">{d}</em><span>{s}</span></div>' for n, v, d, dc, s in kst) + "</div>"
    PC = "1.8fr 70px 66px 66px 96px 92px 62px 62px 74px"
    prods = [("Павербанк Volt 20 000", 142, 142, 0, "227 058", "82 218", "74%", "81%", "38%"), ("Чохол MagSafe", 118, 41, 77, "52 982", "27 140", "79%", "86%", "12%"),
             ("Навушники TWS Pro", 64, 64, 0, "82 560", "24 960", "66%", "71%", "22%"), ("Зарядка GaN 65 Вт", 51, 33, 18, "38 199", "13 260", "75%", "84%", "18%"),
             ("Кабель USB-C 1 м", 49, 6, 43, "9 702", "5 390", "81%", "88%", "4%")]
    pr = tr(PC, ["Товар", '<span style="display:block;text-align:right">Замовл.</span>', '<span style="display:block;text-align:right">Осн., шт</span>', '<span style="display:block;text-align:right">Доп., шт</span>',
                 '<span style="display:block;text-align:right">Сума, ₴</span>', '<span style="display:block;text-align:right">Маржа, ₴</span>', '<span style="display:block;text-align:right">Апрув</span>',
                 '<span style="display:block;text-align:right">Викуп</span>', '<span style="display:block;text-align:right">Допродаж</span>'], "h dn") + "".join(
        tr(PC, [n] + [f'<span style="display:block;text-align:right">{x}</span>' for x in (o, a, b)] + [f'<b style="display:block;text-align:right;font-weight:600">{s}</b>', f'<span style="display:block;text-align:right">{m}</span>'] +
           [f'<span style="display:block;text-align:right">{x}</span>' for x in (ap, bo, up)], "dn") for n, o, a, b, s, m, ap, bo, up in prods)
    tabs = '<div class="tabs" style="padding:8px 10px 6px">' + "".join(f'<span class="tab {"on" if n == "Товари" else ""}" style="height:28px">{n}</span>' for n in ("Товари", "Розрізи", "Замовлення", "Цінові сегменти")) + \
           f'<span style="margin-left:auto;display:flex;gap:6px"><span class="bt s">{ic("file-text", 13)}CSV для Excel</span></span></div>'
    head = f"""<div class="ph cm"><h1>Статистика</h1><div class="r"><span class="bt s">{ic("calendar", 14)}За датою: Додане{ic("chevron-down", 13)}</span><span class="bt s">1–29 жовтня{ic("chevron-down", 13)}</span>
<span class="seg"><span class="on">Авто</span><span>Години</span><span>Дні</span><span>Тижні</span><span>Місяці</span></span><span class="bt s">{ic("link", 13)}Поділитися</span></div></div>
<div class="fls"><span class="ch on">Статус: без дублів{ic("x", 13)}</span><span class="ch on">Джерело: Instagram, TikTok{ic("x", 13)}</span><span class="ch">{ic("plus", 13)}Товар</span><span class="ch">{ic("plus", 13)}Менеджер</span><span class="ch">{ic("plus", 13)}Відділ</span>
<span class="ch">{ic("plus", 13)}Доставка</span><span class="ch">{ic("plus", 13)}Оплата</span><span class="ch">{ic("plus", 13)}UTM</span><span class="ch" style="border-style:solid">{ic("list-filter", 13)}Ще 14 фільтрів і пошук</span>
</div>"""
    body = f"""{head}{t4}{ks}
<div class="c" style="flex:none;flex-direction:row;gap:16px;padding:12px 16px 8px"><div style="flex:1;min-width:0"><h3 style="margin-bottom:2px">Статуси по днях<small>стовпці — статуси, лінія — усі · порівняння з 1–29 вересня</small></h3>{chart}</div>{lg}</div>
<div class="tbl" style="flex:1">{tabs}{pr}</div>"""
    return shell("stats", body)


PAGES = [("00-card", "0 · Картка замовлення · компактні товари", None), ("01-home", "1 · Головна", home), ("02-orders", "2 · Замовлення · щільна стрічка", orders),
         ("03-leads-list", "3 · Ліди · стрічка", leads_list), ("03b-leads-board", "3б · Ліди · компактна дошка", leads_board),
         ("05-invoices", "5 · Видаткові накладні · юрособа в рядку", invoices), ("06-product", "6 · Вікно товару", product_win),
         ("08-customer", "8 · Вікно покупця", customer_win), ("09-stats", "9 · Статистика · усі поля", stats)]


def build():
    return page("Варіант 15 — правки до сторінок", CSS, [(k, n, f(), None, None) for k, n, f in PAGES if f], cols=2)
