"""API: товари, склад, закупівлі, постачальники."""
from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..models import OrderItem, Product, Purchase, PurchaseItem, StockMovement, Supplier, User
from ..services import audit, stock
from ..services.orders import to_int, to_money
from .schemas import AdjustIn, ProductDetailOut, ProductIn, ProductOut, PurchaseIn, PurchaseOut, SupplierIn, SupplierOut, WarehouseOut
from .common import bad, iso, j_product, j_purchase, staff, stock_team

router = APIRouter(prefix="/api", tags=["catalog"])
KINDS = {"purchase": "Закупівля", "reserve": "Резерв", "unreserve": "Зняття резерву", "ship": "Відправка",
         "return": "Повернення", "adjust": "Коригування"}


def j_move(m: StockMovement) -> dict:
    return {"id": m.id, "product_id": m.product_id, "product": m.product.name if m.product else "",
            "kind": m.kind, "kind_name": KINDS.get(m.kind, m.kind), "stock_delta": m.stock_delta,
            "reserved_delta": m.reserved_delta, "order_id": m.order_id, "purchase_id": m.purchase_id,
            "user": m.user.display if m.user else "Система", "comment": m.comment, "created_at": iso(m.created_at)}


def _apply_product(p: Product, d: dict):
    if "name" in d:
        p.name = str(d["name"]).strip()[:255]
    if "sku" in d:
        p.sku = str(d["sku"] or "").strip()[:64] or None
    for f in ("price", "cost"):
        if f in d:
            setattr(p, f, to_money(d[f]))
    if "weight" in d:
        p.weight = to_money(d["weight"]) or Decimal("0.5")
    if "min_stock" in d:
        p.min_stock = to_int(d["min_stock"], 0)
    for f in ("length", "width", "height"):
        if f in d and d[f] is not None:
            setattr(p, f, Decimal(str(d[f])).quantize(Decimal("0.1")))
    if "ship_description" in d and d["ship_description"] is not None:
        p.ship_description = str(d["ship_description"]).strip()[:255]
    if "upsell" in d:
        p.is_upsell = bool(d["upsell"])
    if "upsell_for" in d:
        ids = d["upsell_for"] or []
        p.upsell_for = sorted({int(x) for x in ids if str(x).isdigit() and int(x) != p.id})
    if "active" in d:
        p.is_active = bool(d["active"])


# ---------------------------------------------------------------- товари
@router.get("/products", response_model=list[ProductOut])
def products(q: str = "", show: str = "active", db: Session = Depends(get_db), user: User = Depends(staff)):
    query = db.query(Product)
    if show == "active":
        query = query.filter(Product.is_active.is_(True))
    elif show == "inactive":
        query = query.filter(Product.is_active.is_(False))
    if q:
        query = query.filter(or_(Product.name.ilike(f"%{q}%"), Product.sku.ilike(f"%{q}%")))
    return [j_product(p) for p in query.order_by(Product.is_upsell, Product.name).all()]


@router.get("/products/{pid}", response_model=ProductDetailOut)
def product(pid: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    p = db.get(Product, pid)
    if p is None:
        raise HTTPException(404, "Товар не знайдено")
    moves = (db.query(StockMovement).options(selectinload(StockMovement.user))
             .filter(StockMovement.product_id == pid).order_by(StockMovement.id.desc()).limit(100).all())
    d = j_product(p)
    d["moves"] = [j_move(m) for m in moves]
    d["sold"] = db.query(OrderItem).filter(OrderItem.product_id == pid).count()
    return d


@router.post("/products", response_model=ProductOut)
def product_create(body: ProductIn, db: Session = Depends(get_db), user: User = Depends(stock_team)):
    data = body.model_dump(exclude_unset=True)
    p = Product(stock=0, reserved=0, price=0, cost=0, weight=Decimal("0.5"), min_stock=0, is_upsell=False,
                is_active=True)
    _apply_product(p, data)
    if not p.name:
        bad("Вкажіть назву товару")
    db.add(p)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        bad("Товар з таким артикулом вже існує", 409)
    initial = to_int(data.get("initial_stock"), 0)
    if initial:
        stock.move(db, p.id, "adjust", initial, 0, user=user, comment="початковий залишок")
    audit.log(db, user, "product", p.id, "create", {"назва": p.name, "ціна": p.price})
    db.commit()
    return j_product(p)


@router.patch("/products/{pid}", response_model=ProductOut)
def product_update(pid: int, body: ProductIn, db: Session = Depends(get_db), user: User = Depends(stock_team)):
    data = body.model_dump(exclude_unset=True)
    p = db.get(Product, pid)
    if p is None:
        raise HTTPException(404, "Товар не знайдено")
    before = {"назва": p.name, "ціна": str(p.price), "собівартість": str(p.cost)}
    _apply_product(p, data)
    if not p.name:
        bad("Вкажіть назву товару")
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        bad("Товар з таким артикулом вже існує", 409)
    after = {"назва": p.name, "ціна": str(p.price), "собівартість": str(p.cost)}
    changes = {k: [before[k], after[k]] for k in before if before[k] != after[k]}
    if changes:
        audit.log(db, user, "product", p.id, "update", changes)
    from ..services import events
    events.product_changed(db, p.id)
    db.commit()
    return j_product(p)


# ---------------------------------------------------------------- склад
@router.get("/warehouse", response_model=WarehouseOut)
def warehouse(product: int = 0, kind: str = "", db: Session = Depends(get_db), user: User = Depends(stock_team)):
    products = db.query(Product).filter(Product.is_active.is_(True)).order_by(Product.name).all()
    mq = db.query(StockMovement).options(selectinload(StockMovement.product), selectinload(StockMovement.user))
    if product:
        mq = mq.filter(StockMovement.product_id == product)
    if kind:
        mq = mq.filter(StockMovement.kind == kind)
    return {
        "products": [j_product(p) for p in products],
        "value": float(sum((Decimal(p.cost or 0) * max(p.stock, 0) for p in products), Decimal(0))),
        "units": sum(max(p.stock, 0) for p in products),
        "reserved": sum(p.reserved for p in products),
        "low": sum(1 for p in products if p.available <= p.min_stock),
        "moves": [j_move(m) for m in mq.order_by(StockMovement.id.desc()).limit(150).all()],
        "kinds": KINDS,
    }


@router.post("/warehouse/adjust", response_model=ProductOut)
def adjust(body: AdjustIn, db: Session = Depends(get_db), user: User = Depends(stock_team)):
    data = body.model_dump(exclude_unset=True)
    p = db.get(Product, to_int(data.get("product_id")))
    if p is None:
        raise HTTPException(404, "Товар не знайдено")
    raw = str(data.get("qty", "")).strip()
    if not raw.lstrip("+-").isdigit():
        bad("Вкажіть кількість")
    comment = str(data.get("comment") or "").strip()[:255]
    old = p.stock
    if data.get("mode", "set") == "set":
        stock.adjust(db, p, int(raw), user, comment or "інвентаризація")
    else:
        stock.move(db, p.id, "adjust", int(raw), 0, user=user, comment=comment or "коригування")
    db.flush()
    audit.log(db, user, "product", p.id, "adjust", {"було": old, "стало": p.stock, "коментар": comment})
    db.commit()
    return j_product(p)


# ---------------------------------------------------------------- закупівлі
def _purchase_from(db: Session, p: Purchase, data: dict):
    if "supplier_id" in data:
        p.supplier_id = to_int(data.get("supplier_id")) or None
    if "comment" in data:
        p.comment = str(data.get("comment") or "").strip()
    if "items" in data:
        p.items.clear()
        db.flush()
        for it in data.get("items") or []:
            pid, qty = to_int(it.get("product_id")), to_int(it.get("qty"))
            if pid and qty > 0:
                p.items.append(PurchaseItem(product_id=pid, qty=qty, cost=to_money(it.get("cost"))))


@router.get("/purchases", response_model=list[PurchaseOut])
def purchases(status: str = "", db: Session = Depends(get_db), user: User = Depends(stock_team)):
    q = db.query(Purchase).options(selectinload(Purchase.items).selectinload(PurchaseItem.product),
                                   selectinload(Purchase.supplier))
    if status:
        q = q.filter(Purchase.status == status)
    return [j_purchase(p) for p in q.order_by(Purchase.id.desc()).limit(300).all()]


@router.get("/purchases/{pid}", response_model=PurchaseOut)
def purchase(pid: int, db: Session = Depends(get_db), user: User = Depends(stock_team)):
    p = db.get(Purchase, pid)
    if p is None:
        raise HTTPException(404, "Закупівлю не знайдено")
    return j_purchase(p)


def _then(db: Session, p: Purchase, then: str, user: User):
    if then == "ordered" and p.status == "draft":
        p.status = "ordered"
    elif then == "receive":
        if not p.items:
            bad("Немає товарів для оприбуткування")
        stock.receive_purchase(db, p, user)
        audit.log(db, user, "purchase", p.id, "receive", {"сума": p.total})
    elif then == "cancel" and p.status in ("draft", "ordered"):
        p.status = "cancelled"
        audit.log(db, user, "purchase", p.id, "update", {"статус": "скасовано"})


@router.post("/purchases", response_model=PurchaseOut)
def purchase_create(body: PurchaseIn, db: Session = Depends(get_db), user: User = Depends(stock_team)):
    data = body.model_dump(exclude_unset=True)
    p = Purchase(status="draft", created_by_id=user.id)
    db.add(p)
    _purchase_from(db, p, data)
    if not p.items:
        db.rollback()
        bad("Додайте хоча б один товар")
    db.flush()
    audit.log(db, user, "purchase", p.id, "create", {"сума": p.total})
    _then(db, p, data.get("then", ""), user)
    db.commit()
    return j_purchase(p)


@router.patch("/purchases/{pid}", response_model=PurchaseOut)
def purchase_update(pid: int, body: PurchaseIn, db: Session = Depends(get_db), user: User = Depends(stock_team)):
    data = body.model_dump(exclude_unset=True)
    p = db.get(Purchase, pid)
    if p is None:
        raise HTTPException(404, "Закупівлю не знайдено")
    if p.status not in ("draft", "ordered"):
        bad("Закупівлю вже завершено — змінювати не можна", 409)
    if data.get("then") != "cancel":
        _purchase_from(db, p, data)
    _then(db, p, data.get("then", ""), user)
    db.commit()
    return j_purchase(p)


@router.get("/suppliers", response_model=list[SupplierOut])
def suppliers(db: Session = Depends(get_db), user: User = Depends(stock_team)):
    return [{"id": s.id, "name": s.name, "phone": s.phone, "comment": s.comment}
            for s in db.query(Supplier).order_by(Supplier.name).all()]


@router.post("/suppliers", response_model=SupplierOut)
def supplier_save(body: SupplierIn, db: Session = Depends(get_db), user: User = Depends(stock_team)):
    data = body.model_dump(exclude_unset=True)
    sid = to_int(data.get("id"))
    s = db.get(Supplier, sid) if sid else Supplier()
    s.name = str(data.get("name") or "").strip()[:255]
    s.phone = str(data.get("phone") or "").strip()[:32]
    s.comment = str(data.get("comment") or "").strip()
    if not s.name:
        bad("Вкажіть назву постачальника")
    if not sid:
        db.add(s)
    db.commit()
    return {"id": s.id, "name": s.name, "phone": s.phone, "comment": s.comment}
