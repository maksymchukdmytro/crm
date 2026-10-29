"""Оплати: передоплати, накладені платежі та звірка грошей від перевізників."""
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from ..models import Order, Payment, Status, User, utcnow
from . import audit, events


def _cod_payments(order: Order) -> list[Payment]:
    return [p for p in order.payments if p.kind == "cod" and p.status != "cancelled"]


def ensure_cod_payment(db: Session, order: Order):
    """Створює (або оновлює суму) очікуваного накладеного платежу для відправленого замовлення."""
    if order.payment_type == "prepaid" or Decimal(order.cod_amount or 0) <= 0:
        return
    existing = _cod_payments(order)
    if existing:
        p = existing[0]
        if p.status == "expected" and Decimal(p.amount) != Decimal(order.cod_amount):
            p.amount = order.cod_amount
        return
    order.payments.append(
        Payment(kind="cod", amount=order.cod_amount, status="expected", method=order.delivery_method)
    )


def mark_collected(order: Order):
    for p in _cod_payments(order):
        if p.status == "expected":
            p.status = "collected"
            p.collected_at = utcnow()


def cancel_expected(order: Order):
    for p in _cod_payments(order):
        if p.status in ("expected", "collected"):
            p.status = "cancelled"


def on_status(db: Session, order: Order, status: Status):
    if status.stock_action == "ship" and order.stock_shipped:
        ensure_cod_payment(db, order)
    if status.code == "delivered":
        ensure_cod_payment(db, order)
        mark_collected(order)
    elif status.code in ("refused", "returned", "cancelled"):
        cancel_expected(order)


def on_delivery_state(db: Session, order: Order, state: str):
    if state == "delivered":
        ensure_cod_payment(db, order)
        mark_collected(order)
    elif state in ("refused", "returned"):
        cancel_expected(order)


def mark_received(db: Session, payment: Payment, user: User | None, amount: Decimal | None = None, reference: str = ""):
    payment.status = "received"
    payment.received_at = utcnow()
    payment.received_amount = amount if amount is not None else payment.amount
    if reference:
        payment.reference = reference
    events.order_changed(db, payment.order_id)
    audit.log(db, user, "order", payment.order_id, "payment",
              {"payment_id": payment.id, "status": "received", "amount": payment.received_amount})


def parse_amount(raw: str) -> Decimal | None:
    raw = (raw or "").replace("\xa0", "").replace(" ", "").replace(",", ".")
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


def import_registry(db: Session, rows: list[dict], user: User | None) -> dict:
    """Звірка реєстру грошових переказів (CSV від перевізника чи банку).

    rows: [{"ttn": "...", "amount": "...", "reference": "..."}]
    Повертає звіт: зараховані, розбіжності суми, не знайдені ТТН, вже зараховані.
    """
    report = {"matched": [], "mismatch": [], "not_found": [], "already": []}
    for r in rows:
        ttn = "".join(ch for ch in str(r.get("ttn", "")) if ch.isalnum())
        amount = parse_amount(str(r.get("amount", "")))
        if not ttn:
            continue
        order = db.query(Order).filter(Order.ttn == ttn).first()
        if order is None:
            report["not_found"].append({"ttn": ttn, "amount": amount})
            continue
        cod = [p for p in order.payments if p.kind == "cod"]
        pending = [p for p in cod if p.status in ("expected", "collected")]
        if not pending:
            if any(p.status == "received" for p in cod):
                report["already"].append({"ttn": ttn, "order_id": order.id, "amount": amount})
                continue
            ensure_cod_payment(db, order)
            db.flush()
            pending = [p for p in order.payments if p.kind == "cod" and p.status == "expected"]
            if not pending:
                report["not_found"].append({"ttn": ttn, "amount": amount, "order_id": order.id})
                continue
        p = pending[0]
        expected = Decimal(p.amount)
        mark_received(db, p, user, amount if amount is not None else expected, str(r.get("reference", "")))
        row = {"ttn": ttn, "order_id": order.id, "expected": expected, "amount": amount}
        if amount is not None and abs(amount - expected) > Decimal("0.01"):
            report["mismatch"].append(row)
        else:
            report["matched"].append(row)
    return report
