"""Шаблони, фільтри і допоміжні функції для HTML-сторінок."""
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from .config import config
from .models import DELIVERY_METHODS, DELIVERY_STATES, PAYMENT_TYPES, ROLES

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
# Класичний (серверний) інтерфейс живе за адресою <ROOT_PATH>/classic; новий застосунок — у корені.
CLASSIC_PREFIX = "/classic"
CLASSIC_ROOT = config.ROOT_PATH + CLASSIC_PREFIX
TZ = ZoneInfo(config.DISPLAY_TZ)
UTC = ZoneInfo("UTC")


def to_local(v: datetime | None) -> datetime | None:
    if v is None:
        return None
    return v.replace(tzinfo=UTC).astimezone(TZ)


def f_money(v, decimals: bool = False) -> str:
    if v is None or v == "":
        return "0"
    d = Decimal(str(v))
    if not decimals and d == d.to_integral_value():
        s = f"{int(d):,}"
    else:
        s = f"{d:,.2f}"
    return s.replace(",", " ")


def f_dt(v: datetime | None, fmt: str = "%d.%m.%Y %H:%M") -> str:
    v = to_local(v)
    return v.strftime(fmt) if v else ""


def f_date(v) -> str:
    if v is None:
        return ""
    if isinstance(v, datetime):
        return f_dt(v, "%d.%m.%Y")
    return v.strftime("%d.%m.%Y")


def f_pct(v: float) -> str:
    return f"{v:.1f}%"


def f_phone(v: str) -> str:
    if v and len(v) == 12 and v.startswith("380"):
        return f"+{v[:2]} {v[2:5]} {v[5:8]} {v[8:10]} {v[10:]}"
    return v or ""


def f_json(v) -> Markup:
    return Markup(json.dumps(v, ensure_ascii=False, default=str).replace("</", "<\\/"))


FIELD_NAMES = {
    "customer_name": "ПІБ", "phone": "телефон", "email": "email", "comment": "коментар",
    "delivery_method": "доставка", "city_name": "місто", "city_ref": "місто (ref)", "warehouse_name": "відділення",
    "warehouse_ref": "відділення (ref)", "address": "адреса", "postcode": "індекс", "ttn": "ТТН",
    "delivery_cost": "вартість доставки", "payment_type": "тип оплати", "prepayment": "передоплата",
    "discount": "знижка", "site": "сайт", "source": "джерело", "items": "товари", "duplicate_of": "дубль замовлення",
}


def _fmt_val(v) -> str:
    if v is None or v == "":
        return "—"
    if isinstance(v, list):
        return ", ".join(_fmt_val(x) for x in v) if v else "—"
    if isinstance(v, dict):
        return "; ".join(f"{k}: {_fmt_val(x)}" for k, x in v.items())
    return str(v)


def f_details(d) -> str:
    if not isinstance(d, dict):
        return _fmt_val(d)
    parts = []
    for k, v in d.items():
        if v in (None, "", []):
            continue
        name = FIELD_NAMES.get(k, k)
        if k.endswith("_ref"):
            continue
        if isinstance(v, list) and len(v) == 2 and not isinstance(v[0], list) and k in FIELD_NAMES:
            parts.append(f"{name}: {_fmt_val(v[0])} → {_fmt_val(v[1])}")
        else:
            parts.append(f"{name}: {_fmt_val(v)}")
    return "; ".join(parts)


templates.env.filters.update(money=f_money, dt=f_dt, d=f_date, pct=f_pct, phone=f_phone, tojs=f_json,
                             details=f_details)
templates.env.globals.update(
    DELIVERY_METHODS=DELIVERY_METHODS, DELIVERY_STATES=DELIVERY_STATES, PAYMENT_TYPES=PAYMENT_TYPES, ROLES=ROLES,
)

NAV = [
    ("orders", "/orders", "Замовлення", ("admin", "manager", "warehouse")),
    ("products", "/products", "Товари", ("admin", "manager", "warehouse")),
    ("warehouse", "/warehouse", "Склад", ("admin", "warehouse")),
    ("purchases", "/purchases", "Закупівлі", ("admin", "warehouse")),
    ("payments", "/payments", "Оплати", ("admin",)),
    ("reports", "/reports", "Звіти", ("admin", "manager")),
    ("audit", "/audit", "Журнал дій", ("admin",)),
    ("settings", "/settings", "Налаштування", ("admin",)),
]


def flash(request: Request, message: str, kind: str = "ok"):
    # Присвоюємо новий список: сесія Starlette не помічає змін усередині вкладених об'єктів
    request.session["_flash"] = [*request.session.get("_flash", []), [kind, message]]


def render(request: Request, name: str, ctx: dict | None = None, status_code: int = 200, active: str = ""):
    user = getattr(request.state, "user", None)
    context = dict(ctx or {})
    context.setdefault("user", user)
    context.setdefault("active", active)
    context.setdefault("embed", request.query_params.get("embed") == "1")
    context["flashes"] = request.session.pop("_flash", [])
    context["nav"] = [n for n in NAV if user and user.role in n[3]]
    context["company"] = getattr(request.state, "company", "CRM")
    return templates.TemplateResponse(request, name, context, status_code=status_code)


def redirect(url: str, status_code: int = 303) -> RedirectResponse:
    if url.startswith("/") and not url.startswith("//"):
        url = CLASSIC_ROOT + url
    return RedirectResponse(url, status_code=status_code)


def safe_next(url: str | None, default: str = "/orders") -> str:
    if url and url.startswith("/") and not url.startswith("//"):
        return url
    return default


def parse_date(v: str | None, default: date | None = None) -> date | None:
    if not v:
        return default
    try:
        return date.fromisoformat(v)
    except ValueError:
        return default


def today_local() -> date:
    return datetime.now(TZ).date()


def date_presets() -> list[tuple[str, date, date]]:
    t = today_local()
    month_start = t.replace(day=1)
    prev_month_end = month_start - timedelta(days=1)
    return [
        ("Сьогодні", t, t),
        ("Вчора", t - timedelta(days=1), t - timedelta(days=1)),
        ("7 днів", t - timedelta(days=6), t),
        ("30 днів", t - timedelta(days=29), t),
        ("Цей місяць", month_start, t),
        ("Минулий місяць", prev_month_end.replace(day=1), prev_month_end),
    ]


def qs(params: dict, **override) -> str:
    merged = {**params, **override}
    return urlencode({k: v for k, v in merged.items() if v not in (None, "", 0, "0") or k == "page"})


def icon(name: str, cls: str = "") -> Markup:
    """Лінійна іконка з SVG-спрайту /static/icons.svg (вбудовується через <use>)."""
    return Markup(f'<svg class="i {cls}" aria-hidden="true"><use href="#{name}"/></svg>')


_SPRITE = (BASE_DIR / "static" / "icons.svg").read_text(encoding="utf-8")


def sprite() -> Markup:
    """Спрайт іконок вставляється в сторінку один раз — без додаткових запитів і проблем із префіксом /crm."""
    return Markup(_SPRITE)


templates.env.globals.update(qs=qs, date_presets=date_presets, R=CLASSIC_ROOT, RA=config.ROOT_PATH, icon=icon, sprite=sprite)
