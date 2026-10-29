"""Створення/видалення ТТН і синхронізація статусів доставки."""
from datetime import timedelta

from sqlalchemy.orm import Session

from ..carriers import CARRIERS, CarrierError, TrackResult, get_carrier
from ..models import Order, Status, User, utcnow
from . import audit, events, orders as order_svc, payments
from . import settings as st

FINAL_DELIVERY_STATES = {"delivered", "returned", "deleted"}

# Який статус замовлення ставити за станом посилки (якщо увімкнено автостатуси)
STATE_TO_STATUS = {
    "in_transit": "shipped",
    "arrived": "shipped",
    "created": None,
    "delivered": "delivered",
    "refused": "refused",
    "returned": "refused",
}
# Статуси, з яких дозволено автоматичний перехід у «Відправлено»
PRE_SHIP_CODES = {"new", "confirmed", "packing", "no_answer", "callback"}


def create_ttn(db: Session, order: Order, user: User | None) -> str:
    if order.ttn:
        raise CarrierError(f"У замовлення вже є ТТН {order.ttn}")
    if not order.items:
        raise CarrierError("Додайте товари в замовлення")
    carrier = get_carrier(order.delivery_method, st.get_all(db))
    if carrier is None:
        raise CarrierError("Для цього способу доставки ТТН не створюється")
    res = carrier.create_shipment(order)
    order.ttn, order.carrier_ref = res.ttn, res.ref
    if res.cost:
        order.delivery_cost = res.cost
    order.delivery_state, order.delivery_status = "created", "Створено ТТН"
    order.delivery_checked_at = utcnow()
    audit.log(db, user, "order", order.id, "ttn_create", {"ttn": res.ttn, "служба": carrier.name})
    events.order_changed(db, order.id)
    return res.ttn


def delete_ttn(db: Session, order: Order, user: User | None):
    if not order.ttn:
        return
    carrier = get_carrier(order.delivery_method, st.get_all(db))
    if carrier is not None and order.carrier_ref:
        carrier.delete_shipment(order)
    old = order.ttn
    order.ttn = order.carrier_ref = ""
    order.delivery_state = order.delivery_status = order.delivery_status_code = ""
    audit.log(db, user, "order", order.id, "ttn_delete", {"ttn": old})
    events.order_changed(db, order.id)


def apply_track(db: Session, order: Order, res: TrackResult, auto_status: bool) -> bool:
    order.delivery_checked_at = utcnow()
    if (order.delivery_state, order.delivery_status_code, order.delivery_status) == (
        res.state, res.code, res.status_text
    ):
        return False
    old = order.delivery_status
    order.delivery_state = res.state
    order.delivery_status = (res.status_text or "")[:255]
    order.delivery_status_code = (res.code or "")[:16]
    audit.log(db, None, "order", order.id, "tracking", {"з": old, "на": order.delivery_status})
    events.order_changed(db, order.id)
    payments.on_delivery_state(db, order, res.state)
    if res.state == "delivered":
        order.delivered_at = order.delivered_at or utcnow()

    if auto_status:
        target_code = STATE_TO_STATUS.get(res.state)
        current = order.status.code if order.status else ""
        allowed = False
        if target_code == "shipped":
            allowed = current in PRE_SHIP_CODES
        elif target_code == "delivered":
            allowed = current in PRE_SHIP_CODES | {"shipped"}
        elif target_code == "refused":
            allowed = current in PRE_SHIP_CODES | {"shipped"}
        if allowed:
            target = db.query(Status).filter(Status.code == target_code, Status.is_active.is_(True)).one_or_none()
            if target:
                order_svc.change_status(db, order, target, None, auto=True, reason=res.status_text)
    return True


def sync_tracking(db: Session, order_ids: list[int] | None = None, force: bool = False,
                  carrier: str | None = None) -> dict:
    """Оновлює статуси посилок. Без order_ids — всі активні ТТН, що давно не перевірялись."""
    settings = st.get_all(db)
    auto_status = settings.get("auto_status_from_tracking") == "1"
    q = db.query(Order).filter(Order.ttn != "", Order.delivery_method.in_(list(CARRIERS)))
    if carrier:
        q = q.filter(Order.delivery_method == carrier)
    if order_ids:
        q = q.filter(Order.id.in_(order_ids))
    else:
        q = q.filter((Order.delivery_state.is_(None)) | (~Order.delivery_state.in_(FINAL_DELIVERY_STATES)))
        q = q.filter(Order.created_at >= utcnow() - timedelta(days=60))
        if not force:
            interval = max(st.get_int(db, "tracking_interval_min", 60), 5)
            border = utcnow() - timedelta(minutes=interval)
            q = q.filter((Order.delivery_checked_at.is_(None)) | (Order.delivery_checked_at < border))
    orders = q.all()
    stats = {"checked": 0, "changed": 0, "errors": []}
    by_carrier: dict[str, list[Order]] = {}
    for o in orders:
        by_carrier.setdefault(o.delivery_method, []).append(o)
    for code, group in by_carrier.items():
        carrier = get_carrier(code, settings)
        if carrier is None or not carrier.configured():
            continue
        try:
            results = carrier.track(group)
        except CarrierError as e:
            stats["errors"].append(str(e))
            continue
        by_ttn = {r.ttn: r for r in results}
        for o in group:
            r = by_ttn.get(o.ttn)
            stats["checked"] += 1
            if r is None:
                o.delivery_checked_at = utcnow()
                continue
            if apply_track(db, o, r, auto_status):
                stats["changed"] += 1
    db.commit()
    return stats
