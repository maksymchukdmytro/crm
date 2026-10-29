"""API замовлень: список (курсор), картка, створення, зміни, масові дії, ТТН, оплати, SMS."""
from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from ..carriers import CARRIERS, CarrierError
from ..db import get_db
from ..deps import Forbidden
from ..models import AuditLog, Order, Payment, SmsMessage, Status, User, utcnow
from ..routers.orders import _apply
from ..services import audit, delivery, payments, queue
from ..services import orders as svc
from ..services import settings as st
from ..services import sms as sms_svc
from ..services.audit import ACTION_NAMES
from ..web import f_details
from .schemas import BulkIn, BulkOut, OrderIn, OrderListOut, OrderOut, PaymentIn, SmsIn, TextIn, TrackOut, TtnIn, TtnPreviewOut
from .common import bad, iso, j_order, j_order_row, staff

router = APIRouter(prefix="/api/orders", tags=["orders"])
FILTERS = ("status", "q", "manager", "date_from", "date_to", "delivery", "source", "dup", "pay")


def _get(db: Session, order_id: int, user: User) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(404, "Замовлення не знайдено")
    if not svc.can_view(db, user, order):
        raise Forbidden()
    return order


def _full(db: Session, order: Order) -> dict:
    db.refresh(order)
    d = j_order(order)
    history = (db.query(AuditLog).options(selectinload(AuditLog.user))
               .filter(AuditLog.entity == "order", AuditLog.entity_id == order.id)
               .order_by(AuditLog.id.desc()).limit(200).all())
    d["history"] = [{"id": h.id, "user": h.user.display if h.user else "Система",
                     "action": ACTION_NAMES.get(h.action, h.action), "details": f_details(h.details) if h.details else "",
                     "created_at": iso(h.created_at)} for h in history]
    d["sms"] = [{"id": m.id, "text": m.text, "channel": m.channel, "status": m.status, "error": m.error,
                 "created_at": iso(m.created_at)}
                for m in db.query(SmsMessage).filter(SmsMessage.order_id == order.id).order_by(SmsMessage.id.desc())]
    d["others"] = [j_order_row(o) for o in svc.customer_orders(db, order.phone, exclude_id=order.id)]
    return d


def _items(data: dict) -> list[dict] | None:
    items = data.get("items")
    if items is None:
        return None
    if not isinstance(items, list):
        bad("items має бути списком")
    return [{"product_id": i.get("product_id") or "", "name": i.get("name", ""), "qty": i.get("qty", 1),
             "price": i.get("price", ""), "is_upsell": "1" if i.get("upsell") else "0",
             "upsell_for": i.get("upsell_for") or ""} for i in items if isinstance(i, dict)]


def _fields(data: dict) -> dict:
    return {k: data[k] for k in svc.ORDER_FIELDS if k in data}


# ------------------------------------------------------------------ список
@router.get("", response_model=OrderListOut)
def list_orders(request: Request, before: int = 0, limit: int = Query(100, le=500), counts: int = 1,
                db: Session = Depends(get_db), user: User = Depends(staff)):
    f = {k: (request.query_params.get(k) or "").strip() for k in FILTERS}
    base = svc.visible_orders_query(db, user)
    q = _apply(base, f)
    page_q = q.filter(Order.id < before) if before else q
    rows = (page_q.options(selectinload(Order.items)).order_by(Order.id.desc()).limit(limit + 1).all())
    out = {"items": [j_order_row(o) for o in rows[:limit]],
           "next": rows[limit - 1].id if len(rows) > limit else None}
    if counts:
        out["total"] = q.count()
        by_status = dict(_apply(base, f, with_status=False).with_entities(Order.status_id, func.count(Order.id))
                         .group_by(Order.status_id).all())
        out["counts"] = {str(k): v for k, v in by_status.items()}
        out["all"] = sum(by_status.values())
    return out


@router.get("/sources", response_model=list[str])
def sources(db: Session = Depends(get_db), user: User = Depends(staff)):
    rows = (db.query(Order.utm_source).filter(Order.utm_source != "").group_by(Order.utm_source)
            .order_by(func.count(Order.id).desc()).limit(50).all())
    return [r[0] for r in rows]


# ------------------------------------------------------------------ картка
@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    return _full(db, _get(db, order_id, user))


@router.post("", response_model=OrderOut)
def create_order(body: OrderIn, db: Session = Depends(get_db), user: User = Depends(staff)):
    data = body.model_dump(exclude_unset=True)
    fields = _fields(data)
    if not svc.normalize_phone(fields.get("phone")):
        bad("Вкажіть телефон")
    if user.role == "admin" and data.get("manager_id"):
        fields["manager_id"] = data["manager_id"]
    order = svc.create_order(db, fields, _items(data) or [], user, source="manual")
    sid = svc.to_int(data.get("status_id"))
    if sid and sid != order.status_id:
        status = db.get(Status, sid)
        if status:
            svc.change_status(db, order, status, user)
    svc.add_comment(db, order, data.get("note", ""), user)
    db.commit()
    return _full(db, order)


@router.patch("/{order_id}", response_model=OrderOut)
def update_order(order_id: int, body: OrderIn, db: Session = Depends(get_db), user: User = Depends(staff)):
    data = body.model_dump(exclude_unset=True)
    order = _get(db, order_id, user)
    version = data.get("version")
    if version and order.updated_at and version != order.updated_at.isoformat():
        raise HTTPException(409, "Замовлення щойно змінив інший користувач. Оновіть картку.")
    svc.update_order(db, order, _fields(data), user)
    items = _items(data)
    if items is not None:
        svc.set_items(db, order, items, user)
    if "manager_id" in data and user.role == "admin":
        mid = svc.to_int(data.get("manager_id"))
        svc.assign(db, order, db.get(User, mid) if mid else None, user)
    sid = svc.to_int(data.get("status_id"))
    if sid and sid != order.status_id:
        status = db.get(Status, sid)
        if status is None:
            bad("Невідомий статус")
        svc.change_status(db, order, status, user)
    # оновити час зміни навіть якщо змінився лише статус — для перевірки версії
    order.updated_at = utcnow()
    db.commit()
    return _full(db, order)


@router.post("/bulk", response_model=BulkOut)
def bulk(body: BulkIn, db: Session = Depends(get_db), user: User = Depends(staff)):
    data = body.model_dump(exclude_unset=True)
    ids = [svc.to_int(x) for x in data.get("ids", []) if svc.to_int(x)]
    action, value = data.get("action", ""), data.get("value")
    if not ids:
        bad("Не вибрано жодного замовлення")
    orders = [o for o in db.query(Order).filter(Order.id.in_(ids)).all() if svc.can_view(db, user, o)]
    done, errors, queued = 0, [], 0
    if action == "status":
        status = db.get(Status, svc.to_int(value))
        if status is None:
            bad("Невідомий статус")
        for o in orders:
            done += svc.change_status(db, o, status, user)
    elif action == "assign":
        if user.role == "warehouse":
            raise Forbidden()
        mid = svc.to_int(value)
        manager = db.get(User, mid) if mid else None
        for o in orders:
            svc.assign(db, o, manager, user)
            done += 1
    elif action == "ttn":
        todo = [o for o in orders if not o.ttn and o.delivery_method in CARRIERS]
        for o in todo:
            # з чергою — у фоні (інтерфейс оновиться подіями); без неї — одразу тут
            if queue.enqueue("create_ttn", o.id, user.id):
                queued += 1
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
    else:
        bad("Невідома дія")
    db.commit()
    return {"done": done, "queued": queued, "errors": errors[:20]}


@router.post("/{order_id}/take", response_model=OrderOut)
def take(order_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    order = _get(db, order_id, user)
    if user.role == "warehouse":
        raise Forbidden()
    if order.manager_id and order.manager_id != user.id and user.role != "admin":
        bad("Замовлення вже взяв інший менеджер", 409)
    svc.assign(db, order, user, user)
    db.commit()
    return _full(db, order)


@router.post("/{order_id}/comments", response_model=OrderOut)
def comment(order_id: int, body: TextIn, db: Session = Depends(get_db), user: User = Depends(staff)):
    data = body.model_dump(exclude_unset=True)
    order = _get(db, order_id, user)
    if not svc.add_comment(db, order, data.get("text", ""), user):
        bad("Порожній коментар")
    db.commit()
    return _full(db, order)


@router.get("/{order_id}/ttn/preview", response_model=TtnPreviewOut)
def ttn_preview(order_id: int, np_account_id: int = 0, db: Session = Depends(get_db), user: User = Depends(staff)):
    """Параметри ТТН за замовчуванням для вікна «Створення накладної» (лише Нова Пошта)."""
    from ..services import np as np_svc
    order = _get(db, order_id, user)
    if order.delivery_method != "novaposhta":
        return {"supported": False}
    if np_account_id:
        order.np_account_id = np_account_id  # лише для розрахунку, не зберігаємо
    acc = np_svc.pick_account(db, order)
    carrier = delivery.carrier_for(db, order)
    db.rollback()
    params = carrier.shipment_defaults(order)
    prepaid = bool(order.payment_method and order.payment_method.kind == "prepaid")
    if prepaid:
        params.update(cod_mode="none", cod_amount=0)
    return {"supported": True, "np_account_id": acc.id if acc else None, "params": params, "prepaid": prepaid,
            "sender": " · ".join(x for x in (acc.sender_name, acc.contact_name, acc.city_name, acc.warehouse_name) if x) if acc else "",
            "accounts": [{"id": a.id, "name": a.name or f"Ключ {a.id}", "office_id": a.office_id, "is_default": a.is_default}
                         for a in np_svc.accounts(db)]}


@router.post("/{order_id}/ttn", response_model=OrderOut)
def ttn_create(order_id: int, body: TtnIn | None = None, db: Session = Depends(get_db), user: User = Depends(staff)):
    order = _get(db, order_id, user)
    opts = body.model_dump(exclude_none=True) if body else None
    if opts and "seats" in opts:
        opts["seats"] = [dict(x) for x in opts["seats"]]
    try:
        delivery.create_ttn(db, order, user, opts)
        db.commit()
    except CarrierError as e:
        db.rollback()
        bad(str(e), 422)
    return _full(db, order)


@router.delete("/{order_id}/ttn", response_model=OrderOut)
def ttn_delete(order_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    order = _get(db, order_id, user)
    try:
        delivery.delete_ttn(db, order, user)
        db.commit()
    except CarrierError as e:
        db.rollback()
        bad(str(e), 422)
    return _full(db, order)


@router.post("/{order_id}/track", response_model=TrackOut)
def track(order_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    order = _get(db, order_id, user)
    res = delivery.sync_tracking(db, [order.id], force=True)
    if res["errors"]:
        bad("; ".join(res["errors"]), 422)
    out = _full(db, order)
    out["changed"] = bool(res["changed"])
    return out


@router.post("/{order_id}/sms", response_model=OrderOut)
def send_sms(order_id: int, body: SmsIn, db: Session = Depends(get_db), user: User = Depends(staff)):
    data = body.model_dump(exclude_unset=True)
    order = _get(db, order_id, user)
    text = sms_svc.render(data.get("text", ""), order, st.get(db, "company_name"))
    channel = data.get("channel") if data.get("channel") in ("sms", "viber", "hybrid") else "sms"
    if not text or not order.phone:
        bad("Порожній текст або немає телефону")
    sms_svc.queue(db, order, order.phone, text, channel)
    audit.log(db, user, "order", order.id, "sms", {"текст": text, "канал": channel})
    db.commit()
    return _full(db, order)


@router.post("/{order_id}/payments", response_model=OrderOut)
def add_payment(order_id: int, body: PaymentIn, db: Session = Depends(get_db), user: User = Depends(staff)):
    data = body.model_dump(exclude_unset=True)
    order = _get(db, order_id, user)
    amount = svc.to_money(data.get("amount"))
    if amount <= 0:
        bad("Вкажіть суму")
    p = Payment(kind="prepayment", amount=amount, status="received", method=data.get("method") or "card",
                reference=(data.get("reference") or "")[:255], received_amount=amount, received_at=utcnow())
    order.payments.append(p)
    order.prepayment = Decimal(order.prepayment or 0) + amount
    if order.payment_type == "cod":
        order.payment_type = "partial"
    svc.recalc(order)
    if order.payment_type == "partial" and order.cod_amount <= 0:
        order.payment_type = "prepaid"
        svc.recalc(order)
    if order.stock_shipped:
        payments.ensure_cod_payment(db, order)
    audit.log(db, user, "order", order.id, "payment", {"передоплата": amount, "метод": p.method})
    from ..services import events
    events.order_changed(db, order.id)
    db.commit()
    return _full(db, order)
