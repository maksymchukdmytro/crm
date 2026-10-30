"""API замовлень: список (курсор), картка, створення, зміни, масові дії, ТТН, оплати, SMS."""
from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import case, func
from sqlalchemy.orm import Session, selectinload

from ..carriers import CARRIERS, CarrierError
from ..db import get_db
from ..deps import Forbidden
from ..models import AuditLog, Customer, Order, OrderItem, Payment, SmsMessage, Status, User, utcnow
from ..routers.orders import _apply
from ..services import audit, delivery, payments, queue
from ..services import orders as svc
from ..services import settings as st
from ..services import sms as sms_svc
from ..services.audit import ACTION_NAMES
from ..web import f_details
from .schemas import BulkIn, BulkOut, DocumentsOut, HistoryOut, OrderIn, OrderListOut, OrderOut, PaymentIn, PrepayConfirmIn, ReceiptIn, NpRegistryOut, SmsIn, TextIn, TrackOut, TtnCreatedOut, TtnIn, TtnPreviewOut
from .common import bad, iso, j_order, j_order_row, staff

router = APIRouter(prefix="/api/orders", tags=["orders"])
FILTERS = ("status", "q", "manager", "date_from", "date_to", "delivery", "source", "dup", "pay", "stage", "src", "entity", "pm", "mark", "remind", "ttn")


def _get(db: Session, order_id: int, user: User) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(404, "Замовлення не знайдено")
    if not svc.can_view(db, user, order):
        raise Forbidden()
    return order


def _label_kind(db: Session, order: Order) -> str:
    """Що друкувати кнопкою «Друк» біля ТТН: rozetka — маркування Rozetka, carrier — наклейка перевізника, "" — нічого."""
    from ..services import marketplaces as mp
    if not order.ttn:
        return ""
    if mp.is_rozetka_delivery(order):
        return "rozetka"
    return "carrier" if delivery.carrier_for(db, order) is not None else ""


@router.get("/{order_id}/label", responses={200: {"content": {"application/pdf": {}}, "description": "PDF наклейки"}})
def order_label(order_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    """Наклейка для друку: маркування ROZETKA Delivery (ТТН RMP-…) з API Rozetka або наклейка перевізника (НП 100×100)."""
    from fastapi.responses import Response
    from ..services import marketplaces as mp
    order = _get(db, order_id, user)
    kind = _label_kind(db, order)
    if not kind:
        bad("Для цього замовлення немає наклейки: спершу потрібна ТТН", 404)
    try:
        pdf = mp.rozetka_label(db, order) if kind == "rozetka" else delivery.carrier_for(db, order).label_pdf(order)
    except (mp.MarketplaceError, CarrierError) as e:
        bad(str(e), 422)
    name = f"{'rozetka' if kind == 'rozetka' else 'label'}-{order.ttn}.pdf"
    if order.label_printed_at is None:
        order.label_printed_at = utcnow()
        from ..services import events as ev
        ev.order_changed(db, order.id)
        db.commit()
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="{name}"'})


@router.get("/{order_id}/documents", response_model=DocumentsOut)
def order_documents(order_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    """Дані для друку з поточного замовлення (без видачі документа). Видача з номером — POST /api/orders/{id}/documents/{kind}."""
    from ..services import documents
    return documents.build_data(db, _get(db, order_id, user))


def _full(db: Session, order: Order, user: User | None = None) -> dict:
    from ..services import checklist
    db.refresh(order)
    d = j_order(order)
    d["todo"] = checklist.build(db, order)
    from ..models import IssuedDocument
    d["documents"] = [{"id": x.id, "kind": x.kind, "number_text": x.number_text, "print_count": x.print_count or 0}
                      for x in db.query(IssuedDocument).filter(IssuedDocument.order_id == order.id, IssuedDocument.state == "active")
                      .order_by(IssuedDocument.id)]
    # собівартість і прибуток — лише адміністратору
    d["items_cost"] = float(order.items_cost) if user is not None and user.role == "admin" else None
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
    d["label"] = _label_kind(db, order)
    d["customer"] = None
    if order.customer is not None:
        from ..services import customers as cust
        c, cs = order.customer, cust.stats_for(db, [order.customer_id]).get(order.customer_id, cust.EMPTY_STATS)
        d["customer"] = {"id": c.id, "name": c.name, "group": c.group.name if c.group else "",
                         "group_color": c.group.color if c.group else "", "blacklisted": c.is_blacklisted,
                         "blacklist_reason": c.blacklist_reason, "comment": c.comment, "orders": cs["orders"],
                         "delivered": cs["delivered"], "refused": cs["refused"], "buyout_rate": cs["buyout_rate"],
                         "sum_delivered": cs["sum_delivered"]}
    from ..models import CheckboxCashier
    from ..services import checkbox as cb
    cashiers = {c.id: c for c in db.query(CheckboxCashier).all()}
    d["receipts"] = [{"id": r.id, "kind": r.kind, "kind_name": cb.KINDS.get(r.kind, r.kind), "status": r.status,
                      "fiscal_code": r.fiscal_code, "total": float(r.total or 0), "error": r.error, "url": cb.receipt_url(r),
                      "test": r.test, "cashier": cashiers[r.cashier_id].name if r.cashier_id in cashiers else "",
                      "created_at": iso(r.created_at)} for r in cb.receipts(db, order)]
    d["checkbox_ready"] = any(c.is_active for c in cashiers.values())
    return d


def _items(data: dict) -> list[dict] | None:
    items = data.get("items")
    if items is None:
        return None
    if not isinstance(items, list):
        bad("items має бути списком")
    return [{"product_id": i.get("product_id") or "", "name": i.get("name", ""), "qty": i.get("qty", 1),
             "price": i.get("price", ""), "is_upsell": "1" if i.get("upsell") else "0",
             "upsell_for": i.get("upsell_for") or "", "variant_id": i.get("variant_id") or ""} for i in items if isinstance(i, dict)]


def _fields(data: dict) -> dict:
    return {k: data[k] for k in svc.ORDER_FIELDS if k in data}


# ------------------------------------------------------------------ список
@router.get("", response_model=OrderListOut)
def list_orders(request: Request, before: int = 0, after: int = 0, sort: str = "new", tab: str = "", limit: int = Query(100, le=500), counts: int = 1,
                db: Session = Depends(get_db), user: User = Depends(staff)):
    """Курсор: sort=new — найновіші вгорі (before=<id>), sort=old — найстаріші вгорі («Несортовані», after=<id>).
    Ліди: stage=lead&tab=open|new|no_answer|callback|duplicate|refused|converted|all, sort=wait — хто чекає найдовше (без курсора, до 500)."""
    from ..services import leads
    f = {k: (request.query_params.get(k) or "").strip() for k in FILTERS}
    base = svc.visible_orders_query(db, user)
    lead_tab = tab if f.get("stage") == "lead" and tab in leads.TABS else ""
    if lead_tab:
        f_nostage = {**f, "stage": "", "status": ""}
        q = leads.apply_tab(db, _apply(base, f_nostage), lead_tab)
    else:
        q = _apply(base, f)
    old = sort == "old"
    if sort == "wait":
        rows = (q.options(selectinload(Order.items), selectinload(Order.status), selectinload(Order.customer).selectinload(Customer.group),
                          selectinload(Order.payment_method)).order_by(*leads.wait_order(db)).limit(500).all())
        out = {"items": [j_order_row(o) for o in rows], "next": None, "groups": []}
        if counts:
            out["total"] = len(rows)
            if lead_tab:
                out["lead_tabs"] = leads.tab_counts(db, _apply(base, {**f, "stage": "", "status": ""}))
        return out
    if old:
        page_q = q.filter(Order.id > after) if after else q
        order_by = Order.id.asc()
    else:
        page_q = q.filter(Order.id < before) if before else q
        order_by = Order.id.desc()
    rows = (page_q.options(selectinload(Order.items).selectinload(OrderItem.product), selectinload(Order.items).selectinload(OrderItem.variant),
                           selectinload(Order.customer).selectinload(Customer.group), selectinload(Order.payment_method))
            .order_by(order_by).limit(limit + 1).all())
    page = rows[:limit]
    out = {"items": [j_order_row(o) for o in page],
           "next": rows[limit - 1].id if len(rows) > limit else None,
           "groups": _day_groups(db, q, page)}
    if counts:
        out["total"] = q.count()
        if lead_tab:
            out["lead_tabs"] = leads.tab_counts(db, _apply(base, {**f, "stage": "", "status": ""}))
        by_status = dict(_apply(base, f, with_status=False).with_entities(Order.status_id, func.count(Order.id))
                         .group_by(Order.status_id).all())
        out["counts"] = {str(k): v for k, v in by_status.items()}
        out["all"] = sum(by_status.values())
    return out


def _has_reasons(db: Session) -> bool:
    from ..models import StatusReason
    return db.query(StatusReason.id).filter(StatusReason.is_active.is_(True)).first() is not None


def _day_groups(db: Session, q, page: list[Order]) -> list[dict]:
    """Рядки-групи за днями: «Сьогодні, 29 жовтня · 10 замовлень · 12 316 ₴». Сума — без скасованих і дублів."""
    if not page:
        return []
    from ..services.stats import local_expr, to_local
    days = sorted({to_local(o.created_at).date() for o in page if o.created_at})
    day = func.date(local_expr(Order.created_at))
    excluded = [sid for (sid,) in db.query(Status.id).filter(Status.code.in_(("cancelled", "duplicate", "lead_refused")))]
    paid = func.sum(case((Order.status_id.in_(excluded), 0), else_=Order.total)) if excluded else func.sum(Order.total)
    rows = (q.with_entities(day, func.count(Order.id), func.coalesce(paid, 0)).filter(day.in_(days))
            .group_by(day).order_by(None).all())
    return [{"day": d.isoformat(), "count": int(n), "sum": float(s or 0)} for d, n, s in rows]


@router.get("/sources", response_model=list[str])
def sources(db: Session = Depends(get_db), user: User = Depends(staff)):
    rows = (db.query(Order.utm_source).filter(Order.utm_source != "").group_by(Order.utm_source)
            .order_by(func.count(Order.id).desc()).limit(50).all())
    return [r[0] for r in rows]


# ------------------------------------------------------------------ картка
@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    return _full(db, _get(db, order_id, user), user)


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
    return _full(db, order, user)


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
        if status.code == "cancelled" and not order.reason_id and _has_reasons(db):
            bad("Вкажіть причину відмови")
        svc.change_status(db, order, status, user)
    # оновити час зміни навіть якщо змінився лише статус — для перевірки версії
    order.updated_at = utcnow()
    db.commit()
    return _full(db, order, user)


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
    elif action == "fiscalize":
        from ..services import checkbox as cb
        for o in orders:
            try:
                rec = cb.create_receipt(db, o, "sell", user)
                db.commit()
                if rec.status == "error":
                    errors.append(f"№{o.id}: {rec.error}")
                else:
                    done += 1
            except cb.CheckboxError as e:
                db.rollback()
                errors.append(f"№{o.id}: {e}")
    elif action == "registry":
        from ..services import np as np_svc
        res = np_svc.add_to_registry(db, orders, user)
        done = res["done"]
        errors.extend(res["errors"])
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
    return _full(db, order, user)


@router.post("/{order_id}/comments", response_model=OrderOut)
def comment(order_id: int, body: TextIn, db: Session = Depends(get_db), user: User = Depends(staff)):
    data = body.model_dump(exclude_unset=True)
    order = _get(db, order_id, user)
    if not svc.add_comment(db, order, data.get("text", ""), user):
        bad("Порожній коментар")
    db.commit()
    return _full(db, order, user)


@router.get("/{order_id}/ttn/preview", response_model=TtnPreviewOut)
def ttn_preview(order_id: int, np_account_id: int = 0, city_ref: str = "", db: Session = Depends(get_db), user: User = Depends(staff)):
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
    extra = {}
    if city_ref:  # місто, вибране у вікні ТТН, — лише для розрахунку
        order.city_ref = city_ref
    try:  # вартість і дата — орієнтовні: помилка НП не заважає створити ТТН
        extra.update(carrier.price(order, params))
        extra["eta"] = carrier.delivery_date(order, params.get("service_type") or "WarehouseWarehouse")
    except Exception:  # noqa: BLE001
        pass
    db.rollback()
    return {"supported": True, "np_account_id": acc.id if acc else None, "params": params, "prepaid": prepaid, **extra,
            "recipient": " · ".join(x for x in (order.customer_name, order.phone and f"+{order.phone}") if x),
            "city_name": order.city_name or "", "city_ref": order.city_ref or "", "warehouse_name": order.warehouse_name or "",
            "warehouse_ref": order.warehouse_ref or "",
            "sender": " · ".join(x for x in (acc.sender_name, acc.contact_name, acc.city_name, acc.warehouse_name) if x) if acc else "",
            "accounts": [{"id": a.id, "name": a.name or f"Ключ {a.id}", "office_id": a.office_id, "is_default": a.is_default}
                         for a in np_svc.accounts(db)]}


@router.post("/{order_id}/ttn", response_model=TtnCreatedOut)
def ttn_create(order_id: int, body: TtnIn | None = None, db: Session = Depends(get_db), user: User = Depends(staff)):
    order = _get(db, order_id, user)
    opts = body.model_dump(exclude_none=True) if body else {}
    after = opts.pop("after", None) or {}
    for k in ("city_name", "city_ref", "warehouse_name", "warehouse_ref"):  # місто й відділення з вікна ТТН
        if k in opts:
            setattr(order, k, str(opts.pop(k))[:255])
    if "seats" in opts:
        opts["seats"] = [dict(x) for x in opts["seats"]]
    try:
        delivery.create_ttn(db, order, user, opts or None)
        db.commit()
    except CarrierError as e:
        db.rollback()
        bad(str(e), 422)
    errors: list[str] = []
    if after.get("add_registry") and order.delivery_method == "novaposhta":
        from ..services import np as np_svc
        errors += np_svc.add_to_registry(db, [order], user)["errors"]
    if after.get("send_sms"):
        try:
            _send_ttn_sms(db, order, user)
        except HTTPException as e:
            errors.append(str(e.detail))
    if after.get("set_shipped"):
        shipped = svc.status_by_code(db, "shipped")
        if shipped is not None and shipped.id != order.status_id:
            svc.change_status(db, order, shipped, user)
    db.commit()
    out = _full(db, order, user)
    out["label_url"] = f"/api/orders/{order.id}/label" if after.get("print_label") else None
    out["after_errors"] = errors
    return out


def _send_ttn_sms(db: Session, order: Order, user: User):
    from ..services import checklist
    tpl, channel = checklist.sms_ttn_text(db)
    if not tpl:
        bad("Немає шаблону SMS з {ttn} або не підключено SMS")
    text = sms_svc.render(tpl, order, st.get(db, "company_name"))
    if not text or not order.phone:
        bad("Порожній текст або немає телефону")
    sms_svc.queue(db, order, order.phone, text, channel if channel in ("sms", "viber", "hybrid") else "sms")
    audit.log(db, user, "order", order.id, "sms", {"текст": text, "канал": channel})


@router.post("/{order_id}/sms-ttn", response_model=OrderOut)
def send_ttn_sms(order_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    """«Що лишилось» → SMS з ТТН: шаблон, у якому є {ttn}."""
    order = _get(db, order_id, user)
    if not order.ttn:
        bad("Спершу створіть ТТН")
    _send_ttn_sms(db, order, user)
    db.commit()
    return _full(db, order, user)


@router.post("/{order_id}/registry", response_model=NpRegistryOut)
def add_registry(order_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    """Додати ТТН у реєстр НП на сьогодні (один реєстр на ключ НП за день)."""
    from ..services import np as np_svc
    order = _get(db, order_id, user)
    res = np_svc.add_to_registry(db, [order], user)
    db.commit()
    if not res["done"] and res["errors"]:
        bad(res["errors"][0], 422)
    return {"done": res["done"], "errors": res["errors"], "number": order.np_registry_ref}


@router.post("/{order_id}/prepayment/confirm", response_model=OrderOut)
def confirm_prepayment(order_id: int, body: PrepayConfirmIn, db: Session = Depends(get_db), user: User = Depends(staff)):
    """Позначка ✓ біля передоплати: кошти надійшли на рахунок юрособи (хто й коли підтвердив)."""
    from ..models import LegalEntityAccount
    order = _get(db, order_id, user)
    need = Decimal(order.prepayment or 0) if order.payment_type == "partial" else Decimal(order.total or 0)
    if need <= 0:
        bad("Вкажіть суму передоплати")
    got = sum((p.amount for p in order.payments if p.kind == "prepayment" and p.status == "received"), Decimal(0))
    acc = db.get(LegalEntityAccount, body.account_id) if body.account_id else None
    now = utcnow()
    expected = [p for p in order.payments if p.kind == "prepayment" and p.status == "expected"]
    if expected:
        p = expected[0]
        p.status, p.received_amount, p.received_at = "received", p.amount, now
    elif got < need:
        p = Payment(kind="prepayment", amount=need - got, status="received", method=(acc.kind if acc else "card"),
                    received_amount=need - got, received_at=now)
        order.payments.append(p)
    else:
        p = next(x for x in order.payments if x.kind == "prepayment" and x.status == "received")
    p.account_id = acc.id if acc else p.account_id
    p.confirmed_by_id, p.confirmed_at = user.id, now
    audit.log(db, user, "order", order.id, "payment", {"передоплата надійшла": need, "рахунок": acc.name if acc else ""})
    from ..services import events
    events.order_changed(db, order.id)
    db.commit()
    return _full(db, order, user)


@router.get("/{order_id}/history", response_model=HistoryOut)
def order_history(order_id: int, kind: str = "all", db: Session = Depends(get_db), user: User = Depends(staff)):
    """Історія для бічної панелі: журнал дій, коментарі, SMS — нові зверху; kind=all|status|sms|comments."""
    from ..models import OrderComment
    order = _get(db, order_id, user)
    ev = []
    if kind in ("all", "status"):
        for h in (db.query(AuditLog).options(selectinload(AuditLog.user))
                  .filter(AuditLog.entity == "order", AuditLog.entity_id == order.id).order_by(AuditLog.id.desc()).limit(300)):
            if kind == "status" and h.action != "status":
                continue
            if h.action in ("sms", "comment"):
                continue
            ev.append({"kind": "status" if h.action == "status" else "other", "text": ACTION_NAMES.get(h.action, h.action),
                       "details": f_details(h.details) if h.details else "", "user": h.user.display if h.user else "Система",
                       "at": iso(h.created_at), "_t": h.created_at})
    if kind in ("all", "sms"):
        for m in db.query(SmsMessage).filter(SmsMessage.order_id == order.id).order_by(SmsMessage.id.desc()).limit(100):
            ev.append({"kind": "sms", "text": f"{m.channel.upper()} · {({'sent': 'відправлено', 'failed': 'помилка', 'queued': 'в черзі'}).get(m.status, m.status)}",
                       "details": m.text + (f" — {m.error}" if m.error else ""), "user": "", "at": iso(m.created_at), "_t": m.created_at})
    if kind in ("all", "comments"):
        for c in db.query(OrderComment).options(selectinload(OrderComment.user)).filter(OrderComment.order_id == order.id).order_by(OrderComment.id.desc()):
            ev.append({"kind": "comment", "text": "Коментар", "details": c.text, "user": c.user.display if c.user else "Система",
                       "at": iso(c.created_at), "_t": c.created_at})
    ev.sort(key=lambda x: x.pop("_t") or utcnow(), reverse=True)
    return {"events": ev}


@router.post("/{order_id}/receipts", response_model=OrderOut)
def receipt_create(order_id: int, body: ReceiptIn, db: Session = Depends(get_db), user: User = Depends(staff)):
    """Створити чек Checkbox вручну (продажу, повернення, передоплати, післяплати)."""
    from ..services import checkbox as cb
    order = _get(db, order_id, user)
    try:
        rec = cb.create_receipt(db, order, body.kind, user)
        db.commit()
    except cb.CheckboxError as e:
        db.rollback()
        bad(str(e), 422)
    if rec.status == "error":
        bad(rec.error, 422)
    return _full(db, order, user)


@router.post("/{order_id}/fiscalize", response_model=OrderOut)
def fiscalize(order_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    """Ручна фіскалізація в один клік: чек продажу на суму замовлення через касу юрособи замовлення."""
    from ..services import checkbox as cb
    order = _get(db, order_id, user)
    try:
        rec = cb.create_receipt(db, order, "sell", user)
        db.commit()
    except cb.CheckboxError as e:
        db.rollback()
        bad(str(e), 422)
    if rec.status == "error":
        bad(rec.error, 422)
    return _full(db, order, user)


@router.delete("/{order_id}/ttn", response_model=OrderOut)
def ttn_delete(order_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    order = _get(db, order_id, user)
    try:
        delivery.delete_ttn(db, order, user)
        db.commit()
    except CarrierError as e:
        db.rollback()
        bad(str(e), 422)
    return _full(db, order, user)


@router.post("/{order_id}/track", response_model=TrackOut)
def track(order_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    order = _get(db, order_id, user)
    res = delivery.sync_tracking(db, [order.id], force=True)
    if res["errors"]:
        bad("; ".join(res["errors"]), 422)
    out = _full(db, order, user)
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
    return _full(db, order, user)


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
    return _full(db, order, user)
