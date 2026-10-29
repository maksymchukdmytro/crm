from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.datastructures import FormData

from ..db import get_db
from ..deps import stock_team, staff
from ..models import OrderItem, Product, StockMovement, User
from ..services import audit, stock
from ..services.orders import to_int, to_money
from ..web import flash, redirect, render
from .orders import form_data

router = APIRouter()


@router.get("/products")
def products(request: Request, q: str = "", show: str = "active", db: Session = Depends(get_db),
             user: User = Depends(staff)):
    query = db.query(Product)
    if show == "active":
        query = query.filter(Product.is_active.is_(True))
    elif show == "inactive":
        query = query.filter(Product.is_active.is_(False))
    if q:
        query = query.filter(or_(Product.name.ilike(f"%{q}%"), Product.sku.ilike(f"%{q}%")))
    rows = query.order_by(Product.is_upsell, Product.name).all()
    return render(request, "products/list.html", {"products": rows, "q": q, "show": show}, active="products")


def _product_from_form(p: Product, form: FormData):
    p.name = (form.get("name") or "").strip()[:255]
    p.sku = (form.get("sku") or "").strip()[:64] or None
    p.price = to_money(form.get("price"))
    p.cost = to_money(form.get("cost"))
    p.weight = to_money(form.get("weight")) or p.weight or Decimal("0.5")
    p.min_stock = to_int(form.get("min_stock"), 0)
    p.is_upsell = form.get("is_upsell") == "1"
    p.is_active = form.get("is_active", "1") == "1"


@router.get("/products/new")
def product_new(request: Request, user: User = Depends(stock_team)):
    p = Product(name="", price=0, cost=0, weight=0.5, stock=0, reserved=0, min_stock=0, is_active=True, is_upsell=False)
    return render(request, "products/form.html", {"p": p, "is_new": True}, active="products")


@router.post("/products/new")
def product_create(request: Request, form: FormData = Depends(form_data), db: Session = Depends(get_db),
                   user: User = Depends(stock_team)):
    p = Product(stock=0, reserved=0)
    _product_from_form(p, form)
    if not p.name:
        flash(request, "Вкажіть назву товару", "error")
        return redirect("/products/new")
    db.add(p)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        flash(request, "Товар з таким артикулом вже існує", "error")
        return redirect("/products/new")
    initial = to_int(form.get("initial_stock"), 0)
    if initial:
        stock.move(db, p.id, "adjust", initial, 0, user=user, comment="початковий залишок")
    audit.log(db, user, "product", p.id, "create", {"назва": p.name, "ціна": p.price})
    db.commit()
    flash(request, "Товар додано")
    return redirect("/products")


@router.get("/products/{pid}")
def product_edit(pid: int, request: Request, db: Session = Depends(get_db), user: User = Depends(staff)):
    p = db.get(Product, pid)
    if p is None:
        raise HTTPException(404)
    moves = (db.query(StockMovement).filter(StockMovement.product_id == pid)
             .order_by(StockMovement.id.desc()).limit(50).all())
    sold = db.query(OrderItem).filter(OrderItem.product_id == pid).count()
    return render(request, "products/form.html", {"p": p, "is_new": False, "moves": moves, "sold": sold},
                  active="products")


@router.post("/products/{pid}")
def product_save(pid: int, request: Request, form: FormData = Depends(form_data), db: Session = Depends(get_db),
                 user: User = Depends(stock_team)):
    p = db.get(Product, pid)
    if p is None:
        raise HTTPException(404)
    before = {"назва": p.name, "ціна": str(p.price), "собівартість": str(p.cost)}
    _product_from_form(p, form)
    if not p.name:
        flash(request, "Вкажіть назву товару", "error")
        return redirect(f"/products/{pid}")
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        flash(request, "Товар з таким артикулом вже існує", "error")
        return redirect(f"/products/{pid}")
    after = {"назва": p.name, "ціна": str(p.price), "собівартість": str(p.cost)}
    changes = {k: [before[k], after[k]] for k in before if before[k] != after[k]}
    if changes:
        audit.log(db, user, "product", p.id, "update", changes)
    db.commit()
    flash(request, "Збережено")
    return redirect("/products")
