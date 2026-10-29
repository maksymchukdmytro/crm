from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, selectinload
from starlette.datastructures import FormData

from ..db import get_db
from ..deps import stock_team
from ..models import Product, StockMovement, User
from ..services import audit, stock
from ..services.orders import to_int
from ..web import flash, redirect, render
from .orders import form_data

router = APIRouter()

KINDS = {"purchase": "Закупівля", "reserve": "Резерв", "unreserve": "Зняття резерву", "ship": "Відправка",
         "return": "Повернення", "adjust": "Коригування"}


@router.get("/warehouse")
def warehouse(request: Request, product: int = 0, kind: str = "", low: int = 0, db: Session = Depends(get_db),
              user: User = Depends(stock_team)):
    products = db.query(Product).filter(Product.is_active.is_(True)).order_by(Product.name).all()
    value = sum((Decimal(p.cost or 0) * max(p.stock, 0) for p in products), Decimal(0))
    low_items = [p for p in products if p.available <= p.min_stock]
    shown = low_items if low else products
    mq = db.query(StockMovement).options(selectinload(StockMovement.product), selectinload(StockMovement.user))
    if product:
        mq = mq.filter(StockMovement.product_id == product)
    if kind:
        mq = mq.filter(StockMovement.kind == kind)
    moves = mq.order_by(StockMovement.id.desc()).limit(100).all()
    ctx = {"products": shown, "all_products": products, "value": value, "low_count": len(low_items),
           "reserved": sum(p.reserved for p in products), "units": sum(max(p.stock, 0) for p in products),
           "moves": moves, "kinds": KINDS, "f_product": product, "f_kind": kind, "low": low}
    return render(request, "warehouse/index.html", ctx, active="warehouse")


@router.post("/warehouse/adjust")
def adjust(request: Request, form: FormData = Depends(form_data), db: Session = Depends(get_db),
           user: User = Depends(stock_team)):
    p = db.get(Product, to_int(form.get("product_id")))
    if p is None:
        raise HTTPException(404)
    raw = (form.get("qty") or "").strip()
    if not raw.lstrip("+-").isdigit():
        flash(request, "Вкажіть кількість", "error")
        return redirect(f"/warehouse?product={p.id}")
    mode = form.get("mode", "set")
    comment = (form.get("comment") or "").strip()[:255]
    old = p.stock
    if mode == "set":
        stock.adjust(db, p, int(raw), user, comment or "інвентаризація")
    else:
        stock.move(db, p.id, "adjust", int(raw), 0, user=user, comment=comment or "коригування")
    db.flush()
    audit.log(db, user, "product", p.id, "adjust", {"було": old, "стало": p.stock, "коментар": comment})
    db.commit()
    flash(request, f"Залишок «{p.name}»: {old} → {p.stock}")
    return redirect(f"/warehouse?product={p.id}")
