import csv
import io
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload
from starlette.datastructures import FormData

from ..carriers import CARRIERS, CarrierError, get_carrier
from ..db import get_db
from ..deps import Forbidden, staff
from ..models import AuditLog, Order, Payment, Product, SmsMessage, Status, User
from ..services import audit, delivery, payments
from ..services import orders as svc
from ..services import settings as st
from ..services import sms as sms_svc
from ..services.reports import period_bounds
from ..web import flash, parse_date, redirect, render, safe_next

router = APIRouter()
PER_PAGE = 50
FILTER_KEYS = ("status", "q", "manager", "date_from", "date_to", "delivery", "source", "dup", "pay")


async def form_data(request: Request) -> FormData:
    return await request.form()


# ---------------------------------------------------------------- helpers
def _filters(request: Request) -> dict:
    return {k: (request.query_params.get(k) or "").strip() for k in FILTER_KEYS}


def _apply(q, f: dict, with_status: bool = True):
    if f.get("stage") in ("lead", "order"):  # розділ «Ліди» / «Замовлення»
        q = q.filter(Order.status.has(Status.stage == f["stage"]))
    if with_status and f.get("status"):
        q = q.filter(Order.status_id == svc.to_int(f["status"]))
    text = f.get("q")
    if text:
        digits = "".join(ch for ch in text if ch.isdigit())
        conds = [Order.customer_name.ilike(f"%{text}%"), Order.ttn.contains(text.replace(" ", ""))]
        if digits and len(digits) >= 5:
            conds.append(Order.phone.contains(digits[-9:] if len(digits) > 9 else digits))
        if digits and len(digits) <= 9 and digits == text.strip().lstrip("#"):
            conds.append(Order.id == int(digits))
        q = q.filter(or_(*conds))
    if f.get("manager") == "none":
        q = q.filter(Order.manager_id.is_(None))
    elif f.get("manager"):
        q = q.filter(Order.manager_id == svc.to_int(f["manager"]))
    d1, d2 = parse_date(f.get("date_from")), parse_date(f.get("date_to"))
    if d1 or d2:
        start, end = period_bounds(d1 or d2, d2 or d1)
        q = q.filter(Order.created_at >= start, Order.created_at < end)
    if f.get("delivery"):
        q = q.filter(Order.delivery_method == f["delivery"])
    if f.get("source"):
        q = q.filter(or_(Order.utm_source == f["source"], Order.site == f["source"]))
    if f.get("dup") == "1":
        q = q.filter(Order.duplicate_of_id.is_not(None))
    if f.get("pay"):
        q = q.filter(Order.payment_type == f["pay"])
    return q


def _card(request: Request, order: Order, anchor: str = "") -> str:
    """Адреса картки замовлення; у вбудованому режимі (вікно поверх списку) зберігає ?embed=1."""
    q = "?embed=1" if request.query_params.get("embed") == "1" else ""
    return f"/orders/{order.id}{q}{anchor}"


def _get_order(db: Session, order_id: int, user: User) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(404, "Замовлення не знайдено")
    if not svc.can_view(db, user, order):
        raise Forbidden()
    return order


def _items_from_form(form: FormData) -> list[dict]:
    pids, names = form.getlist("item_product_id"), form.getlist("item_name")
    qtys, prices, upsells = form.getlist("item_qty"), form.getlist("item_price"), form.getlist("item_upsell")
    items = []
    for i in range(len(names)):
        items.append({
            "product_id": pids[i] if i < len(pids) else "",
            "name": names[i],
            "qty": qtys[i] if i < len(qtys) else 1,
            "price": prices[i] if i < len(prices) else "",
            "is_upsell": upsells[i] if i < len(upsells) else "0",
        })
    return items


def _fields_from_form(form: FormData) -> dict:
    return {f: form.get(f) for f in svc.ORDER_FIELDS if f in form}


def _lookups(db: Session) -> dict:
    statuses = db.query(Status).filter(Status.is_active.is_(True)).order_by(Status.sort, Status.id).all()
    managers = (db.query(User).filter(User.is_active.is_(True), User.role.in_(["admin", "manager"]))
                .order_by(User.full_name, User.username).all())
    products = db.query(Product).filter(Product.is_active.is_(True)).order_by(Product.is_upsell, Product.name).all()
    products_js = [{"id": p.id, "name": p.name, "sku": p.sku or "", "price": str(p.price),
                    "available": p.available, "upsell": p.is_upsell} for p in products]
    return {"statuses": statuses, "managers": managers, "products_js": products_js}


def _items_js(order: Order) -> list[dict]:
    return [{"product_id": i.product_id, "name": i.name, "qty": i.qty, "price": str(i.price),
             "upsell": bool(i.is_upsell)} for i in order.items]


def _carrier_info(db: Session) -> dict:
    s = st.get_all(db)
    return {code: {"name": cls.name, "beta": cls.beta, "configured": cls(s).configured()}
            for code, cls in CARRIERS.items()}


# ---------------------------------------------------------------- list
@router.get("/orders")
def orders_list(request: Request, page: int = 1, db: Session = Depends(get_db), user: User = Depends(staff)):
    f = _filters(request)
    base = svc.visible_orders_query(db, user)
    q = _apply(base, f)
    total = q.count()
    page = max(page, 1)
    rows = (q.options(selectinload(Order.items), selectinload(Order.status), selectinload(Order.manager))
            .order_by(Order.id.desc()).offset((page - 1) * PER_PAGE).limit(PER_PAGE).all())
    counts = dict(_apply(base, f, with_status=False).with_entities(Order.status_id, func.count(Order.id))
                  .group_by(Order.status_id).all())
    sources = [r[0] for r in db.query(Order.utm_source).filter(Order.utm_source != "")
               .group_by(Order.utm_source).order_by(func.count(Order.id).desc()).limit(30).all()]
    ctx = {"orders": rows, "f": f, "total": total, "page": page, "pages": max((total - 1) // PER_PAGE + 1, 1),
           "counts": counts, "all_count": sum(counts.values()), "sources": sources, **_lookups(db)}
    return render(request, "orders/list.html", ctx, active="orders")


@router.post("/orders/bulk")
def orders_bulk(request: Request, form: FormData = Depends(form_data), db: Session = Depends(get_db),
                user: User = Depends(staff)):
    ids = [svc.to_int(x) for x in form.getlist("ids") if svc.to_int(x)]
    action = form.get("action", "")
    back = safe_next(form.get("back"), "/orders")
    if not ids:
        flash(request, "Не вибрано жодного замовлення", "warn")
        return redirect(back)
    orders = [o for o in db.query(Order).filter(Order.id.in_(ids)).all() if svc.can_view(db, user, o)]
    done, errors = 0, []
    if action.startswith("status:"):
        status = db.get(Status, svc.to_int(action.split(":", 1)[1]))
        if status:
            for o in orders:
                done += svc.change_status(db, o, status, user)
    elif action.startswith("assign:"):
        if user.role == "warehouse":
            raise Forbidden()
        mid = svc.to_int(action.split(":", 1)[1])
        manager = db.get(User, mid) if mid else None
        for o in orders:
            svc.assign(db, o, manager, user)
            done += 1
    elif action == "ttn":
        for o in orders:
            if o.ttn or o.delivery_method not in CARRIERS:
                continue
            try:
                delivery.create_ttn(db, o, user)
                db.commit()
                done += 1
            except CarrierError as e:
                db.rollback()
                errors.append(f"№{o.id}: {e}")
    elif action == "track":
        res = delivery.sync_tracking(db, [o.id for o in orders], force=True)
        done = res["checked"]
        errors.extend(res["errors"])
    db.commit()
    flash(request, f"Оброблено замовлень: {done}")
    for e in errors[:10]:
        flash(request, e, "error")
    return redirect(back)


@router.get("/orders/export.csv")
def orders_export(request: Request, db: Session = Depends(get_db), user: User = Depends(staff)):
    f = _filters(request)
    q = _apply(svc.visible_orders_query(db, user), f).options(
        selectinload(Order.items), selectinload(Order.status), selectinload(Order.manager)).order_by(Order.id.desc())
    buf = io.StringIO()
    buf.write("﻿")
    w = csv.writer(buf, delimiter=";")
    w.writerow(["ID", "Дата", "Статус", "Менеджер", "Клієнт", "Телефон", "Товари", "Сума", "Накладений",
                "Доставка", "Місто", "Відділення", "ТТН", "Стан доставки", "Джерело", "Кампанія", "Сайт"])
    from ..web import f_dt
    for o in q.yield_per(500):
        w.writerow([o.id, f_dt(o.created_at), o.status.name, o.manager.display if o.manager else "",
                    o.customer_name, o.phone, "; ".join(f"{i.name} x{i.qty}" for i in o.items),
                    o.total, o.cod_amount, o.delivery_method_name, o.city_name, o.warehouse_name, o.ttn,
                    o.delivery_status, o.utm_source, o.utm_campaign, o.site])
    return Response(buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="orders.csv"'})


# ---------------------------------------------------------------- create
@router.get("/orders/new")
def order_new(request: Request, db: Session = Depends(get_db), user: User = Depends(staff)):
    order = Order(delivery_method="novaposhta", payment_type="cod", items=[], discount=0, prepayment=0,
                  delivery_cost=0, total=0, cod_amount=0)
    phone = request.query_params.get("phone", "")
    if phone:
        order.phone = svc.normalize_phone(phone)
        prev = svc.customer_orders(db, order.phone, limit=1)
        if prev:
            p = prev[0]
            for fld in ("customer_name", "delivery_method", "city_name", "city_ref", "warehouse_name",
                        "warehouse_ref", "address", "postcode"):
                setattr(order, fld, getattr(p, fld))
    return render(request, "orders/form.html", {"order": order, "is_new": True, "carriers": _carrier_info(db),
                                                 "items_js": [], "version": "", **_lookups(db)}, active="orders")


@router.post("/orders/new")
def order_create(request: Request, form: FormData = Depends(form_data), db: Session = Depends(get_db),
                 user: User = Depends(staff)):
    data = _fields_from_form(form)
    if user.role == "admin" and form.get("manager_id"):
        data["manager_id"] = form.get("manager_id")
    order = svc.create_order(db, data, _items_from_form(form), user, source="manual")
    sid = svc.to_int(form.get("status_id"))
    if sid and sid != order.status_id:
        status = db.get(Status, sid)
        if status:
            svc.change_status(db, order, status, user)
    svc.add_comment(db, order, form.get("new_comment", ""), user)
    db.commit()
    flash(request, f"Замовлення №{order.id} створено")
    return redirect(_card(request, order))


# ---------------------------------------------------------------- card
@router.get("/orders/{order_id}")
def order_view(order_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(staff)):
    order = _get_order(db, order_id, user)
    history = (db.query(AuditLog).options(selectinload(AuditLog.user))
               .filter(AuditLog.entity == "order", AuditLog.entity_id == order.id)
               .order_by(AuditLog.id.desc()).limit(200).all())
    ctx = {
        "order": order,
        "is_new": False,
        "history": history,
        "action_names": audit.ACTION_NAMES,
        "others": svc.customer_orders(db, order.phone, exclude_id=order.id),
        "sms_list": db.query(SmsMessage).filter(SmsMessage.order_id == order.id).order_by(SmsMessage.id.desc()).all(),
        "carriers": _carrier_info(db),
        "sms_ready": bool(st.get(db, "sms_token")),
        "version": order.updated_at.isoformat() if order.updated_at else "",
        "items_js": _items_js(order),
        **_lookups(db),
    }
    return render(request, "orders/form.html", ctx, active="orders")


@router.post("/orders/{order_id}")
def order_save(order_id: int, request: Request, form: FormData = Depends(form_data), db: Session = Depends(get_db),
               user: User = Depends(staff)):
    order = _get_order(db, order_id, user)
    version = form.get("version", "")
    if version and order.updated_at and version != order.updated_at.isoformat():
        flash(request, "Замовлення щойно змінив інший користувач. Перевірте дані і збережіть ще раз.", "error")
        return redirect(_card(request, order))
    svc.update_order(db, order, _fields_from_form(form), user)
    if "item_name" in form or form.get("items_present") == "1":
        svc.set_items(db, order, _items_from_form(form), user)
    if user.role == "admin" and "manager_id" in form:
        mid = svc.to_int(form.get("manager_id"))
        svc.assign(db, order, db.get(User, mid) if mid else None, user)
    sid = svc.to_int(form.get("status_id"))
    if sid and sid != order.status_id:
        status = db.get(Status, sid)
        if status:
            svc.change_status(db, order, status, user)
    svc.add_comment(db, order, form.get("new_comment", ""), user)
    db.commit()
    if form.get("then") == "ttn":
        try:
            ttn = delivery.create_ttn(db, order, user)
            db.commit()
            flash(request, f"Збережено. ТТН {ttn} створено")
        except CarrierError as e:
            db.rollback()
            flash(request, f"Збережено, але ТТН не створено: {e}", "error")
        return redirect(_card(request, order))
    flash(request, "Збережено")
    nxt = form.get("next")
    if nxt == "list":
        return redirect("/orders")
    return redirect(_card(request, order))


@router.post("/orders/{order_id}/take")
def order_take(order_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(staff)):
    order = _get_order(db, order_id, user)
    if user.role == "warehouse":
        raise Forbidden()
    if order.manager_id and order.manager_id != user.id and user.role != "admin":
        flash(request, "Замовлення вже взяв інший менеджер", "warn")
    else:
        svc.assign(db, order, user, user)
        db.commit()
    return redirect(_card(request, order))


@router.post("/orders/{order_id}/comment")
def order_comment(order_id: int, request: Request, form: FormData = Depends(form_data),
                  db: Session = Depends(get_db), user: User = Depends(staff)):
    order = _get_order(db, order_id, user)
    if svc.add_comment(db, order, form.get("text", ""), user):
        db.commit()
    return redirect(_card(request, order, '#comments'))


@router.post("/orders/{order_id}/ttn")
def order_ttn(order_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(staff)):
    order = _get_order(db, order_id, user)
    try:
        ttn = delivery.create_ttn(db, order, user)
        db.commit()
        flash(request, f"ТТН {ttn} створено")
    except CarrierError as e:
        db.rollback()
        flash(request, str(e), "error")
    return redirect(_card(request, order))


@router.post("/orders/{order_id}/ttn/delete")
def order_ttn_delete(order_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(staff)):
    order = _get_order(db, order_id, user)
    try:
        delivery.delete_ttn(db, order, user)
        db.commit()
        flash(request, "ТТН видалено")
    except CarrierError as e:
        db.rollback()
        flash(request, str(e), "error")
    return redirect(_card(request, order))


@router.post("/orders/{order_id}/track")
def order_track(order_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(staff)):
    order = _get_order(db, order_id, user)
    res = delivery.sync_tracking(db, [order.id], force=True)
    for e in res["errors"]:
        flash(request, e, "error")
    if not res["errors"]:
        flash(request, "Статус доставки оновлено" if res["changed"] else "Статус доставки без змін")
    return redirect(_card(request, order))


@router.get("/orders/{order_id}/label")
def order_label(order_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(staff)):
    order = _get_order(db, order_id, user)
    from ..services.delivery import carrier_for
    carrier = carrier_for(db, order)
    if carrier is None or not order.ttn:
        raise HTTPException(404)
    try:
        pdf = carrier.label_pdf(order)
    except CarrierError as e:
        flash(request, str(e), "error")
        return redirect(_card(request, order))
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="label-{order.ttn}.pdf"'})


@router.get("/orders/{order_id}/print")
def order_print(order_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(staff)):
    order = _get_order(db, order_id, user)
    return render(request, "orders/print.html", {"order": order}, active="orders")


@router.post("/orders/{order_id}/sms")
def order_sms(order_id: int, request: Request, form: FormData = Depends(form_data), db: Session = Depends(get_db),
              user: User = Depends(staff)):
    order = _get_order(db, order_id, user)
    text = sms_svc.render(form.get("text", ""), order, st.get(db, "company_name"))
    channel = form.get("channel") if form.get("channel") in ("sms", "viber", "hybrid") else "sms"
    if text and order.phone:
        sms_svc.queue(db, order, order.phone, text, channel)
        audit.log(db, user, "order", order.id, "sms", {"текст": text, "канал": channel})
        db.commit()
        flash(request, "Повідомлення поставлено в чергу на відправку")
    return redirect(_card(request, order, '#sms'))


@router.post("/orders/{order_id}/payment")
def order_payment(order_id: int, request: Request, form: FormData = Depends(form_data),
                  db: Session = Depends(get_db), user: User = Depends(staff)):
    order = _get_order(db, order_id, user)
    amount = svc.to_money(form.get("amount"))
    if amount <= 0:
        flash(request, "Вкажіть суму", "error")
        return redirect(_card(request, order, '#payments'))
    p = Payment(kind="prepayment", amount=amount, status="received", method=form.get("method") or "card",
                reference=(form.get("reference") or "")[:255], received_amount=amount)
    from ..models import utcnow
    p.received_at = utcnow()
    order.payments.append(p)
    order.prepayment = Decimal(order.prepayment or 0) + amount
    if order.payment_type == "cod":
        order.payment_type = "partial"
    svc.recalc(order)
    if order.payment_type == "partial" and order.cod_amount <= 0:
        order.payment_type = "prepaid"
        svc.recalc(order)
    payments.ensure_cod_payment(db, order) if order.stock_shipped else None
    audit.log(db, user, "order", order.id, "payment", {"передоплата": amount, "метод": p.method})
    db.commit()
    flash(request, f"Передоплату {amount} грн додано")
    return redirect(_card(request, order, '#payments'))
