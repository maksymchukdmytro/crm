"""Бізнес-логіка замовлень: створення, товари, статуси, дублі, розподіл між менеджерами."""
import re
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from ..models import COUNTRIES, Office, Order, OrderComment, OrderItem, OrderMark, OrderSource, PaymentMethod, Product, ProductVariant, Status, StatusReason, User, utcnow
from . import audit, customers, events, payments, sms, stock
from . import settings as st
from .names import join_name, split_full_name

NAME_PARTS = ("last_name", "first_name", "middle_name")
ORDER_FIELDS = [
    "customer_name", *NAME_PARTS, "phone", "email", "comment", "country",
    "office_id", "np_account_id", "legal_entity_id", "reason_id", "mark_id", "remind_at",
    "delivery_method", "city_name", "city_ref", "warehouse_name", "warehouse_ref", "address", "postcode",
    "ttn", "delivery_cost", "payment_type", "payment_method_id", "prepayment", "discount",
    "source_id", "extra1", "extra2", "extra3", "extra4", "site", "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term",
]
MONEY_FIELDS = {"delivery_cost", "prepayment", "discount"}
ID_FIELDS = {"payment_method_id", "source_id", "office_id", "np_account_id", "legal_entity_id", "reason_id", "mark_id"}


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
        variant = None
        pid = to_int(d.get("product_id"), 0)
        vid = to_int(d.get("variant_id"), 0)
        if vid:
            variant = db.get(ProductVariant, vid)
            if variant is not None and pid and variant.product_id != pid:
                variant = None
        if pid:
            product = db.get(Product, pid)
        elif variant is not None:
            product = variant.product
        elif d.get("sku"):
            sku = str(d["sku"]).strip()
            product = db.query(Product).filter(Product.sku == sku).one_or_none()
            if product is None:  # артикул варіанта
                variant = db.query(ProductVariant).filter(ProductVariant.sku == sku).one_or_none()
                product = variant.product if variant is not None else None
        if product is not None and variant is None and product.variants and vid:
            variant = next((v for v in product.variants if v.id == vid), None)
        name = (d.get("name") or "").strip()
        if not name and product is not None:
            name = f"{product.name} ({variant.name})" if variant is not None and variant.name else product.name
        if not name:
            continue
        price = d.get("price")
        if price not in (None, ""):
            price = to_money(price)
        elif variant is not None and variant.price is not None:
            price = Decimal(variant.price)
        else:
            price = product.sale_price if product is not None else Decimal(0)
        is_upsell = str(d.get("is_upsell", "")).lower() in ("1", "true", "on", "yes")
        upsell_for = to_int(d.get("upsell_for"), 0) if is_upsell else 0
        result.append(
            OrderItem(
                product_id=product.id if product else None,
                variant_id=variant.id if variant is not None else None,
                name=name,
                price=price,
                cost=Decimal(product.cost) if product else Decimal(0),
                qty=qty,
                is_upsell=is_upsell,
                upsell_for_id=upsell_for or None,
            )
        )
    return result


def _names(data: dict, order: Order | None) -> dict:
    """ПІБ: окремі поля мають перевагу; один рядок (з лендингу, старі клієнти API) розбираємо самі."""
    if any(k in data for k in NAME_PARTS):
        parts = {k: (str(data[k]) if data.get(k) is not None else "").strip()[:100] if k in data
                 else (getattr(order, k, "") if order else "") or "" for k in NAME_PARTS}
    elif "customer_name" in data:
        last, first, middle = split_full_name(str(data.get("customer_name") or ""))
        parts = {"last_name": last[:100], "first_name": first[:100], "middle_name": middle[:100]}
    else:
        return {}
    parts["customer_name"] = join_name(parts["last_name"], parts["first_name"], parts["middle_name"])[:255]
    return parts


def _clean_fields(data: dict, order: Order | None = None) -> dict:
    clean = _names(data, order)
    for f in ORDER_FIELDS:
        if f not in data or f in clean:
            continue
        v = data[f]
        if f in MONEY_FIELDS:
            v = to_money(v)
        elif f in ID_FIELDS:
            v = to_int(v, 0) or None
        elif f == "remind_at":
            v = parse_dt(v)
        elif f == "country":
            v = str(v or "UA").strip().upper()[:2]
            v = v if v in COUNTRIES else "UA"
        elif f == "phone":
            v = normalize_phone(v)
        elif f == "ttn":
            v = re.sub(r"\s", "", str(v or ""))
        else:
            v = (str(v) if v is not None else "").strip()[:255] if f != "comment" else str(v or "").strip()
        clean[f] = v
    return clean


def parse_dt(v):
    """ISO-дата з інтерфейсу (з часовим поясом або без) → UTC без поясу, як усі дати в базі; порожньо → None."""
    from datetime import datetime, timezone
    if not v:
        return None
    try:
        d = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        return None
    return d.astimezone(timezone.utc).replace(tzinfo=None) if d.tzinfo else d


def _apply_directories(db: Session, fields: dict):
    """Вид оплати визначає розрахунок (payment_type); невідомі id довідників — відкидаємо."""
    if fields.get("payment_method_id"):
        m = db.get(PaymentMethod, fields["payment_method_id"])
        if m is None:
            fields["payment_method_id"] = None
        else:
            fields["payment_type"] = m.kind
    from ..models import LegalEntity, NpAccount
    for key, model in (("source_id", OrderSource), ("office_id", Office), ("reason_id", StatusReason),
                       ("mark_id", OrderMark), ("np_account_id", NpAccount), ("legal_entity_id", LegalEntity)):
        if fields.get(key) and db.get(model, fields[key]) is None:
            fields[key] = None
    if fields.get("source_id"):  # відділ визначається джерелом
        src = db.get(OrderSource, fields["source_id"])
        if src is not None and src.office_id:
            fields["office_id"] = src.office_id


def create_order(db: Session, data: dict, items_data: list[dict], user: User | None = None,
                 source: str = "manual") -> Order:
    new_status = status_by_code(db, "new") or db.query(Status).order_by(Status.sort).first()
    fields = _clean_fields(data)
    _apply_directories(db, fields)
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
    customers.attach(db, order)
    db.flush()
    events.order_changed(db, order.id)
    audit.log(db, user, "order", order.id, "create", {
        "source": source,
        "items": [f"{i.name} × {i.qty}" for i in order.items],
        "duplicate_of": order.duplicate_of_id,
    })
    return order


def update_order(db: Session, order: Order, data: dict, user: User | None) -> dict:
    fields = _clean_fields(data, order)
    _apply_directories(db, fields)
    changes = audit.diff(order, fields, list(fields))
    if "phone" in changes:
        dup = find_duplicate(db, order.phone, exclude_id=order.id)
        order.duplicate_of_id = dup.id if dup and dup.id < order.id else None
    if changes.keys() & {"phone", "customer_name", "last_name", "first_name", "middle_name", "email"}:
        customers.attach(db, order)
    recalc(order)
    if order.stock_shipped:
        payments.ensure_cod_payment(db, order)
    if changes:
        audit.log(db, user, "order", order.id, "update", changes)
        events.order_changed(db, order.id)
    return changes


def set_items(db: Session, order: Order, items_data: list[dict], user: User | None):
    old_items = [(i.product_id, i.qty, i.variant_id) for i in order.items]
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
        events.order_changed(db, order.id)


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
    events.order_changed(db, order.id)
    db.flush()
    sms.queue_for_status(db, order, new_status)
    if order.shop_id and order.external_id:  # передати статус на маркетплейс (через чергу, без неї — одразу)
        _push_marketplace(db, order)
    try:  # автоматичні чеки Checkbox за статусом
        from .checkbox import CheckboxError, on_status
        on_status(db, order)
    except CheckboxError:
        pass
    return True


def _push_marketplace(db: Session, order: Order):
    from . import queue
    from .events import after_commit

    if queue.available():
        oid = order.id
        after_commit(db, f"mp_push:{oid}", lambda: queue.enqueue("marketplace_push", oid, job_id=f"mp:{oid}:{utcnow().timestamp()}"))
    else:
        from .marketplaces import push_status
        push_status(db, order)


def assign(db: Session, order: Order, manager: User | None, user: User | None):
    if order.manager_id == (manager.id if manager else None):
        return
    old = order.manager.display if order.manager else "—"
    order.manager = manager
    order.manager_id = manager.id if manager else None
    audit.log(db, user, "order", order.id, "assign", {"з": old, "на": manager.display if manager else "—"})
    events.order_changed(db, order.id)


def add_comment(db: Session, order: Order, text: str, user: User | None) -> OrderComment | None:
    text = (text or "").strip()
    if not text:
        return None
    c = OrderComment(order=order, user=user, text=text)
    db.add(c)
    events.order_changed(db, order.id)
    return c


def visible_orders_query(db: Session, user: User):
    q = db.query(Order)
    if user.role == "manager" and st.get_bool(db, "managers_see_own_only"):
        q = q.filter((Order.manager_id == user.id) | (Order.manager_id.is_(None)))
    if user.role != "admin" and user.offices:  # доступ лише до своїх відділів (замовлення без відділу — усім)
        q = q.filter(Order.office_id.is_(None) | Order.office_id.in_([int(x) for x in user.offices]))
    return q


def can_view(db: Session, user: User, order: Order) -> bool:
    if user.role == "manager" and st.get_bool(db, "managers_see_own_only") and order.manager_id not in (None, user.id):
        return False
    if user.role != "admin" and user.offices and order.office_id is not None:
        return order.office_id in [int(x) for x in user.offices]
    return True
