"""Спільні дані й фрагменти для макетів CRM (лише картинки, не продакшн-код)."""
import re
from pathlib import Path

ROOT = Path(__file__).parent
ICONS = ROOT / "icons"
FONTS = ROOT / "fonts"
_ic = {}


def ic(name, size=18, sw=1.75, cls=""):
    if name not in _ic:
        raw = (ICONS / f"{name}.svg").read_text()
        body = raw[raw.index(">", raw.index("<svg")) + 1: raw.rindex("</svg>")]
        _ic[name] = re.sub(r"\s+", " ", body).strip()
    return (f'<svg class="i {cls}" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_ic[name]}</svg>')


def font_face(family, file, weight="100 900"):
    return (f"@font-face{{font-family:'{family}';src:url('file://{FONTS / file}') format('truetype');"
            f"font-weight:{weight};font-display:block}}")


ALL_FONTS = "\n".join([
    font_face("Manrope", "Manrope.ttf", "200 800"), font_face("Onest", "Onest.ttf"), font_face("Unbounded", "Unbounded.ttf"),
    font_face("Golos", "GolosText.ttf", "400 900"), font_face("Commissioner", "Commissioner.ttf"),
    font_face("Geologica", "Geologica.ttf"), font_face("MontAlt", "MontserratAlternates-Medium.ttf", "500"),
    font_face("JB", "JetBrainsMono.ttf", "100 800"), font_face("Rubik", "Rubik.ttf", "300 900"),
])

# ---------------------------------------------------------------- навігація CRM
NAV = [
    ("Продажі", [("home", "Головна", "house", None), ("leads", "Ліди", "inbox", "12"), ("orders", "Замовлення", "receipt-text", "248"),
                 ("board", "Дошка", "square-kanban", None), ("customers", "Покупці", "contact", None)]),
    ("Склад", [("products", "Товари", "package", None), ("warehouse", "Склад", "boxes", None), ("purchases", "Закупівлі", "shopping-cart", None)]),
    ("Гроші й аналітика", [("payments", "Оплати", "wallet", None), ("stats", "Статистика", "chart-column-stacked", None),
                           ("reports", "Звіти", "chart-bar", None)]),
    ("Керування", [("audit", "Журнал дій", "clock-fading", None), ("settings", "Налаштування", "settings", None),
                   ("system", "Система", "activity", None)]),
]
FLAT_NAV = [it for _, items in NAV for it in items]

# ---------------------------------------------------------------- статуси
ST = {
    "new": ("Новий", "#3B82F6"), "noans": ("Недодзвон", "#F59E0B"), "call": ("Передзвонити", "#8B5CF6"), "dup": ("Дубль", "#94A3B8"),
    "ok": ("Підтверджено", "#10B981"), "pack": ("Комплектується", "#0891B2"), "sent": ("Відправлено", "#6366F1"),
    "arr": ("Прибуло у відділення", "#F97316"), "got": ("Отримано", "#16A34A"), "ref": ("Відмова", "#EF4444"),
    "paid": ("Оплачено", "#0EA5E9"), "ret": ("Повернено", "#64748B"),
}


def pill(code, cls="st"):
    name, c = ST[code]
    return f'<span class="{cls}" style="--c:{c}"><i></i>{name}</span>'


ORDERS = [
    (1482, "Шевченко Тарас", "+380 67 123 45 67", "Павербанк 20000 мА·год", 1, "1 797", "ok", "НП · Київ, №12", "Instagram", "Олена", "14:32"),
    (1481, "Коваленко Ірина", "+380 93 552 10 08", "Набір кабелів USB-C", 0, "649", "new", "—", "Лендинг", "—", "14:18"),
    (1480, "Бондаренко Олег", "+380 50 771 23 90", "Навушники TWS Pro", 0, "1 290", "sent", "НП · Львів, №4", "Rozetka", "Андрій", "13:57"),
    (1479, "Ткаченко Марія", "+380 66 410 77 12", "Лампа настільна LED", 1, "1 048", "pack", "Укрпошта · Вінниця", "Facebook", "Олена", "13:40"),
    (1478, "Кравченко Андрій", "+380 97 300 45 61", "Зарядка GaN 65 Вт", 0, "749", "got", "НП · Одеса, №31", "Prom", "Андрій", "12:15"),
    (1477, "Олійник Світлана", "+380 68 905 12 44", "Павербанк 10000 мА·год", 0, "999", "ref", "НП · Дніпро, №7", "Instagram", "Олена", "11:52"),
    (1476, "Мельник Денис", "+380 63 118 90 05", "Смарт-годинник Fit 3", 1, "2 398", "arr", "НП · Тульчин, №1", "TikTok", "Андрій", "11:30"),
    (1475, "Шевчук Анна", "+380 95 640 31 27", "Чохол MagSafe", 0, "449", "paid", "Meest · Київ", "Лендинг", "Олена", "10:47"),
    (1474, "Поліщук Віктор", "+380 73 222 81 19", "Колонка Go Mini", 0, "1 599", "sent", "НП · Харків, №52", "Rozetka", "Андрій", "10:05"),
    (1473, "Лисенко Юлія", "+380 99 731 04 66", "Кабель Lightning 2 м", 1, "398", "new", "—", "Instagram", "—", "09:41"),
    (1472, "Гнатюк Роман", "+380 67 880 15 72", "Павербанк 20000 мА·год", 0, "1 599", "ok", "НП · Київ, №201", "Facebook", "Олена", "09:12"),
]

TABS = [("Усі", "248"), ("Підтверджено", "31"), ("Комплектується", "14"), ("Відправлено", "57"), ("У відділенні", "22"),
        ("Отримано", "96"), ("Відмова", "9")]

# ---------------------------------------------------------------- картка замовлення
ORDER = dict(
    id=1482, created="29.10.2026, 14:32", name="Шевченко Тарас Григорович", phone="+380 67 123 45 67", email="taras.sh@gmail.com",
    total="1 797", items=[
        ("Павербанк 20000 мА·год", "Чорний · 20 000 мА·год", "PB-20-BLK", "1", "1 599", "1 599", False),
        ("Кабель USB-C → USB-C 1 м", "Допродаж", "CB-C1-WHT", "1", "198", "198", True),
    ],
)
CUSTOMER = [("Замовлень", "4"), ("Викуп", "75%"), ("Відмов", "1"), ("Сума", "5 840 ₴")]
TIMELINE = [
    ("14:32", "Заявка з лендингу", "utm: instagram / stories / powerbank-20", "inbox"),
    ("14:40", "Олена взяла в роботу", "Відділ «Інтернет-магазин»", "user"),
    ("14:52", "Статус «Підтверджено»", "Товар зарезервовано на складі", "circle-check-big"),
    ("14:53", "SMS доставлено", "«Замовлення №1482 підтверджено…»", "message-square"),
    ("15:20", "Створено ТТН", "20450913998365 · Нова Пошта", "truck"),
]

# ---------------------------------------------------------------- налаштування
SETTINGS = [("Загальні", "sliders-horizontal"), ("Статуси", "list-checks"), ("Довідники", "layers"), ("Юрособи", "landmark"),
            ("Нова Пошта", "truck"), ("Checkbox", "receipt"), ("Маркетплейси", "store"), ("SMS і Viber", "message-square"),
            ("Telegram", "send"), ("Документи", "file-text"), ("Покупці", "users"), ("Користувачі", "key-round")]
# назва, код, розділ, склад, чек, sms
STATUS_ROWS = [
    ("new", "Ліди", "—", "—", "—"), ("noans", "Ліди", "—", "—", "Не додзвонились"), ("call", "Ліди", "—", "—", "—"),
    ("dup", "Ліди", "—", "—", "—"),
    ("ok", "Замовлення", "Резерв", "—", "Підтвердження"), ("pack", "Замовлення", "Резерв", "—", "—"),
    ("sent", "Замовлення", "Списання", "Продаж", "ТТН"), ("arr", "Замовлення", "—", "—", "Нагадування"),
    ("got", "Замовлення", "—", "Післяплата", "Дякуємо"), ("ref", "Замовлення", "Повернення", "Повернення", "—"),
]

# ---------------------------------------------------------------- атрибути
ATTR_GROUPS = [
    ("Колір", "palette", "Колір", [("Чорний", "#151515"), ("Білий", "#F4F4F2"), ("Синій", "#2F5BEA"), ("Рожевий", "#F2A7C3")], "32 товари"),
    ("Ємність", "zap", "Список", [("10 000 мА·год", None), ("20 000 мА·год", None), ("30 000 мА·год", None)], "8 товарів"),
    ("Довжина кабелю", "ruler", "Список", [("1 м", None), ("2 м", None), ("3 м", None)], "12 товарів"),
    ("Розмір", "box", "Список", [("S", None), ("M", None), ("L", None), ("XL", None)], "6 товарів"),
    ("Роз'єм", "link", "Список", [("USB-C", None), ("Lightning", None), ("USB-A", None)], "15 товарів"),
    ("Матеріал", "layers", "Список", [("Силікон", None), ("Шкіра", None), ("Пластик", None)], "9 товарів"),
]
# колір, ємність, sku, ціна, залишок, резерв
VARIANTS = [
    ("Чорний", "#151515", "10 000", "PB-10-BLK", "999", 24, 2), ("Чорний", "#151515", "20 000", "PB-20-BLK", "1 599", 18, 3),
    ("Білий", "#F4F4F2", "10 000", "PB-10-WHT", "999", 11, 0), ("Білий", "#F4F4F2", "20 000", "PB-20-WHT", "1 599", 3, 1),
    ("Синій", "#2F5BEA", "10 000", "PB-10-BLU", "999", 0, 0), ("Синій", "#2F5BEA", "20 000", "PB-20-BLU", "1 649", 7, 0),
]


def initials(name):
    p = name.split()
    return (p[0][0] + (p[1][0] if len(p) > 1 else "")).upper()


def page(title, css, frames, w=1440, h=900, gap=48, cols=2, bg="#DADCD6", label_color="#222"):
    """Сторінка-дошка: кадри 1440×900 у сітці; кожен кадр — .frame з data-name для окремого знімка."""
    heads = "".join(
        f'<section class="cell"><div class="cap" style="color:{label_color}">{n}</div><div class="frame" data-name="{k}" '
        f'style="width:{fw or w}px;height:{fh or h}px">{html}</div></section>'
        for k, n, html, fw, fh in frames)
    return f"""<!doctype html><html lang="uk"><head><meta charset="utf-8"><title>{title}</title><style>
{ALL_FONTS}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:{bg}}}
.board{{display:grid;grid-template-columns:repeat({cols},max-content);gap:{gap}px;padding:{gap}px;align-items:start}}
.cap{{font:600 22px/1.2 'Manrope',sans-serif;margin:0 0 14px 4px;letter-spacing:-.01em}}
.frame{{position:relative;overflow:hidden;border-radius:18px;box-shadow:0 30px 60px -30px rgba(0,0,0,.35)}}
.i{{flex:none;display:inline-block;vertical-align:middle}}
{css}
</style></head><body><div class="board">{heads}</div></body></html>"""
