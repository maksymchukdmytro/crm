"""Головна сторінка: ключові показники бізнесу одним запитом.

Гроші й кількість рахуються за замовленнями без скасованих і дублів (як «продажі»); апрув, викуп і
допродаж — тими самими формулами, що на сторінці «Статистика» (services/stats.py).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Customer, Order, Payment, Product, Status, User, utcnow
from . import settings as st
from . import stats as st_svc
from .orders import visible_orders_query
from .reports import period_bounds

NOT_SALES = ("cancelled", "duplicate")
WAIT_SHIP = ("confirmed", "packing")


def _money(v) -> float:
    return float(round(Decimal(v or 0), 2))


def _delta(cur: float, prev: float) -> float | None:
    """Зміна у відсотках; None, якщо порівнювати нема з чим."""
    if not prev:
        return None
    return round((cur - prev) * 100 / prev, 1)


def parse_period(period: str | None, today: date) -> tuple[date, date, date, date]:
    """Період головної і такий самий попередній для порівняння.

    `YYYY-MM` — місяць (поточний — з 1-го по сьогодні, порівняння з тим самим відрізком минулого місяця);
    `YYYY-MM-DD..YYYY-MM-DD` — свій період (порівняння з відрізком тієї самої довжини перед ним);
    порожньо — поточний місяць."""
    period = (period or "").strip()
    try:
        if ".." in period:
            a, b = period.split("..", 1)
            d1, d2 = date.fromisoformat(a), date.fromisoformat(b)
            if d2 < d1:
                d1, d2 = d2, d1
            d2 = min(d2, today)
            length = (d2 - d1).days
            return d1, d2, d1 - timedelta(days=length + 1), d1 - timedelta(days=1)
        if period:
            y, m = (int(x) for x in period.split("-")[:2])
            d1 = date(y, m, 1)
        else:
            d1 = today.replace(day=1)
    except (ValueError, TypeError):
        d1 = today.replace(day=1)
    if d1 > today:
        d1 = today.replace(day=1)
    month_end = (d1.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    d2 = min(month_end, today)
    prev_end = d1 - timedelta(days=1)
    prev_start = prev_end.replace(day=1)
    # той самий відрізок минулого місяця (1-ше … те саме число), щоб порівняння було чесним
    prev_same_end = min(prev_start + timedelta(days=(d2 - d1).days), prev_end)
    return d1, d2, prev_start, prev_same_end


def dashboard(db: Session, user: User, period: str | None = None) -> dict:
    tz = st_svc.tz()
    today = datetime.now(tz).date()
    month_start, period_end, prev_start, prev_same_end = parse_period(period, today)

    sales = (visible_orders_query(db, user).join(Status, Status.id == Order.status_id)
             .filter(Status.code.notin_(NOT_SALES), Order.duplicate_of_id.is_(None)))

    def agg(d1: date, d2: date) -> tuple[int, float]:
        s, e = period_bounds(d1, d2)
        n, total = sales.filter(Order.created_at >= s, Order.created_at < e).with_entities(
            func.count(Order.id), func.coalesce(func.sum(Order.total), 0)).one()
        return int(n), _money(total)

    t_n, t_sum = agg(today, today)
    y_n, y_sum = agg(today - timedelta(days=1), today - timedelta(days=1))
    m_n, m_sum = agg(month_start, period_end)
    p_n, p_sum = agg(prev_start, prev_same_end)

    # по днях періоду: кількість і сума; prev_days — попередній період день у день (пунктир на графіку)
    day = func.date_trunc("day", st_svc.local_expr(Order.created_at)).label("d")

    def per_day(d1: date, d2: date) -> list[dict]:
        s, e = period_bounds(d1, d2)
        rows = (sales.filter(Order.created_at >= s, Order.created_at < e)
                .with_entities(day, func.count(Order.id), func.coalesce(func.sum(Order.total), 0)).group_by(day).all())
        by_day = {r[0].date(): (int(r[1]), _money(r[2])) for r in rows}
        out, d = [], d1
        while d <= d2:
            n, total = by_day.get(d, (0, 0.0))
            out.append({"day": d.isoformat(), "orders": n, "sum": total})
            d += timedelta(days=1)
        return out

    days = per_day(month_start, period_end)
    prev_days = per_day(prev_start, prev_same_end)

    # апрув, викуп, допродаж — як у «Статистиці», і те саме за попередній період (дельта в пунктах)
    def quality(d1: date, d2: date) -> dict:
        fq = st_svc.StatsFilter(date_from=d1, date_to=d2)
        return st_svc.summary_from(st_svc._with_aggregates(
            st_svc.base_query(db, user, fq, *period_bounds(d1, d2)), st_svc.per_order_items()).one())

    f = st_svc.StatsFilter(date_from=month_start, date_to=period_end)
    summary = quality(month_start, period_end)
    prev_q = quality(prev_start, prev_same_end)

    def pp(k: str) -> float | None:
        return round(float(summary[k]) - float(prev_q[k]), 1) if prev_q.get("orders") else None

    # покупці
    ms, me = period_bounds(month_start, period_end)
    customers = db.query(func.count(Customer.id)).scalar() or 0
    new_customers = db.query(func.count(Customer.id)).filter(Customer.created_at >= ms, Customer.created_at < me).scalar() or 0
    ps, pe = period_bounds(prev_start, prev_same_end)
    new_prev = db.query(func.count(Customer.id)).filter(Customer.created_at >= ps, Customer.created_at < pe).scalar() or 0
    ts0, te0 = period_bounds(today, today)
    new_today = db.query(func.count(Customer.id)).filter(Customer.created_at >= ts0, Customer.created_at < te0).scalar() or 0
    blacklisted = db.query(func.count(Customer.id)).filter(Customer.is_blacklisted.is_(True)).scalar() or 0
    # повторні — покупці з двома й більше замовленнями (без скасованих і дублів) серед усіх, хто замовляв
    per_cust = (sales.filter(Order.customer_id.isnot(None)).with_entities(Order.customer_id, func.count(Order.id).label("n"))
                .group_by(Order.customer_id).subquery())
    buyers, repeat = db.query(func.count(), func.count().filter(per_cust.c.n >= 2)).select_from(per_cust).one()
    repeat_share = round(repeat * 100 / buyers, 1) if buyers else 0.0

    # що потребує уваги зараз
    vis = visible_orders_query(db, user).join(Status, Status.id == Order.status_id)
    leads_on = st.get(db, "leads_enabled") != "0"
    leads_new = vis.filter(Status.code == "new").count() if leads_on else 0
    leads_open = vis.filter(Status.stage == "lead", ~Status.code.in_(("duplicate", "lead_refused"))).count() if leads_on else 0
    unsorted = vis.filter(Status.code == "unsorted").count()
    to_ship = vis.filter(Status.code.in_(WAIT_SHIP), Order.ttn == "").count()
    on_way = vis.filter(Order.delivery_state.in_(("created", "in_transit", "arrived"))).count()
    arrived = vis.filter((Order.delivery_state == "arrived") | (Status.code == "arrived")).count()
    reminders = vis.filter(Order.remind_at.isnot(None), Order.remind_at <= utcnow()).count()
    visible_ids = visible_orders_query(db, user).with_entities(Order.id).subquery()
    cod_expected = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.status == "expected", Payment.order_id.in_(visible_ids.select())).scalar()
    cod_collected = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.status == "collected", Payment.order_id.in_(visible_ids.select())).scalar()
    low_stock = db.query(func.count(Product.id)).filter(
        Product.is_active.is_(True), Product.min_stock > 0, Product.stock - Product.reserved <= Product.min_stock).scalar() or 0

    top = st_svc.products(db, user, f, limit=5)

    # команда сьогодні (лише адміністратору): ліди й нові на менеджері, підтверджені замовлення, апрув і сума
    team = []
    if user.role == "admin":
        ts, te = period_bounds(today, today)
        conf_rows = db.query(Order.manager_id, func.count(Order.id), func.coalesce(func.sum(Order.total), 0)).filter(
            Order.confirmed_at >= ts, Order.confirmed_at < te, Order.manager_id.isnot(None)).group_by(Order.manager_id).all()
        confirmed = {r[0]: (int(r[1]), _money(r[2])) for r in conf_rows}
        assigned = dict(db.query(Order.manager_id, func.count(Order.id)).filter(
            Order.created_at >= ts, Order.created_at < te, Order.manager_id.isnot(None)).group_by(Order.manager_id).all())
        leads_today = dict(db.query(Order.manager_id, func.count(Order.id)).join(Status, Status.id == Order.status_id).filter(
            Order.created_at >= ts, Order.created_at < te, Order.manager_id.isnot(None),
            (Status.stage == "lead") | Order.confirmed_at.isnot(None)).group_by(Order.manager_id).all())
        for u in db.query(User).filter(User.is_active.is_(True), User.role.in_(("admin", "manager"))).order_by(User.id):
            c_n, c_sum = confirmed.get(u.id, (0, 0.0))
            new_n = int(assigned.get(u.id, 0))
            team.append({"id": u.id, "name": u.display, "role": u.role, "confirmed": c_n, "new": new_n,
                         "leads": int(leads_today.get(u.id, 0)), "sum": c_sum,
                         "approve_rate": round(c_n * 100 / new_n, 1) if new_n else None,
                         "last_login": u.last_login_at.isoformat() + "Z" if u.last_login_at else None})

    return {
        "today": {"date": today.isoformat(), "orders": t_n, "sum": t_sum, "orders_delta": _delta(t_n, y_n), "sum_delta": _delta(t_sum, y_sum),
                  "yesterday_orders": y_n, "yesterday_sum": y_sum},
        "period": {"date_from": month_start.isoformat(), "date_to": period_end.isoformat(),
                   "prev_from": prev_start.isoformat(), "prev_to": prev_same_end.isoformat()},
        "quality": {"approve_rate": summary["approve_rate"], "buyout_rate": summary["buyout_rate"], "upsell_rate": summary["upsell_rate"],
                    "approve_delta": pp("approve_rate"), "buyout_delta": pp("buyout_rate"), "upsell_delta": pp("upsell_rate")},
        "month": {"date_from": month_start.isoformat(), "orders": m_n, "sum": m_sum, "avg_check": _money(m_sum / m_n) if m_n else 0.0,
                  "orders_delta": _delta(m_n, p_n), "sum_delta": _delta(m_sum, p_sum), "prev_orders": p_n, "prev_sum": p_sum,
                  "approve_rate": summary["approve_rate"], "buyout_rate": summary["buyout_rate"], "upsell_rate": summary["upsell_rate"],
                  "margin": summary["margin"]},
        "customers": {"total": int(customers), "new": int(new_customers), "new_delta": _delta(new_customers, new_prev),
                      "new_prev": int(new_prev), "new_today": int(new_today), "repeat_share": repeat_share, "blacklisted": int(blacklisted)},
        "attention": {"leads_new": leads_new, "leads_open": leads_open, "orders_unsorted": unsorted, "to_ship": to_ship, "on_way": on_way, "arrived": arrived,
                      "reminders": reminders, "low_stock": int(low_stock),
                      "cod_expected": _money(cod_expected), "cod_collected": _money(cod_collected)},
        "days": days,
        "prev_days": prev_days,
        "team": team,
        "top": [{"product_id": p["product_id"], "name": p["name"], "qty": p["qty"], "sum": p["sum"]} for p in top],
    }
