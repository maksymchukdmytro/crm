"""Покупці: один запис на номер телефону, історія й суми — із замовлень; групи й чорний список."""
from __future__ import annotations

from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session

from ..models import Customer, CustomerGroup, Order, Status


def default_group_id(db: Session) -> int | None:
    g = db.query(CustomerGroup).order_by(CustomerGroup.sort, CustomerGroup.id).first()
    return g.id if g else None


def attach(db: Session, order: Order) -> Customer | None:
    """Прив'язує замовлення до покупця за телефоном; нового покупця створює. Ручні правки картки покупця
    не перезаписуються — порожні ім'я й пошта лише доповнюються даними замовлення."""
    phone = (order.phone or "").strip()
    if not phone:
        order.customer = None
        order.customer_id = None
        return None
    c = db.query(Customer).filter(Customer.phone == phone).one_or_none()
    if c is None:
        with db.no_autoflush:
            c = Customer(phone=phone, name=order.customer_name or "", email=order.email or "",
                         country=order.country or "UA", group_id=default_group_id(db))
        db.add(c)
    else:
        if not c.name and order.customer_name:
            c.name = order.customer_name
        if not c.email and order.email:
            c.email = order.email
    order.customer = c
    return c


def _flags():
    delivered = or_(Status.code == "delivered", Order.delivery_state == "delivered")
    refused = and_(~delivered, or_(Status.code.in_(("refused", "returned")),
                                   Order.delivery_state.in_(("refused", "returned"))))
    cancelled = Status.code.in_(("cancelled",))
    return delivered, refused, cancelled


def stats_query(db: Session):
    """Підсумки по покупцях: замовлення, отримані, відмови, скасовані, сума отриманих і загальна, дати."""
    delivered, refused, cancelled = _flags()
    one = lambda c: func.coalesce(func.sum(case((c, 1), else_=0)), 0)  # noqa: E731
    return (
        db.query(
            Order.customer_id.label("cid"),
            func.count(Order.id).label("orders"),
            one(delivered).label("delivered"),
            one(refused).label("refused"),
            one(cancelled).label("cancelled"),
            func.coalesce(func.sum(case((delivered, Order.total), else_=0)), 0).label("sum_delivered"),
            func.coalesce(func.sum(Order.total), 0).label("sum_total"),
            func.min(Order.created_at).label("first_at"),
            func.max(Order.created_at).label("last_at"),
        )
        .join(Status, Status.id == Order.status_id)
        .filter(Order.customer_id.isnot(None))
        .group_by(Order.customer_id)
    )


def stats_for(db: Session, ids: list[int]) -> dict[int, dict]:
    if not ids:
        return {}
    rows = stats_query(db).filter(Order.customer_id.in_(ids)).all()
    return {r.cid: _row(r) for r in rows}


def _row(r) -> dict:
    done = int(r.delivered) + int(r.refused)
    return {
        "orders": int(r.orders), "delivered": int(r.delivered), "refused": int(r.refused), "cancelled": int(r.cancelled),
        "sum_delivered": float(r.sum_delivered or 0), "sum_total": float(r.sum_total or 0),
        "buyout_rate": round(int(r.delivered) * 100 / done, 1) if done else None,
        "first_at": r.first_at, "last_at": r.last_at,
    }


EMPTY_STATS = {"orders": 0, "delivered": 0, "refused": 0, "cancelled": 0, "sum_delivered": 0.0, "sum_total": 0.0,
               "buyout_rate": None, "first_at": None, "last_at": None}


def blacklisted(db: Session, phone: str) -> Customer | None:
    if not phone:
        return None
    return db.query(Customer).filter(Customer.phone == phone, Customer.is_blacklisted.is_(True)).one_or_none()
