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


def dashboard(db: Session, user: User) -> dict:
    tz = st_svc.tz()
    today = datetime.now(tz).date()
    month_start = today.replace(day=1)
    prev_end = month_start - timedelta(days=1)
    prev_start = prev_end.replace(day=1)
    # той самий відрізок минулого місяця (1-ше … сьогоднішнє число), щоб порівняння було чесним
    prev_same_end = min(prev_start + timedelta(days=today.day - 1), prev_end)

    sales = (visible_orders_query(db, user).join(Status, Status.id == Order.status_id)
             .filter(Status.code.notin_(NOT_SALES), Order.duplicate_of_id.is_(None)))

    def agg(d1: date, d2: date) -> tuple[int, float]:
        s, e = period_bounds(d1, d2)
        n, total = sales.filter(Order.created_at >= s, Order.created_at < e).with_entities(
            func.count(Order.id), func.coalesce(func.sum(Order.total), 0)).one()
        return int(n), _money(total)

    t_n, t_sum = agg(today, today)
    y_n, y_sum = agg(today - timedelta(days=1), today - timedelta(days=1))
    m_n, m_sum = agg(month_start, today)
    p_n, p_sum = agg(prev_start, prev_same_end)

    # по днях місяця: кількість і сума
    s, e = period_bounds(month_start, today)
    day = func.date_trunc("day", st_svc.local_expr(Order.created_at)).label("d")
    rows = (sales.filter(Order.created_at >= s, Order.created_at < e)
            .with_entities(day, func.count(Order.id), func.coalesce(func.sum(Order.total), 0)).group_by(day).all())
    by_day = {r[0].date(): (int(r[1]), _money(r[2])) for r in rows}
    days = []
    d = month_start
    while d <= today:
        n, total = by_day.get(d, (0, 0.0))
        days.append({"day": d.isoformat(), "orders": n, "sum": total})
        d += timedelta(days=1)

    # апрув, викуп, допродаж за місяць — як у «Статистиці»
    f = st_svc.StatsFilter(date_from=month_start, date_to=today)
    summary = st_svc.summary_from(st_svc._with_aggregates(
        st_svc.base_query(db, user, f, *period_bounds(month_start, today)), st_svc.per_order_items()).one())

    # покупці
    ms, me = period_bounds(month_start, today)
    customers = db.query(func.count(Customer.id)).scalar() or 0
    new_customers = db.query(func.count(Customer.id)).filter(Customer.created_at >= ms, Customer.created_at < me).scalar() or 0
    ps, pe = period_bounds(prev_start, prev_same_end)
    new_prev = db.query(func.count(Customer.id)).filter(Customer.created_at >= ps, Customer.created_at < pe).scalar() or 0

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

    # команда сьогодні (лише адміністратору): скільки кожен підтвердив і коли заходив
    team = []
    if user.role == "admin":
        ts, te = period_bounds(today, today)
        confirmed = dict(db.query(Order.manager_id, func.count(Order.id)).filter(
            Order.confirmed_at >= ts, Order.confirmed_at < te, Order.manager_id.isnot(None)).group_by(Order.manager_id).all())
        assigned = dict(db.query(Order.manager_id, func.count(Order.id)).filter(
            Order.created_at >= ts, Order.created_at < te, Order.manager_id.isnot(None)).group_by(Order.manager_id).all())
        for u in db.query(User).filter(User.is_active.is_(True), User.role.in_(("admin", "manager"))).order_by(User.id):
            team.append({"id": u.id, "name": u.display, "role": u.role, "confirmed": int(confirmed.get(u.id, 0)),
                         "new": int(assigned.get(u.id, 0)),
                         "last_login": u.last_login_at.isoformat() + "Z" if u.last_login_at else None})

    return {
        "today": {"date": today.isoformat(), "orders": t_n, "sum": t_sum, "orders_delta": _delta(t_n, y_n), "sum_delta": _delta(t_sum, y_sum),
                  "yesterday_orders": y_n, "yesterday_sum": y_sum},
        "month": {"date_from": month_start.isoformat(), "orders": m_n, "sum": m_sum, "avg_check": _money(m_sum / m_n) if m_n else 0.0,
                  "orders_delta": _delta(m_n, p_n), "sum_delta": _delta(m_sum, p_sum), "prev_orders": p_n, "prev_sum": p_sum,
                  "approve_rate": summary["approve_rate"], "buyout_rate": summary["buyout_rate"], "upsell_rate": summary["upsell_rate"],
                  "margin": summary["margin"]},
        "customers": {"total": int(customers), "new": int(new_customers), "new_delta": _delta(new_customers, new_prev)},
        "attention": {"leads_new": leads_new, "leads_open": leads_open, "orders_unsorted": unsorted, "to_ship": to_ship, "on_way": on_way, "arrived": arrived,
                      "reminders": reminders, "low_stock": int(low_stock),
                      "cod_expected": _money(cod_expected), "cod_collected": _money(cod_collected)},
        "days": days,
        "team": team,
        "top": [{"product_id": p["product_id"], "name": p["name"], "qty": p["qty"], "sum": p["sum"]} for p in top],
    }
