from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, selectinload
from starlette.datastructures import FormData

from ..db import get_db
from ..deps import stock_team
from ..models import Product, Purchase, PurchaseItem, Supplier, User
from ..services import audit, stock
from ..services.orders import to_int, to_money
from ..web import flash, redirect, render
from .orders import form_data

router = APIRouter()

PURCHASE_STATUSES = {"draft": "Чернетка", "ordered": "Замовлено", "received": "Оприбутковано", "cancelled": "Скасовано"}


def _ctx(db: Session) -> dict:
    return {
        "suppliers": db.query(Supplier).order_by(Supplier.name).all(),
        "products": db.query(Product).filter(Product.is_active.is_(True)).order_by(Product.name).all(),
        "statuses": PURCHASE_STATUSES,
    }


def _apply_form(db: Session, purchase: Purchase, form: FormData):
    purchase.supplier_id = to_int(form.get("supplier_id")) or None
    purchase.comment = (form.get("comment") or "").strip()
    pids, qtys, costs = form.getlist("item_product_id"), form.getlist("item_qty"), form.getlist("item_cost")
    purchase.items.clear()
    db.flush()
    for i, pid in enumerate(pids):
        pid, qty = to_int(pid), to_int(qtys[i] if i < len(qtys) else 0)
        if pid and qty > 0:
            purchase.items.append(PurchaseItem(product_id=pid, qty=qty,
                                               cost=to_money(costs[i] if i < len(costs) else 0)))


@router.get("/purchases")
def purchases(request: Request, status: str = "", db: Session = Depends(get_db), user: User = Depends(stock_team)):
    q = db.query(Purchase).options(selectinload(Purchase.items), selectinload(Purchase.supplier))
    if status:
        q = q.filter(Purchase.status == status)
    rows = q.order_by(Purchase.id.desc()).limit(300).all()
    return render(request, "purchases/list.html", {"purchases": rows, "f_status": status, **_ctx(db)},
                  active="purchases")


@router.get("/purchases/new")
def purchase_new(request: Request, db: Session = Depends(get_db), user: User = Depends(stock_team)):
    return render(request, "purchases/form.html", {"p": Purchase(status="draft", items=[]), "is_new": True, **_ctx(db)},
                  active="purchases")


@router.post("/purchases/new")
def purchase_create(request: Request, form: FormData = Depends(form_data), db: Session = Depends(get_db),
                    user: User = Depends(stock_team)):
    p = Purchase(status="draft", created_by_id=user.id)
    db.add(p)
    _apply_form(db, p, form)
    if not p.items:
        db.rollback()
        flash(request, "Додайте хоча б один товар", "error")
        return redirect("/purchases/new")
    db.flush()
    audit.log(db, user, "purchase", p.id, "create", {"сума": p.total})
    if form.get("then") == "receive":
        stock.receive_purchase(db, p, user)
        audit.log(db, user, "purchase", p.id, "receive", {})
    db.commit()
    flash(request, f"Закупівлю №{p.id} збережено")
    return redirect(f"/purchases/{p.id}")


@router.get("/purchases/{pid}")
def purchase_view(pid: int, request: Request, db: Session = Depends(get_db), user: User = Depends(stock_team)):
    p = db.get(Purchase, pid)
    if p is None:
        raise HTTPException(404)
    return render(request, "purchases/form.html", {"p": p, "is_new": False, **_ctx(db)}, active="purchases")


@router.post("/purchases/{pid}")
def purchase_save(pid: int, request: Request, form: FormData = Depends(form_data), db: Session = Depends(get_db),
                  user: User = Depends(stock_team)):
    p = db.get(Purchase, pid)
    if p is None:
        raise HTTPException(404)
    action = form.get("then", "save")
    if p.status in ("draft", "ordered") and action in ("save", "receive", "ordered"):
        _apply_form(db, p, form)
        if action == "ordered":
            p.status = "ordered"
        if action == "receive":
            if not p.items:
                flash(request, "Немає товарів для оприбуткування", "error")
                db.rollback()
                return redirect(f"/purchases/{pid}")
            stock.receive_purchase(db, p, user)
            audit.log(db, user, "purchase", p.id, "receive", {"сума": p.total})
            flash(request, "Товар оприбутковано, залишки оновлено")
        else:
            flash(request, "Збережено")
    elif action == "cancel" and p.status in ("draft", "ordered"):
        p.status = "cancelled"
        audit.log(db, user, "purchase", p.id, "update", {"статус": "скасовано"})
        flash(request, "Закупівлю скасовано")
    db.commit()
    return redirect(f"/purchases/{pid}")


@router.get("/suppliers")
def suppliers(request: Request, db: Session = Depends(get_db), user: User = Depends(stock_team)):
    rows = db.query(Supplier).order_by(Supplier.name).all()
    return render(request, "purchases/suppliers.html", {"suppliers": rows}, active="purchases")


@router.post("/suppliers")
def supplier_save(request: Request, form: FormData = Depends(form_data), db: Session = Depends(get_db),
                  user: User = Depends(stock_team)):
    sid = to_int(form.get("id"))
    s = db.get(Supplier, sid) if sid else Supplier()
    s.name = (form.get("name") or "").strip()[:255]
    s.phone = (form.get("phone") or "").strip()[:32]
    s.comment = (form.get("comment") or "").strip()
    if not s.name:
        flash(request, "Вкажіть назву постачальника", "error")
        return redirect("/suppliers")
    if not sid:
        db.add(s)
    db.commit()
    flash(request, "Постачальника збережено")
    return redirect("/suppliers")
