"""Форматування для API й документів: місцевий час, гроші, телефон, опис змін у журналі, дати."""
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from .config import config

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


def parse_date(v: str | None, default: date | None = None) -> date | None:
    if not v:
        return default
    try:
        return date.fromisoformat(v)
    except ValueError:
        return default


def today_local() -> date:
    return datetime.now(TZ).date()
