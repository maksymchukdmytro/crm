"""Бізнес-логіка замовлень: створення, товари, статуси, дублі, розподіл між менеджерами."""
import re
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from ..models import Order, OrderComment, OrderItem, Product, Status, User, utcnow
from . import audit, payments, sms, stock
from . import settings as st

ORDER_FIELDS = [
    "customer_name", "phone", "email", "comment",
    "delivery_method", "city_name", "city_ref", "warehouse_name", "warehouse_ref", "address", "postcode",
    "ttn", "delivery_cost", "payment_type", "prepayment", "discount",
    "site", "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term",
]
MONEY_FIELDS = {"delivery_cost", "prepayment", "discount"}


def normalize_phone(raw: str | None) -> str:
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 10 and digits.startswith("0"):
        digits = "38" + digits
    elif len(digits) == 9:
        digits = "380" + digits
    elif len(digits) == 11 and digits.startswith("80"):
        digits = "3" + digits
    return digits


def to_money(v) -> Decimal:
    if v is None or v == "":
        return Decimal(0)
    try:
        return Decimal(str(v).replace(",", ".").replace(" ", "")).quantize(Decimal("0.01"))
    except InvalidOperation:
        return Decimal(0)


def to_int(v, default: int = 0) -> int:
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return default


def status_by_code(db: Session, code: str) -> Status | None:
    return db.query(Status).filter(Status.code == code).one_or_none()


def recalc(order: Order):
    subtotal = sum((Decimal(i.price or 0) * i.qty for i in order.items), Decimal(0))
    order.total = max(subtotal - Decimal(order.discount or 0), Decimal(0))
    if order.payment_type == "prepaid":
        order.cod_amount = Decimal(0)
    else:
        order.cod_amount = max(order.total - Decimal(order.prepayment or 0), Decimal(0))


def find_duplicate(db: Session, phone: str, exclude_id: int | None = None) -> Order | None:
    days = st.get_int(db, "duplicate_days", 14)
    if not phone or days <= 0:
        return None
    q = db.query(Order).filter(Order.phone == phone, Order.created_at >= utcnow() - timedelta(days=days))
    if exclude_id:
        q = q.filter(Order.id != exclude_id)
    return q.order_by(Order.id.desc()).first()


def customer_orders(db: Session, phone: str, exclude_id: int | None = None, limit: int = 20) -> list[Order]:
    if not phone:
        return []
    q = db.query(Order).filter(Order.phone == phone)
    if exclude_id:
        q = q.filter(Order.id != exclude_id)
    return q.order_by(Order.id.desc()).limit(limit).all()


def pick_manager_round_robin(db: Session) -> User | None:
    managers = (
        db.query(User).filter(User.role == "manager", User.is_active.is_(True)).order_by(User.id).all()
    )
    if not managers:
        return None
    last = st.get_int(db, "rr_last_manager_id", 0)
    nxt = next((m for m in managers if m.id > last), managers[0])
    st.set_value(db, "rr_last_manager_id", str(nxt.id))
    return nxt


def build_items(db: Session, items_data: list[dict]) -> list[OrderItem]:
    result = []
    for d in items_data:
        qty = to_int(d.get("qty"), 1)
        if qty <= 0:
            continue
        product = None
        pid = to_int(d.get("product_id"), 0)
        if pid:
            product = db.get(Product, pid)
        elif d.get("sku"):
            product = db.query(Product).filter(Product.sku == str(d["sku"]).strip()).one_or_none()
        name = (d.get("name") or "").strip() or (product.name if product else "")
        if not name:
            continue
        price = d.get("price")
        price = to_money(price) if price not in (None, "") else (Decimal(product.price) if product else Decimal(0))
        is_upsell = str(d.get("is_upsell", "")).lower() in ("1", "true", "on", "yes")
        result.append(
            OrderItem(
                product_id=product.id if product else None,
                name=name,
                price=price,
                cost=Decimal(product.cost) if product else Decimal(0),
                qty=qty,
                is_upsell=is_upsell,
            )
        )
    return result


def _clean_fields(data: dict) -> dict:
    clean = {}
    for f in ORDER_FIELDS:
        if f not in data:
            continue
        v = data[f]
        if f in MONEY_FIELDS:
            v = to_money(v)
        elif f == "phone":
            v = normalize_phone(v)
        elif f == "ttn":
            v = re.sub(r"\s", "", str(v or ""))
        else:
            v = (str(v) if v is not None else "").strip()[:255] if f != "comment" else str(v or "").strip()
        clean[f] = v
    return clean


def create_order(db: Session, data: dict, items_data: list[dict], user: User | None = None,
                 source: str = "manual") -> Order:
    new_status = status_by_code(db, "new") or db.query(Status).order_by(Status.sort).first()
    fields = _clean_fields(data)
    order = Order(status=new_status, **fields)
    order.ip = (data.get("ip") or "")[:64]
    if source == "webhook" and not order.delivery_method:
        order.delivery_method = "novaposhta"
    order.delivery_method = order.delivery_method or "novaposhta"
    order.payment_type = order.payment_type or "cod"

    dup = find_duplicate(db, order.phone)
    if dup:
        order.duplicate_of_id = dup.id

    if user and user.role == "manager":
        order.manager = user
    elif st.get(db, "auto_assign") == "round_robin":
        order.manager = pick_manager_round_robin(db)
    if data.get("manager_id") and user and user.role == "admin":
        order.manager_id = to_int(data["manager_id"]) or None

    order.items = build_items(db, items_data)
    recalc(order)
    db.add(order)
    db.flush()
    audit.log(db, user, "order", order.id, "create", {
        "source": source,
        "items": [f"{i.name} × {i.qty}" for i in order.items],
        "duplicate_of": order.duplicate_of_id,
    })
    return order


def update_order(db: Session, order: Order, data: dict, user: User | None) -> dict:
    fields = _clean_fields(data)
    changes = audit.diff(order, fields, list(fields))
    if "phone" in changes:
        dup = find_duplicate(db, order.phone, exclude_id=order.id)
        order.duplicate_of_id = dup.id if dup and dup.id < order.id else None
    recalc(order)
    if order.stock_shipped:
        payments.ensure_cod_payment(db, order)
    if changes:
        audit.log(db, user, "order", order.id, "update", changes)
    return changes


def set_items(db: Session, order: Order, items_data: list[dict], user: User | None):
    old_items = [(i.product_id, i.qty) for i in order.items]
    old_desc = [f"{i.name} × {i.qty} = {i.price}" for i in order.items]
    order.items.clear()
    db.flush()
    order.items.extend(build_items(db, items_data))
    recalc(order)
    stock.on_items_changed(db, order, old_items, user)
    if order.stock_shipped:
        payments.ensure_cod_payment(db, order)
    new_desc = [f"{i.name} × {i.qty} = {i.price}" for i in order.items]
    if old_desc != new_desc:
        audit.log(db, user, "order", order.id, "items", {"було": old_desc, "стало": new_desc})


def change_status(db: Session, order: Order, new_status: Status, user: User | None,
                  auto: bool = False, reason: str = "") -> bool:
    if order.status_id == new_status.id:
        return False
    old_name = order.status.name if order.status else ""
    order.status = new_status
    order.status_id = new_status.id
    order.status_changed_at = utcnow()
    stock.apply_action(db, order, new_status.stock_action, user)
    if new_status.code == "delivered":
        order.delivered_at = order.delivered_at or utcnow()
    payments.on_status(db, order, new_status)
    details = {"з": old_name, "на": new_status.name}
    if auto:
        details["авто"] = reason or "трекінг"
    audit.log(db, user, "order", order.id, "status", details)
    db.flush()
    sms.queue_for_status(db, order, new_status)
    return True


def assign(db: Session, order: Order, manager: User | None, user: User | None):
    if order.manager_id == (manager.id if manager else None):
        return
    old = order.manager.display if order.manager else "—"
    order.manager = manager
    order.manager_id = manager.id if manager else None
    audit.log(db, user, "order", order.id, "assign", {"з": old, "на": manager.display if manager else "—"})


def add_comment(db: Session, order: Order, text: str, user: User | None) -> OrderComment | None:
    text = (text or "").strip()
    if not text:
        return None
    c = OrderComment(order=order, user=user, text=text)
    db.add(c)
    return c


def visible_orders_query(db: Session, user: User):
    q = db.query(Order)
    if user.role == "manager" and st.get_bool(db, "managers_see_own_only"):
        q = q.filter((Order.manager_id == user.id) | (Order.manager_id.is_(None)))
    return q


def can_view(db: Session, user: User, order: Order) -> bool:
    if user.role == "manager" and st.get_bool(db, "managers_see_own_only"):
        return order.manager_id in (None, user.id)
    return True
