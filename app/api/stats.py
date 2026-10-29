"""Статистика як у LP-CRM: замовлення за днями в розрізі статусів, основне / допродаж, товари, фільтри."""
from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, selectinload

from ..config import config
from ..db import get_db
from ..models import Order, OrderItem, User
from ..services import orders as svc
from ..services.reports import period_bounds
from ..web import parse_date, today_local
from .common import sales
from .schemas import StatsOut

router = APIRouter(prefix="/api", tags=["stats"])

DATE_FIELDS = {"created": Order.created_at, "shipped": Order.shipped_at, "changed": Order.status_changed_at}


def _ids(v: str) -> list[int]:
    return [int(x) for x in (v or "").split(",") if x.strip().isdigit()]


def _strs(v: str) -> list[str]:
    return [x.strip() for x in (v or "").split(",") if x.strip()]


@router.get("/stats", response_model=StatsOut)
def stats(date_from: str = "", date_to: str = "", date_field: str = Query("created", pattern="^(created|shipped|changed)$"),
          status: str = "", product: str = "", payment: str = "", delivery: str = "", office: str = "", source: str = "",
          manager: str = "", country: str = "", utm_source: str = "", site: str = "", search_extra: str = "",
          db: Session = Depends(get_db), user: User = Depends(sales)):
    today = today_local()
    d_to = parse_date(date_to, today)
    d_from = parse_date(date_from, d_to - timedelta(days=29))
    if d_from > d_to:
        d_from, d_to = d_to, d_from
    start, end = period_bounds(d_from, d_to)
    col = DATE_FIELDS[date_field]
    q = svc.visible_orders_query(db, user).filter(col >= start, col < end)
    for ids, c in ((_ids(status), Order.status_id), (_ids(payment), Order.payment_method_id), (_ids(office), Order.office_id),
                   (_ids(source), Order.source_id), (_ids(manager), Order.manager_id)):
        if ids:
            q = q.filter(c.in_(ids))
    for vals, c in ((_strs(delivery), Order.delivery_method), (_strs(country), Order.country),
                    (_strs(utm_source), Order.utm_source), (_strs(site), Order.site)):
        if vals:
            q = q.filter(c.in_(vals))
    if search_extra:
        like = f"%{search_extra.strip()}%"
        q = q.filter(Order.extra1.ilike(like) | Order.extra2.ilike(like) | Order.extra3.ilike(like) | Order.extra4.ilike(like))
    if _ids(product):
        q = q.filter(Order.items.any(OrderItem.product_id.in_(_ids(product))))
    orders = q.options(selectinload(Order.items)).all()

    tz = ZoneInfo(config.DISPLAY_TZ)
    days: dict[str, dict[int, int]] = {}
    d = d_from
    while d <= d_to and len(days) < 400:  # кожен день періоду, навіть порожній
        days[d.isoformat()] = defaultdict(int)
        d += timedelta(days=1)
    by_status: dict[int, int] = defaultdict(int)
    zero = Decimal(0)
    s = {"orders": 0, "orders_upsell": 0, "qty_main": 0, "qty_upsell": 0, "sum_main": zero, "sum_upsell": zero,
         "margin_main": zero, "margin_upsell": zero, "discount": zero}
    prods: dict[str, dict] = {}
    for o in orders:
        when = getattr(o, col.key)
        day = when.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz).date().isoformat() if when else None
        if day in days:
            days[day][o.status_id] += 1
        by_status[o.status_id] += 1
        s["orders"] += 1
        s["discount"] += Decimal(o.discount or 0)
        if any(i.is_upsell for i in o.items):
            s["orders_upsell"] += 1
        for i in o.items:
            part = "upsell" if i.is_upsell else "main"
            rev = Decimal(i.price or 0) * i.qty
            mar = rev - Decimal(i.cost or 0) * i.qty
            s[f"qty_{part}"] += i.qty
            s[f"sum_{part}"] += rev
            s[f"margin_{part}"] += mar
            key = str(i.product_id or f"name:{i.name}")
            p = prods.setdefault(key, {"product_id": i.product_id, "name": i.name, "qty_main": 0, "qty_upsell": 0,
                                       "sum_main": zero, "sum_upsell": zero, "margin_main": zero, "margin_upsell": zero})
            p[f"qty_{part}"] += i.qty
            p[f"sum_{part}"] += rev
            p[f"margin_{part}"] += mar

    n = s["orders"] or 1
    qty = s["qty_main"] + s["qty_upsell"]
    total_sum = s["sum_main"] + s["sum_upsell"] - s["discount"]
    margin = s["margin_main"] + s["margin_upsell"] - s["discount"]  # знижка зменшує маржу основного продажу
    f = lambda v: float(round(v, 2))  # noqa: E731
    return {
        "date_from": d_from.isoformat(), "date_to": d_to.isoformat(), "date_field": date_field,
        "days": [{"day": k, "total": sum(v.values()), "by_status": {str(sid): c for sid, c in v.items()}} for k, v in days.items()],
        "statuses": [{"status_id": sid, "count": c, "share": round(c * 100 / n, 1)}
                     for sid, c in sorted(by_status.items(), key=lambda x: -x[1])],
        "summary": {
            "orders": s["orders"], "orders_plain": s["orders"] - s["orders_upsell"], "orders_upsell": s["orders_upsell"],
            "upsell_rate": round(s["orders_upsell"] * 100 / n, 1) if s["orders"] else 0,
            "qty": qty, "qty_main": s["qty_main"], "qty_upsell": s["qty_upsell"],
            "qty_upsell_rate": round(s["qty_upsell"] * 100 / qty, 1) if qty else 0,
            "margin": f(margin), "margin_main": f(s["margin_main"] - s["discount"]), "margin_upsell": f(s["margin_upsell"]),
            "margin_avg": f(margin / n) if s["orders"] else 0,
            "sum": f(total_sum), "sum_main": f(s["sum_main"] - s["discount"]), "sum_upsell": f(s["sum_upsell"]),
            "avg_check": f(total_sum / n) if s["orders"] else 0,
        },
        "products": sorted(({**p, "qty": p["qty_main"] + p["qty_upsell"], "sum": f(p["sum_main"] + p["sum_upsell"]),
                             "margin": f(p["margin_main"] + p["margin_upsell"]), "sum_main": f(p["sum_main"]),
                             "sum_upsell": f(p["sum_upsell"]), "margin_main": f(p["margin_main"]),
                             "margin_upsell": f(p["margin_upsell"])} for p in prods.values()),
                           key=lambda x: (-x["qty"], -x["sum"]))[:500],
    }

