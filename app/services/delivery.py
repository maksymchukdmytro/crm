"""Створення/видалення ТТН і синхронізація статусів доставки."""
from datetime import timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from ..carriers import CARRIERS, CarrierError, TrackResult, get_carrier
from ..models import Order, Status, User, utcnow
from . import audit, events, np as np_svc, orders as order_svc, pay_check, payments
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


def carrier_for(db: Session, order: Order):
    """Перевізник для замовлення; для Нової Пошти — з ключем (ФОП), вибраним у замовленні чи за відділом."""
    return get_carrier(order.delivery_method, np_svc.carrier_settings(db, order))


def create_ttn(db: Session, order: Order, user: User | None, opts: dict | None = None) -> str:
    if order.ttn:
        raise CarrierError(f"У замовлення вже є ТТН {order.ttn}")
    if not order.items:
        raise CarrierError("Додайте товари в замовлення")
    if opts and opts.get("np_account_id") and order.delivery_method == "novaposhta":
        order.np_account_id = int(opts["np_account_id"])
    carrier = carrier_for(db, order)
    if carrier is None:
        raise CarrierError("Для цього способу доставки ТТН не створюється")
    if order.payment_method and order.payment_method.kind == "prepaid":
        opts = {**(opts or {}), "cod_mode": "none", "cod_amount": 0}  # вид оплати виключає післяплату
    res = carrier.create_shipment(order, opts)
    if order.delivery_method == "novaposhta" and carrier.s.get("np_account_id"):
        order.np_account_id = int(carrier.s["np_account_id"])
    order.ttn, order.carrier_ref = res.ttn, res.ref
    order.ttn_cod_kind, order.ttn_cod_sum = res.cod_kind, res.cod_sum
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
    carrier = carrier_for(db, order)
    if carrier is not None and order.carrier_ref:
        carrier.delete_shipment(order)
    old = order.ttn
    order.ttn = order.carrier_ref = ""
    order.ttn_cod_kind, order.ttn_cod_sum = "", Decimal(0)
    order.delivery_state = order.delivery_status = order.delivery_status_code = ""
    audit.log(db, user, "order", order.id, "ttn_delete", {"ttn": old})
    events.order_changed(db, order.id)


def apply_track(db: Session, order: Order, res: TrackResult, auto_status: bool) -> bool:
    order.delivery_checked_at = utcnow()
    if order.delivery_method == "novaposhta":
        cod = pay_check.cod_from_np(res.raw)
        if cod is not None and cod != (order.ttn_cod_kind, Decimal(order.ttn_cod_sum or 0)):
            order.ttn_cod_kind, order.ttn_cod_sum = cod
            events.order_changed(db, order.id)
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

    rules = np_svc.rules(db) if order.delivery_method == "novaposhta" else []
    if rules:  # налаштовані правила «статус ТТН → статус замовлення» мають перевагу над стандартною логікою
        rule = next((r for r in rules if r.np_code == str(res.code)), None)
        if rule and order.status_id != rule.status_id and order.status_id not in [int(x) for x in rule.except_ids or []]:
            target = db.get(Status, rule.status_id)
            if target is not None and target.is_active:
                order_svc.change_status(db, order, target, None, auto=True, reason=res.status_text)
        return True
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
    by_carrier: dict[tuple, list[Order]] = {}
    accs = {a.id: a for a in np_svc.accounts(db, active_only=False)}
    for o in orders:
        acc = (o.np_account_id if o.np_account_id in accs else None) if o.delivery_method == "novaposhta" else None
        by_carrier.setdefault((o.delivery_method, acc), []).append(o)
    for (code, acc_id), group in by_carrier.items():
        cs = settings
        if code == "novaposhta":
            cs = np_svc.account_settings(settings, accs.get(acc_id) if acc_id else np_svc.pick_account(db))
        carrier = get_carrier(code, cs)
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
