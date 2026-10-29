"""Складський облік: резерви, списання, повернення, оприбуткування.

Кожна зміна залишку записується в stock_movements, тому історію руху
товару завжди можна переглянути і звірити. Якщо в товару є варіанти
(колір, розмір…), залишок ведеться і по варіанту, і загалом по товару:
залишок товару = сума залишків варіантів (плюс позиції без варіанта).
"""
from collections import defaultdict
from decimal import Decimal

from sqlalchemy.orm import Session

from ..models import Order, Product, ProductVariant, Purchase, StockMovement, User, utcnow
from . import events


def _lock(db: Session, product_id: int) -> Product | None:
    return (
        db.query(Product)
        .filter(Product.id == product_id)
        .with_for_update()
        .populate_existing()
        .one_or_none()
    )


def move(
    db: Session,
    product_id: int,
    kind: str,
    stock_delta: int = 0,
    reserved_delta: int = 0,
    *,
    order: Order | None = None,
    purchase: Purchase | None = None,
    user: User | None = None,
    comment: str = "",
    variant_id: int | None = None,
):
    if not stock_delta and not reserved_delta:
        return
    p = _lock(db, product_id)
    if p is None:
        return
    events.product_changed(db, product_id)
    p.stock = (p.stock or 0) + stock_delta
    p.reserved = max((p.reserved or 0) + reserved_delta, 0)
    if variant_id:
        v = (db.query(ProductVariant).filter(ProductVariant.id == variant_id, ProductVariant.product_id == product_id)
             .with_for_update().populate_existing().one_or_none())
        if v is None:
            variant_id = None
        else:
            v.stock = (v.stock or 0) + stock_delta
            v.reserved = max((v.reserved or 0) + reserved_delta, 0)
    db.add(
        StockMovement(
            product_id=product_id,
            variant_id=variant_id,
            kind=kind,
            stock_delta=stock_delta,
            reserved_delta=reserved_delta,
            order_id=order.id if order else None,
            purchase_id=purchase.id if purchase else None,
            user_id=user.id if user else None,
            comment=comment,
        )
    )


def _qty_by_product(items) -> dict[tuple[int, int | None], int]:
    """Кількість за (товар, варіант). Елементи — позиції замовлення або кортежі (товар, кількість[, варіант])."""
    res: dict[tuple[int, int | None], int] = defaultdict(int)
    for it in items:
        if isinstance(it, tuple):
            pid, qty, vid = it[0], it[1], (it[2] if len(it) > 2 else None)
        else:
            pid, qty, vid = it.product_id, it.qty, getattr(it, "variant_id", None)
        if pid:
            res[(pid, vid or None)] += int(qty or 0)
    return res


def reserve(db: Session, order: Order, user: User | None = None):
    if order.stock_reserved or order.stock_shipped:
        return
    for (pid, vid), qty in _qty_by_product(order.items).items():
        move(db, pid, "reserve", 0, qty, order=order, user=user, variant_id=vid)
    order.stock_reserved = True


def release(db: Session, order: Order, user: User | None = None):
    if not order.stock_reserved or order.stock_shipped:
        return
    for (pid, vid), qty in _qty_by_product(order.items).items():
        move(db, pid, "unreserve", 0, -qty, order=order, user=user, variant_id=vid)
    order.stock_reserved = False


def ship(db: Session, order: Order, user: User | None = None):
    if order.stock_shipped:
        return
    for (pid, vid), qty in _qty_by_product(order.items).items():
        move(db, pid, "ship", -qty, -qty if order.stock_reserved else 0, order=order, user=user, variant_id=vid)
    order.stock_reserved = False
    order.stock_shipped = True
    order.shipped_at = order.shipped_at or utcnow()


def return_to_stock(db: Session, order: Order, user: User | None = None):
    if not order.stock_shipped:
        return
    for (pid, vid), qty in _qty_by_product(order.items).items():
        move(db, pid, "return", qty, 0, order=order, user=user, variant_id=vid)
    order.stock_shipped = False


def apply_action(db: Session, order: Order, action: str, user: User | None = None):
    if action == "reserve":
        reserve(db, order, user)
    elif action == "ship":
        ship(db, order, user)
    elif action == "return":
        return_to_stock(db, order, user)
    elif action == "release":
        release(db, order, user)


def on_items_changed(db: Session, order: Order, old_items: list[tuple], user: User | None = None):
    """Коригує резерв/списання, якщо товари змінили вже після резервування чи відправки."""
    if not (order.stock_reserved or order.stock_shipped):
        return
    old = _qty_by_product(old_items)
    new = _qty_by_product(order.items)
    for key in set(old) | set(new):
        delta = new.get(key, 0) - old.get(key, 0)
        if not delta:
            continue
        pid, vid = key
        if order.stock_shipped:
            move(db, pid, "ship", -delta, 0, order=order, user=user, comment="зміна складу замовлення", variant_id=vid)
        else:
            move(db, pid, "reserve" if delta > 0 else "unreserve", 0, delta, order=order, user=user,
                 comment="зміна складу замовлення", variant_id=vid)


def receive_purchase(db: Session, purchase: Purchase, user: User | None = None):
    """Оприбуткування закупівлі: збільшує залишки і перераховує середню собівартість."""
    if purchase.status == "received":
        return
    for it in purchase.items:
        p = _lock(db, it.product_id)
        if p is None:
            continue
        old_qty = max(p.stock or 0, 0)
        new_cost = Decimal(it.cost or 0)
        if old_qty + it.qty > 0 and new_cost > 0:
            avg = (Decimal(p.cost or 0) * old_qty + new_cost * it.qty) / (old_qty + it.qty)
            p.cost = avg.quantize(Decimal("0.01"))
        move(db, it.product_id, "purchase", it.qty, 0, purchase=purchase, user=user, variant_id=it.variant_id)
    purchase.status = "received"
    purchase.received_at = utcnow()


def adjust(db: Session, product: Product, new_stock: int, user: User | None, comment: str,
           variant: ProductVariant | None = None):
    current = (variant.stock if variant is not None else product.stock) or 0
    delta = int(new_stock) - current
    move(db, product.id, "adjust", delta, 0, user=user, comment=comment or "інвентаризація",
         variant_id=variant.id if variant is not None else None)
