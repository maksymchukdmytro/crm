"""API: товари, склад, закупівлі, постачальники."""
from __future__ import annotations

from decimal import Decimal

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..config import config
from ..models import (
    COUNTRIES, Attribute, AttributeGroup, Category, Manufacturer, OrderItem, Product, ProductPhoto, ProductVariant, Purchase,
    PurchaseItem, StockMovement, Supplier, User,
)
from ..services import audit, stock
from ..services.orders import to_int, to_money
from .schemas import (
    AdjustIn, AttributeGroupIn, AttributeGroupOut, AttributeIn, CategoryIn, CategoryOut, ManufacturerIn, ManufacturerOut, Ok,
    PhotoOut, ProductDeleteOut, ProductDetailOut, ProductIn, ProductOut, PurchaseIn, PurchaseOut, SupplierIn, SupplierOut, WarehouseOut,
)
from .common import admin, bad, iso, j_product, j_purchase, photo_url, staff, stock_team

router = APIRouter(prefix="/api", tags=["catalog"])
KINDS = {"purchase": "Закупівля", "reserve": "Резерв", "unreserve": "Зняття резерву", "ship": "Відправка",
         "return": "Повернення", "adjust": "Коригування"}


def j_move(m: StockMovement) -> dict:
    name = m.product.name if m.product else ""
    if m.variant_id and m.product:
        v = next((x for x in m.product.variants if x.id == m.variant_id), None)
        if v is not None and v.name:
            name = f"{name} ({v.name})"
    return {"id": m.id, "product_id": m.product_id, "product": name,
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
    if "warranty_months" in d and d["warranty_months"] is not None:
        p.warranty_months = max(0, min(int(d["warranty_months"] or 0), 240))
    if "upsell" in d:
        p.is_upsell = bool(d["upsell"])
    if "upsell_for" in d:
        ids = d["upsell_for"] or []
        p.upsell_for = sorted({int(x) for x in ids if str(x).isdigit() and int(x) != p.id})
    if "active" in d:
        p.is_active = bool(d["active"])
    if "category_id" in d:
        p.category_id = to_int(d["category_id"]) or None
    if "manufacturer_id" in d:
        p.manufacturer_id = to_int(d["manufacturer_id"]) or None
    if "model" in d:
        p.model = str(d["model"] or "").strip()[:120]
    if "description" in d:
        p.description = str(d["description"] or "").strip()
    if "countries" in d:
        p.countries = sorted({str(c).upper() for c in (d["countries"] or []) if str(c).upper() in COUNTRIES})
    for f in ("spec_price", "wholesale_price"):
        if f in d:
            setattr(p, f, to_money(d[f]))


def _variant_name(db: Session, ids: list[int]) -> str:
    if not ids:
        return ""
    names = {a.id: a for a in db.query(Attribute).filter(Attribute.id.in_(ids))}
    groups = {g.id: g.sort for g in db.query(AttributeGroup)}
    attrs = sorted((names[i] for i in ids if i in names), key=lambda a: (groups.get(a.group_id, 0), a.group_id))
    return " / ".join(a.name for a in attrs)


def _apply_variants(db: Session, p: Product, rows: list[dict], user: User):
    """Повний список варіантів: нові створюються (з початковим залишком), відсутні — видаляються,
    а якщо вже були в замовленнях чи на складі — лише вимикаються, щоб не зламати історію."""
    keep: set[int] = set()
    by_id = {v.id: v for v in p.variants}
    for r in rows:
        ids = sorted({int(x) for x in (r.get("attribute_ids") or [])})
        name = str(r.get("name") or "").strip()[:255] or _variant_name(db, ids)
        if not name:
            bad("Вкажіть назву варіанта або виберіть атрибути")
        vid = to_int(r.get("id"))
        v = by_id.get(vid) if vid else None
        if v is None:
            v = ProductVariant(product=p, stock=0, reserved=0, sort=(len(p.variants) + 1) * 10)
            db.add(v)
        v.name, v.attribute_ids = name, ids
        v.sku = str(r.get("sku") or "").strip()[:64] or None
        v.price = to_money(r["price"]) if r.get("price") not in (None, "") else None
        v.is_active = bool(r.get("active", True))
        db.flush()
        keep.add(v.id)
        initial = to_int(r.get("initial_stock"), 0)
        if not vid and initial > 0:
            stock.move(db, p.id, "adjust", initial, 0, user=user, comment="початковий залишок варіанта", variant_id=v.id)
    for v in list(p.variants):
        if v.id in keep:
            continue
        used = (db.query(OrderItem).filter(OrderItem.variant_id == v.id).count()
                or db.query(StockMovement).filter(StockMovement.variant_id == v.id).count())
        if used or v.stock or v.reserved:
            v.is_active = False
        else:
            p.variants.remove(v)
            db.delete(v)
    names = [v.name.lower() for v in p.variants if v.is_active]
    if len(names) != len(set(names)):
        bad("Варіанти з однаковою назвою — змініть атрибути чи назву")


# ---------------------------------------------------------------- товари
@router.get("/products", response_model=list[ProductOut])
def products(q: str = "", show: str = "active", category: int = 0, manufacturer: int = 0, stock_state: str = "",
             db: Session = Depends(get_db), user: User = Depends(staff)):
    query = db.query(Product).options(selectinload(Product.variants), selectinload(Product.photos))
    if show == "active":
        query = query.filter(Product.is_active.is_(True))
    elif show == "inactive":
        query = query.filter(Product.is_active.is_(False))
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Product.name.ilike(like), Product.sku.ilike(like), Product.model.ilike(like),
                                 Product.variants.any(ProductVariant.sku.ilike(like))))
    if category > 0:
        cats = {category} | {c.id for c in db.query(Category).filter(Category.parent_id == category)}
        query = query.filter(Product.category_id.in_(cats))
    elif category == -1:
        query = query.filter(Product.category_id.is_(None))
    if manufacturer:
        query = query.filter(Product.manufacturer_id == manufacturer)
    if stock_state == "in":
        query = query.filter(Product.stock - Product.reserved > 0)
    elif stock_state == "out":
        query = query.filter(Product.stock - Product.reserved == 0)
    elif stock_state == "minus":
        query = query.filter(Product.stock - Product.reserved < 0)
    elif stock_state == "low":
        query = query.filter(Product.stock - Product.reserved <= Product.min_stock)
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
    d["description"] = p.description or ""
    d["photos"] = [{"id": ph.id, "url": photo_url(ph.file)} for ph in p.photos]
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
    if data.get("variants"):
        _apply_variants(db, p, data["variants"], user)
    else:
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
    before = {"назва": p.name, "ціна": str(p.price), "собівартість": str(p.cost), "акційна ціна": str(p.spec_price),
              "варіанти": ", ".join(v.name for v in p.variants if v.is_active)}
    _apply_product(p, data)
    if not p.name:
        bad("Вкажіть назву товару")
    try:
        db.flush()
        if "variants" in data and data["variants"] is not None:
            _apply_variants(db, p, data["variants"], user)
            db.flush()
    except IntegrityError:
        db.rollback()
        bad("Товар або варіант з таким артикулом вже існує", 409)
    db.refresh(p)
    after = {"назва": p.name, "ціна": str(p.price), "собівартість": str(p.cost), "акційна ціна": str(p.spec_price),
             "варіанти": ", ".join(v.name for v in p.variants if v.is_active)}
    changes = {k: [before[k], after[k]] for k in before if before[k] != after[k]}
    if changes:
        audit.log(db, user, "product", p.id, "update", changes)
    from ..services import events
    events.product_changed(db, p.id)
    db.commit()
    return j_product(p)


@router.delete("/products/{pid}", response_model=ProductDeleteOut)
def product_delete(pid: int, db: Session = Depends(get_db), user: User = Depends(stock_team)):
    """Видалити товар. Якщо він уже був у замовленнях, закупівлях чи русі складу — лише в архів (вимкнути),
    щоб історія й статистика лишились цілими."""
    p = db.get(Product, pid)
    if p is None:
        raise HTTPException(404, "Товар не знайдено")
    used = (db.query(OrderItem).filter(OrderItem.product_id == pid).first()
            or db.query(PurchaseItem).filter(PurchaseItem.product_id == pid).first()
            or db.query(StockMovement).filter(StockMovement.product_id == pid).first())
    name = p.name
    if used:
        p.is_active = False
        audit.log(db, user, "product", pid, "update", {"архів": name})
        db.commit()
        return {"deleted": False, "message": f"«{name}» уже є в замовленнях або на складі — товар перенесено в архів (вимкнено)"}
    files = [ph.file for ph in p.photos]
    db.delete(p)
    audit.log(db, user, "product", pid, "delete", {"назва": name})
    db.commit()
    for f in files:
        try:
            (_photos_dir() / f).unlink(missing_ok=True)
        except OSError:
            pass
    return {"deleted": True, "message": f"Товар «{name}» видалено"}


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
    variant = None
    if data.get("variant_id"):
        variant = db.get(ProductVariant, to_int(data["variant_id"]))
        if variant is None or variant.product_id != p.id:
            bad("Варіант не знайдено")
    elif any(v.is_active for v in p.variants):
        bad("У товару є варіанти — виберіть, залишок якого варіанта змінити")
    old = variant.stock if variant is not None else p.stock
    if data.get("mode", "set") == "set":
        stock.adjust(db, p, int(raw), user, comment or "інвентаризація", variant=variant)
    else:
        stock.move(db, p.id, "adjust", int(raw), 0, user=user, comment=comment or "коригування",
                   variant_id=variant.id if variant is not None else None)
    db.flush()
    db.refresh(p)
    new = variant.stock if variant is not None else p.stock
    audit.log(db, user, "product", p.id, "adjust", {"варіант": variant.name if variant is not None else "",
                                                     "було": old, "стало": new, "коментар": comment})
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
                p.items.append(PurchaseItem(product_id=pid, variant_id=to_int(it.get("variant_id")) or None, qty=qty,
                                            cost=to_money(it.get("cost"))))


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


# ---------------------------------------------------------------- фото товарів
PHOTO_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}
PHOTO_MAX = 10 * 1024 * 1024


def _photos_dir() -> Path:
    d = Path(config.MEDIA_DIR) / "products"
    d.mkdir(parents=True, exist_ok=True)
    return d


@router.post("/products/{pid}/photos", response_model=list[PhotoOut])
async def photo_upload(pid: int, files: list[UploadFile] = File(...), db: Session = Depends(get_db),
                       user: User = Depends(stock_team)):
    p = db.get(Product, pid)
    if p is None:
        raise HTTPException(404, "Товар не знайдено")
    if len(p.photos) + len(files) > 20:
        bad("Не більше 20 фото на товар")
    sort = max((ph.sort for ph in p.photos), default=0)
    for f in files:
        ext = PHOTO_TYPES.get((f.content_type or "").lower())
        if not ext:
            bad(f"«{f.filename}»: підтримуються JPG, PNG, WEBP і GIF")
        data = await f.read()
        if len(data) > PHOTO_MAX:
            bad(f"«{f.filename}»: файл більший за 10 МБ")
        name = f"{pid}-{uuid.uuid4().hex[:12]}{ext}"
        (_photos_dir() / name).write_bytes(data)
        sort += 10
        db.add(ProductPhoto(product_id=pid, file=name, sort=sort))
    audit.log(db, user, "product", pid, "update", {"фото": f"додано {len(files)}"})
    db.commit()
    db.refresh(p)
    return [{"id": ph.id, "url": photo_url(ph.file)} for ph in p.photos]


@router.delete("/products/{pid}/photos/{photo_id}", response_model=list[PhotoOut])
def photo_delete(pid: int, photo_id: int, db: Session = Depends(get_db), user: User = Depends(stock_team)):
    ph = db.get(ProductPhoto, photo_id)
    if ph is None or ph.product_id != pid:
        raise HTTPException(404, "Фото не знайдено")
    try:
        (_photos_dir() / ph.file).unlink(missing_ok=True)
    except OSError:
        pass
    db.delete(ph)
    db.commit()
    return [{"id": x.id, "url": photo_url(x.file)} for x in db.query(ProductPhoto).filter(ProductPhoto.product_id == pid)
            .order_by(ProductPhoto.sort, ProductPhoto.id)]


@router.put("/products/{pid}/photos", response_model=list[PhotoOut])
def photo_order(pid: int, ids: list[int], db: Session = Depends(get_db), user: User = Depends(stock_team)):
    photos = {ph.id: ph for ph in db.query(ProductPhoto).filter(ProductPhoto.product_id == pid)}
    for i, x in enumerate(ids):
        if x in photos:
            photos[x].sort = (i + 1) * 10
    db.commit()
    return [{"id": ph.id, "url": photo_url(ph.file)} for ph in sorted(photos.values(), key=lambda p: (p.sort, p.id))]


# ---------------------------------------------------------------- категорії, виробники, атрибути
def _counts(db: Session, col) -> dict[int, int]:
    return dict(db.query(col, func.count(Product.id)).filter(col.isnot(None)).group_by(col).all())


@router.get("/catalog/categories", response_model=list[CategoryOut])
def categories(db: Session = Depends(get_db), user: User = Depends(staff)):
    counts = _counts(db, Product.category_id)
    rows = db.query(Category).order_by(Category.sort, Category.name).all()
    return [{"id": c.id, "name": c.name, "parent_id": c.parent_id, "sort": c.sort, "active": c.is_active,
             "products": counts.get(c.id, 0)} for c in rows]


@router.post("/catalog/categories", response_model=list[CategoryOut])
def category_save(body: CategoryIn, db: Session = Depends(get_db), user: User = Depends(stock_team)):
    c = db.get(Category, body.id) if body.id else Category()
    if body.id and c is None:
        raise HTTPException(404, "Категорію не знайдено")
    name = body.name.strip()
    if not name:
        bad("Вкажіть назву категорії")
    parent = db.get(Category, body.parent_id) if body.parent_id else None
    if parent is not None and (parent.parent_id is not None or (c.id and parent.id == c.id)):
        bad("Підкатегорія може бути лише в розділі першого рівня")
    if c.id and parent is not None and db.query(Category).filter(Category.parent_id == c.id).count():
        bad("У цієї категорії є підкатегорії — її не можна зробити підкатегорією")
    c.name, c.parent_id, c.is_active = name[:160], parent.id if parent else None, body.active
    if body.sort is not None:
        c.sort = body.sort
    if not c.id:
        db.add(c)
    db.commit()
    return categories(db, user)


@router.delete("/catalog/categories/{cid}", response_model=list[CategoryOut])
def category_delete(cid: int, db: Session = Depends(get_db), user: User = Depends(stock_team)):
    c = db.get(Category, cid)
    if c is None:
        raise HTTPException(404, "Категорію не знайдено")
    db.query(Category).filter(Category.parent_id == cid).update({"parent_id": None})
    db.query(Product).filter(Product.category_id == cid).update({"category_id": None})
    db.delete(c)
    db.commit()
    return categories(db, user)


@router.get("/catalog/manufacturers", response_model=list[ManufacturerOut])
def manufacturers(db: Session = Depends(get_db), user: User = Depends(staff)):
    counts = _counts(db, Product.manufacturer_id)
    return [{"id": m.id, "name": m.name, "active": m.is_active, "products": counts.get(m.id, 0)}
            for m in db.query(Manufacturer).order_by(Manufacturer.name)]


@router.post("/catalog/manufacturers", response_model=list[ManufacturerOut])
def manufacturer_save(body: ManufacturerIn, db: Session = Depends(get_db), user: User = Depends(stock_team)):
    m = db.get(Manufacturer, body.id) if body.id else Manufacturer()
    if body.id and m is None:
        raise HTTPException(404, "Виробника не знайдено")
    name = body.name.strip()[:160]
    if not name:
        bad("Вкажіть назву виробника")
    dup = db.query(Manufacturer).filter(func.lower(Manufacturer.name) == name.lower(), Manufacturer.id != (m.id or 0)).first()
    if dup:
        bad("Такий виробник уже є", 409)
    m.name, m.is_active = name, body.active
    if not m.id:
        db.add(m)
    db.commit()
    return manufacturers(db, user)


@router.delete("/catalog/manufacturers/{mid}", response_model=list[ManufacturerOut])
def manufacturer_delete(mid: int, db: Session = Depends(get_db), user: User = Depends(stock_team)):
    m = db.get(Manufacturer, mid)
    if m is None:
        raise HTTPException(404, "Виробника не знайдено")
    db.query(Product).filter(Product.manufacturer_id == mid).update({"manufacturer_id": None})
    db.delete(m)
    db.commit()
    return manufacturers(db, user)


def _groups(db: Session) -> list[dict]:
    return [{"id": g.id, "name": g.name, "sort": g.sort,
             "attributes": [{"id": a.id, "name": a.name, "sort": a.sort, "active": a.is_active} for a in g.attributes]}
            for g in db.query(AttributeGroup).options(selectinload(AttributeGroup.attributes)).order_by(AttributeGroup.sort, AttributeGroup.id)]


@router.get("/catalog/attributes", response_model=list[AttributeGroupOut])
def attributes(db: Session = Depends(get_db), user: User = Depends(staff)):
    return _groups(db)


@router.post("/catalog/attribute-groups", response_model=list[AttributeGroupOut])
def attribute_group_save(body: AttributeGroupIn, db: Session = Depends(get_db), user: User = Depends(stock_team)):
    g = db.get(AttributeGroup, body.id) if body.id else AttributeGroup()
    if body.id and g is None:
        raise HTTPException(404, "Категорію атрибутів не знайдено")
    if not body.name.strip():
        bad("Вкажіть назву, наприклад «Колір» чи «Розмір»")
    g.name = body.name.strip()[:120]
    if body.sort is not None:
        g.sort = body.sort
    if not g.id:
        db.add(g)
    db.commit()
    return _groups(db)


@router.delete("/catalog/attribute-groups/{gid}", response_model=list[AttributeGroupOut])
def attribute_group_delete(gid: int, db: Session = Depends(get_db), user: User = Depends(stock_team)):
    g = db.get(AttributeGroup, gid)
    if g is None:
        raise HTTPException(404, "Категорію атрибутів не знайдено")
    db.delete(g)
    db.commit()
    return _groups(db)


@router.post("/catalog/attributes", response_model=list[AttributeGroupOut])
def attribute_save(body: AttributeIn, db: Session = Depends(get_db), user: User = Depends(stock_team)):
    a = db.get(Attribute, body.id) if body.id else Attribute()
    if body.id and a is None:
        raise HTTPException(404, "Атрибут не знайдено")
    if db.get(AttributeGroup, body.group_id) is None:
        bad("Виберіть категорію атрибутів")
    if not body.name.strip():
        bad("Вкажіть значення атрибута")
    a.group_id, a.name, a.is_active = body.group_id, body.name.strip()[:120], body.active
    if body.sort is not None:
        a.sort = body.sort
    if not a.id:
        db.add(a)
    db.commit()
    return _groups(db)


@router.delete("/catalog/attributes/{aid}", response_model=list[AttributeGroupOut])
def attribute_delete(aid: int, db: Session = Depends(get_db), user: User = Depends(stock_team)):
    a = db.get(Attribute, aid)
    if a is None:
        raise HTTPException(404, "Атрибут не знайдено")
    used = db.query(ProductVariant).all()
    if any(aid in (v.attribute_ids or []) for v in used):
        a.is_active = False  # уже у варіантах товарів — лише вимикаємо
    else:
        db.delete(a)
    db.commit()
    return _groups(db)
