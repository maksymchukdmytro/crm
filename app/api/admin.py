"""API: оплати й звірка, звіти, журнал дій, налаштування, користувачі."""
from __future__ import annotations

import re
import uuid
from pathlib import Path

import secrets
from datetime import timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..carriers import CarrierError
from ..carriers.novaposhta import NovaPoshta
from ..config import config
from ..db import get_db
from ..models import CHECKBOX_PAYMENTS, ROLES, STOCK_ACTIONS, AuditLog, CheckboxCashier, MarketplaceShop, NpAccount, NpStatusRule, Office, Order, OrderMark, OrderSource, Payment, PaymentMethod, StatusReason, SmsMessage, SmsTemplate, Status, User
from ..routers.payments import parse_registry
from ..routers.settings import CHECKBOXES, SECTION_KEYS
from ..security import hash_password
from ..services import audit
from ..services import np as np_svc
from ..services import payments as pay_svc
from ..services import reports as rep
from ..services import settings as st
from ..services import sms as sms_svc
from ..services.audit import ACTION_NAMES
from ..services.orders import normalize_phone, to_int
from ..services.reports import period_bounds
from ..web import f_details, parse_date, today_local
from .schemas import SystemOut, AuditOut, DoneOut, Ok, PaymentsOut, ReceiveIn, RegistryOut, ReportOut, SettingsOut, SmsTemplateIn, SmsTestIn, StatusIn, UserIn, UserOut, PaymentMethodIn, SourceIn, NpAccountIn, NpRuleIn, ShopCheckOut, ShopIn, ShopSyncOut, CashierCheckOut, CashierIn, TestDataIn, TestDataOut, LegalEntityIn
from .common import admin, bad, iso, j_payment, j_payment_method, j_source, j_status, j_user, sales

router = APIRouter(prefix="/api", tags=["admin"])


# ---------------------------------------------------------------- оплати
@router.get("/payments", response_model=PaymentsOut)
def payments(status: str = "collected", method: str = "", db: Session = Depends(get_db), user: User = Depends(admin)):
    q = db.query(Payment).options(selectinload(Payment.order)).filter(Payment.kind == "cod")
    if status:
        q = q.filter(Payment.status == status)
    if method:
        q = q.filter(Payment.method == method)
    rows = q.order_by(Payment.id.desc()).limit(1000).all()
    agg = (db.query(Payment.status, func.count(Payment.id), func.coalesce(func.sum(Payment.amount), 0))
           .filter(Payment.kind == "cod").group_by(Payment.status).all())
    out = []
    for p in rows:
        d = j_payment(p)
        d.update(ttn=p.order.ttn, customer=p.order.customer_name)
        out.append(d)
    return {"items": out, "totals": {s: {"count": c, "sum": float(v)} for s, c, v in agg}}


@router.post("/payments/receive", response_model=DoneOut)
def payments_receive(body: ReceiveIn, db: Session = Depends(get_db), user: User = Depends(admin)):
    data = body.model_dump(exclude_unset=True)
    ids = [to_int(x) for x in data.get("ids", []) if to_int(x)]
    n = 0
    for p in db.query(Payment).filter(Payment.id.in_(ids)).all():
        if p.status in ("expected", "collected"):
            pay_svc.mark_received(db, p, user, reference=str(data.get("reference") or "")[:255])
            n += 1
    db.commit()
    return {"done": n}


@router.post("/payments/import", response_model=RegistryOut)
async def payments_import(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db),
                          user: User = Depends(admin)):
    rows, err = parse_registry(await file.read())
    if err:
        bad(err)
    report = pay_svc.import_registry(db, rows, user)
    db.commit()
    return {k: [{a: (float(b) if isinstance(b, Decimal) else b) for a, b in it.items()} for it in v[:500]]
            for k, v in report.items()}


# ---------------------------------------------------------------- звіти
def _bucket(b: rep.Bucket) -> dict:
    return {"leads": b.leads, "unique": b.unique, "approved": b.approved, "shipped": b.shipped,
            "delivered": b.delivered, "refused": b.refused, "revenue": float(b.revenue), "cost": float(b.cost),
            "profit": float(b.profit), "avg_check": float(b.avg_check), "approve_rate": round(b.approve_rate, 2),
            "buyout_rate": round(b.buyout_rate, 2)}


@router.get("/reports", response_model=ReportOut)
def reports(date_from: str = "", date_to: str = "", dim: str = "utm_source", manager: int = 0,
            db: Session = Depends(get_db), user: User = Depends(sales)):
    t = today_local()
    d2 = parse_date(date_to, t)
    d1 = parse_date(date_from, d2 - timedelta(days=29))
    if d1 > d2:
        d1, d2 = d2, d1
    d1 = max(d1, d2 - timedelta(days=366))
    if dim not in rep.DIMENSIONS:
        dim = "utm_source"
    if user.role == "manager":
        manager = user.id
    r = rep.build(db, d1, d2, dim, manager or None)
    return {
        "date_from": d1.isoformat(), "date_to": d2.isoformat(), "dim": dim, "dims": rep.DIMENSIONS,
        "total": _bucket(r["total"]),
        "groups": [{"name": k, **_bucket(b)} for k, b in r["groups"]],
        "days": [{"day": d.isoformat(), "leads": b.leads, "approved": b.approved} for d, b in r["days"]],
        "products": [{"name": k, **{a: (float(v) if isinstance(v, Decimal) else v) for a, v in p.items()}}
                     for k, p in r["products"]],
    }


# ---------------------------------------------------------------- журнал
@router.get("/audit", response_model=AuditOut)
def audit_log(entity: str = "", user_id: int = 0, action: str = "", date_from: str = "", date_to: str = "",
              before: int = 0, limit: int = Query(100, le=300), db: Session = Depends(get_db),
              user: User = Depends(admin)):
    q = db.query(AuditLog).options(selectinload(AuditLog.user))
    if entity:
        q = q.filter(AuditLog.entity == entity)
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    if action:
        q = q.filter(AuditLog.action == action)
    d1, d2 = parse_date(date_from), parse_date(date_to)
    if d1 or d2:
        start, end = period_bounds(d1 or d2, d2 or d1)
        q = q.filter(AuditLog.created_at >= start, AuditLog.created_at < end)
    if before:
        q = q.filter(AuditLog.id < before)
    rows = q.order_by(AuditLog.id.desc()).limit(limit + 1).all()
    return {"items": [{"id": r.id, "user": r.user.display if r.user else "Система", "entity": r.entity,
                       "entity_id": r.entity_id, "action": r.action, "action_name": ACTION_NAMES.get(r.action, r.action),
                       "details": f_details(r.details) if r.details else "", "created_at": iso(r.created_at)}
                      for r in rows[:limit]],
            "next": rows[limit - 1].id if len(rows) > limit else None,
            "actions": ACTION_NAMES}


# ---------------------------------------------------------------- стан системи
@router.get("/system", response_model=SystemOut)
def system(db: Session = Depends(get_db), user: User = Depends(admin)):
    from ..services import monitoring
    return monitoring.system_status(db)


@router.post("/system/alert-test", response_model=Ok)
def alert_test(db: Session = Depends(get_db), user: User = Depends(admin)):
    from ..services import monitoring
    token, chat = st.get(db, "alert_tg_token"), st.get(db, "alert_tg_chat")
    if not token or not chat:
        bad("Вкажіть токен бота і ID чату в налаштуваннях сповіщень")
    ok, info = monitoring.send_telegram(token, chat, f"🔔 {st.get(db, 'company_name')}: тестове сповіщення CRM — усе працює")
    if not ok:
        bad(f"Telegram відповів помилкою: {info}", 422)
    return {"ok": True}


@router.get("/system/test-data", response_model=TestDataOut)
def test_data_counts(db: Session = Depends(get_db), user: User = Depends(admin)):
    from ..services import test_data
    return {**test_data.counts(db), "message": ""}


@router.post("/system/test-data", response_model=TestDataOut)
def test_data_action(body: TestDataIn, db: Session = Depends(get_db), user: User = Depends(admin)):
    """Тестові товари й замовлення для перевірки статистики (позначені, видаляються одним кліком)."""
    from ..services import test_data
    if body.action == "create":
        r = test_data.create(db, user)
        msg = f"Створено {r['created_orders']} тестових замовлень за останні 30 днів і 10 тестових товарів"
    else:
        r = test_data.delete(db)
        msg = f"Видалено тестових замовлень: {r['deleted_orders']}, товарів: {r['deleted_products']}"
        if r["disabled_products"]:
            msg += f" (ще {r['disabled_products']} вимкнено — вони є в справжніх замовленнях)"
    audit.log(db, user, "system", None, f"test_data_{body.action}", {"повідомлення": msg})
    db.commit()
    return {"products": r["products"], "orders": r["orders"], "message": msg}


# ---------------------------------------------------------------- налаштування
NP_FIELDS = ("name", "sender_ref", "sender_name", "contact_ref", "contact_name", "sender_phone", "city_name", "city_ref",
             "warehouse_name", "warehouse_ref", "payer", "cargo_type", "service_type", "cod_mode", "cod_payer",
             "info_comment", "info_items", "info_item_ids", "seat_size", "description", "office_id", "legal_entity_id",
             "is_default", "is_active")


def j_np_account(a: NpAccount) -> dict:
    d = {f: getattr(a, f) for f in NP_FIELDS}
    d.update(id=a.id, api_key="********" if a.api_key else "", default_weight=float(a.default_weight or 0.5),
             directory=a.directory or {})
    return d


def j_shop(x: MarketplaceShop) -> dict:
    return {"id": x.id, "kind": x.kind, "name": x.name, "login": x.login, "secret": "********" if x.secret else "",
            "office_id": x.office_id, "source_id": x.source_id, "import_status_id": x.import_status_id,
            "extra_field": x.extra_field, "status_map": x.status_map or {}, "payment_map": x.payment_map or {},
            "delivery_map": x.delivery_map or {}, "directory": x.directory or {}, "since": iso(x.since),
            "last_sync_at": iso(x.last_sync_at), "last_error": x.last_error or "", "imported": x.imported or 0,
            "is_active": x.is_active}


def j_cashier(c: CheckboxCashier) -> dict:
    return {"id": c.id, "name": c.name, "license_key": "********" if c.license_key else "", "login": c.login,
            "password": "********" if c.password else "", "test_mode": c.test_mode, "auto_shift": c.auto_shift,
            "legal_entity_id": c.legal_entity_id, "condition": c.condition, "condition_value": c.condition_value, "sort": c.sort, "is_active": c.is_active,
            "last_error": c.last_error or ""}


def _settings_payload(request: Request, db: Session) -> dict:
    s = st.get_all(db)
    values = {k: ("********" if (k in st.SECRET_KEYS and v) else v) for k, v in s.items() if k not in st.INTERNAL_KEYS}
    return {
        "values": values,
        "secret_keys": sorted(st.SECRET_KEYS),
        "webhook_url": str(request.base_url).rstrip("/") + config.ROOT_PATH + "/api/v1/orders?key=" + s["webhook_key"],
        "statuses": [j_status(x) for x in db.query(Status).order_by(Status.sort, Status.id).all()],
        "users": [j_user(u) for u in db.query(User).order_by(User.is_active.desc(), User.role, User.username).all()],
        "sms_templates": [{"id": t.id, "status_id": t.status_id, "channel": t.channel, "text": t.text,
                           "active": t.is_active} for t in db.query(SmsTemplate).order_by(SmsTemplate.id).all()],
        "placeholders": sms_svc.PLACEHOLDERS,
        "sms_log": [{"id": m.id, "phone": m.phone, "text": m.text, "status": m.status, "error": m.error,
                     "channel": m.channel, "created_at": iso(m.created_at)}
                    for m in db.query(SmsMessage).order_by(SmsMessage.id.desc()).limit(30).all()],
        "stock_actions": STOCK_ACTIONS,
        "roles": ROLES,
        "payment_methods": [j_payment_method(m) for m in db.query(PaymentMethod).order_by(PaymentMethod.sort, PaymentMethod.id)],
        "order_sources": [{**j_source(x), "office_id": x.office_id} for x in db.query(OrderSource).order_by(OrderSource.sort, OrderSource.id)],
        "offices": [j_source(x) for x in db.query(Office).order_by(Office.sort, Office.id)],
        "reasons": [j_source(x) for x in db.query(StatusReason).order_by(StatusReason.sort, StatusReason.id)],
        "marks": [j_source(x) for x in db.query(OrderMark).order_by(OrderMark.sort, OrderMark.id)],
        "checkbox_payments": CHECKBOX_PAYMENTS,
        "np_accounts": [j_np_account(a) for a in np_svc.accounts(db, active_only=False)],
        "np_status_rules": [{"id": r.id, "np_code": r.np_code, "status_id": r.status_id,
                             "except_ids": [int(x) for x in r.except_ids or []]} for r in np_svc.rules(db)],
        "np_statuses": np_svc.NP_STATUSES,
        "shops": [j_shop(x) for x in db.query(MarketplaceShop).order_by(MarketplaceShop.id)],
        "cashiers": [j_cashier(c) for c in db.query(CheckboxCashier).order_by(CheckboxCashier.sort, CheckboxCashier.id)],
        "legal_entities": _legal_entities(db),
    }


def _legal_entities(db: Session) -> list[dict]:
    from sqlalchemy import func
    from ..models import LegalEntity
    counts = dict(db.query(Order.legal_entity_id, func.count(Order.id)).filter(Order.legal_entity_id.isnot(None))
                  .group_by(Order.legal_entity_id).all())
    cashiers = {c.legal_entity_id: c.name or f"Каса {c.id}" for c in db.query(CheckboxCashier)
                .filter(CheckboxCashier.is_active.is_(True), CheckboxCashier.legal_entity_id.isnot(None))
                .order_by(CheckboxCashier.sort.desc())}
    return [{"id": x.id, "name": x.name, "code": x.code, "iban": x.iban, "is_default": x.is_default,
             "code_label": x.code_label or "РНОКПП", "address": x.address or "", "bank": x.bank or "", "phone": x.phone or "",
             "vat_note": x.vat_note or "", "signer": x.signer or "",
             "is_active": x.is_active, "sort": x.sort, "orders": counts.get(x.id, 0), "cashier": cashiers.get(x.id, "")}
            for x in db.query(LegalEntity).order_by(LegalEntity.sort, LegalEntity.id)]


@router.get("/settings", response_model=SettingsOut)
def settings_get(request: Request, db: Session = Depends(get_db), user: User = Depends(admin)):
    return _settings_payload(request, db)


@router.post("/settings/np/load-sender", response_model=SettingsOut)
def np_load_sender(request: Request, db: Session = Depends(get_db), user: User = Depends(admin)):
    try:
        data = NovaPoshta(st.get_all(db)).load_sender()
    except CarrierError as e:
        bad(str(e), 422)
    for k in ("np_sender_ref", "np_contact_ref", "np_sender_phone"):
        st.set_value(db, k, data[k])
    db.commit()
    out = _settings_payload(request, db)
    out["message"] = f"Відправника завантажено: {data['sender_name']}, контакт {data['contact_name']}"
    return out


@router.post("/settings/webhook/regenerate", response_model=SettingsOut)
def webhook_regenerate(request: Request, db: Session = Depends(get_db), user: User = Depends(admin)):
    st.set_value(db, "webhook_key", secrets.token_urlsafe(24))
    audit.log(db, user, "settings", None, "update", {"поля": ["webhook_key"]})
    db.commit()
    return _settings_payload(request, db)


@router.put("/settings/statuses", response_model=SettingsOut)
def statuses_save(request: Request, body: list[StatusIn], db: Session = Depends(get_db), user: User = Depends(admin)):
    data = [b.model_dump(exclude_unset=True) for b in body]
    by_id = {s.id: s for s in db.query(Status).all()}
    for d in data:
        s = by_id.get(to_int(d.get("id")))
        if s is None:
            continue
        s.name = str(d.get("name") or s.name).strip()[:80]
        s.color = str(d.get("color") or s.color)[:9]
        s.sort = to_int(d.get("sort"), s.sort)
        if d.get("stock_action") in STOCK_ACTIONS:
            s.stock_action = d["stock_action"]
        s.counts_as_approved = bool(d.get("approved"))
        s.is_final = bool(d.get("final"))
        s.is_active = bool(d.get("active")) or s.code == "new"
        if d.get("stage") in ("lead", "order"):
            s.stage = d["stage"]
    audit.log(db, user, "settings", None, "update", {"поля": ["statuses"]})
    db.commit()
    return _settings_payload(request, db)


@router.post("/settings/statuses", response_model=SettingsOut)
def status_create(request: Request, body: StatusIn, db: Session = Depends(get_db), user: User = Depends(admin)):
    data = body.model_dump(exclude_unset=True)
    name = str(data.get("name") or "").strip()
    if not name:
        bad("Вкажіть назву статусу")
    db.add(Status(code="custom_" + secrets.token_hex(3), name=name[:80], color=data.get("color") or "#64748b",
                  sort=to_int(data.get("sort"), 200),
                  stock_action=data.get("stock_action") if data.get("stock_action") in STOCK_ACTIONS else "none"))
    db.commit()
    return _settings_payload(request, db)


@router.delete("/settings/statuses/{sid}", response_model=SettingsOut)
def status_delete(sid: int, request: Request, db: Session = Depends(get_db), user: User = Depends(admin)):
    s = db.get(Status, sid)
    if s is None:
        raise HTTPException(404, "Статус не знайдено")
    if s.is_system:
        bad("Системний статус не можна видалити, але його можна вимкнути")
    if db.query(Order).filter(Order.status_id == sid).count():
        bad("У цьому статусі є замовлення. Перенесіть їх або вимкніть статус.")
    db.query(SmsTemplate).filter(SmsTemplate.status_id == sid).delete()
    db.delete(s)
    db.commit()
    return _settings_payload(request, db)


@router.put("/settings/payment-methods", response_model=SettingsOut)
def payment_methods_save(request: Request, body: list[PaymentMethodIn], db: Session = Depends(get_db),
                         user: User = Depends(admin)):
    """Зберегти довідник видів оплат цілим списком (рядок без id — новий вид)."""
    by_id = {m.id: m for m in db.query(PaymentMethod).all()}
    for b in body:
        if b.checkbox_type and b.checkbox_type not in CHECKBOX_PAYMENTS:
            bad(f"Невідомий тип оплати Checkbox: {b.checkbox_type}")
        m = by_id.get(b.id) if b.id else None
        if m is None:
            m = PaymentMethod()
            db.add(m)
        m.name, m.icon, m.kind = b.name.strip()[:80], (b.icon or "cash")[:32], b.kind
        m.checkbox_type, m.is_active, m.sort = b.checkbox_type, b.active, b.sort
        m.np_cod = b.np_cod
    audit.log(db, user, "settings", None, "update", {"поля": ["види оплат"]})
    db.commit()
    return _settings_payload(request, db)


PAY_IMAGE_TYPES = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif"}  # без SVG — може містити скрипти


def _pay_dir() -> Path:
    d = Path(config.MEDIA_DIR) / "pay"
    d.mkdir(parents=True, exist_ok=True)
    return d


@router.post("/settings/payment-methods/{mid}/image", response_model=SettingsOut)
async def payment_method_image(mid: int, request: Request, file: UploadFile = File(...), db: Session = Depends(get_db),
                               user: User = Depends(admin)):
    """Свій значок виду оплати (наприклад, офіційний логотип платіжної системи): PNG, JPG, WEBP або GIF до 1 МБ."""
    m = db.get(PaymentMethod, mid)
    if m is None:
        raise HTTPException(404, "Вид оплати не знайдено")
    ext = PAY_IMAGE_TYPES.get((file.content_type or "").lower())
    if not ext:
        bad("Підтримуються PNG, JPG, WEBP і GIF")
    data = await file.read()
    if len(data) > 1024 * 1024:
        bad("Картинка більша за 1 МБ")
    old = m.image
    m.image = f"{mid}-{uuid.uuid4().hex[:10]}{ext}"
    (_pay_dir() / m.image).write_bytes(data)
    if old:
        (_pay_dir() / old).unlink(missing_ok=True)
    audit.log(db, user, "settings", None, "update", {"поля": [f"значок виду оплати «{m.name}»"]})
    db.commit()
    return _settings_payload(request, db)


@router.delete("/settings/payment-methods/{mid}/image", response_model=SettingsOut)
def payment_method_image_delete(mid: int, request: Request, db: Session = Depends(get_db), user: User = Depends(admin)):
    m = db.get(PaymentMethod, mid)
    if m is None:
        raise HTTPException(404, "Вид оплати не знайдено")
    if m.image:
        (_pay_dir() / m.image).unlink(missing_ok=True)
        m.image = ""
        db.commit()
    return _settings_payload(request, db)


DIRECTORIES = {  # шлях → (модель, поле замовлення, назва для журналу)
    "sources": (OrderSource, "source_id", "джерела замовлень"),
    "offices": (Office, "office_id", "відділи"),
    "reasons": (StatusReason, "reason_id", "причини статусів"),
    "marks": (OrderMark, "mark_id", "позначки"),
}


@router.put("/settings/dir/{kind}", response_model=SettingsOut)
def directory_save(kind: str, request: Request, body: list[SourceIn], db: Session = Depends(get_db),
                   user: User = Depends(admin)):
    """Зберегти простий довідник цілим списком: рядок без id — новий, delete — прибрати
    (якщо є замовлення з цим значенням — лише вимикаємо, щоб не зламати історію)."""
    if kind not in DIRECTORIES:
        raise HTTPException(404, "Невідомий довідник")
    model, field, title = DIRECTORIES[kind]
    by_id = {x.id: x for x in db.query(model).all()}
    for b in body:
        x = by_id.get(b.id) if b.id else None
        if b.delete:
            if x is not None:
                if db.query(Order).filter(getattr(Order, field) == x.id).first():
                    x.is_active = False
                else:
                    db.delete(x)
            continue
        if x is None:
            x = model()
            db.add(x)
        x.name, x.is_active, x.sort = b.name.strip()[:120], b.active, b.sort
        if kind == "reasons" and b.status_ids is not None:
            x.status_ids = sorted({int(i) for i in b.status_ids})
        if kind == "marks":
            x.icon = (b.icon or x.icon or "tag")[:24]
            x.color = b.color or x.color or "#475569"
        if kind == "sources":
            office = b.office_id if b.office_id and db.get(Office, b.office_id) else None
            if x.id and x.office_id != office:  # відділ = сукупність джерел: переносимо й наявні замовлення
                db.query(Order).filter(Order.source_id == x.id).update({"office_id": office}, synchronize_session=False)
            x.office_id = office
    audit.log(db, user, "settings", None, "update", {"поля": [title]})
    db.commit()
    return _settings_payload(request, db)


@router.put("/settings/np-accounts", response_model=SettingsOut)
def np_accounts_save(request: Request, body: list[NpAccountIn], db: Session = Depends(get_db), user: User = Depends(admin)):
    """Ключі Нової Пошти цілим списком. api_key «********» — не змінювати; delete — прибрати ключ."""
    by_id = {a.id: a for a in db.query(NpAccount).all()}
    for b in body:
        a = by_id.get(b.id) if b.id else None
        if b.delete:
            if a is not None:
                db.delete(a)
            continue
        if a is None:
            a = NpAccount()
            db.add(a)
        for f in NP_FIELDS:
            setattr(a, f, getattr(b, f))
        a.default_weight = Decimal(str(b.default_weight))
        if b.api_key is not None and b.api_key != "********":
            a.api_key = b.api_key.strip()
        if b.directory is not None:
            a.directory = b.directory
    db.flush()
    accs = db.query(NpAccount).order_by(NpAccount.id).all()
    defaults = [a for a in accs if a.is_default and a.is_active]
    for a in accs:  # основний ключ — рівно один
        a.is_default = bool(defaults) and a is defaults[0]
    if accs and not defaults:
        next((a for a in accs if a.is_active), accs[0]).is_default = True
    audit.log(db, user, "settings", None, "update", {"поля": ["ключі Нової Пошти"]})
    db.commit()
    return _settings_payload(request, db)


@router.post("/settings/np-accounts/{aid}/sync", response_model=SettingsOut)
def np_account_sync(aid: int, request: Request, db: Session = Depends(get_db), user: User = Depends(admin)):
    """Підтягнути з кабінету НП контрагентів і контактних осіб; якщо відправник не вибраний — перший."""
    a = db.get(NpAccount, aid)
    if a is None:
        raise HTTPException(404, "Ключ не знайдено")
    try:
        data = NovaPoshta(np_svc.account_settings(st.get_all(db), a)).load_directory()
    except CarrierError as e:
        bad(str(e), 422)
    a.directory = data
    senders = data.get("senders") or []
    if senders and not any(x["ref"] == a.sender_ref for x in senders):
        a.sender_ref, a.sender_name = senders[0]["ref"], senders[0]["name"]
    cur = next((x for x in senders if x["ref"] == a.sender_ref), None)
    if cur and cur["contacts"] and not any(c["ref"] == a.contact_ref for c in cur["contacts"]):
        c = cur["contacts"][0]
        a.contact_ref, a.contact_name, a.sender_phone = c["ref"], c["name"], c["phone"]
    if not a.name and a.sender_name:
        a.name = a.sender_name
    db.commit()
    out = _settings_payload(request, db)
    out["message"] = f"Синхронізовано: відправників {len(senders)}"
    return out


@router.put("/settings/np-rules", response_model=SettingsOut)
def np_rules_save(request: Request, body: list[NpRuleIn], db: Session = Depends(get_db), user: User = Depends(admin)):
    db.query(NpStatusRule).delete()
    statuses = {s.id for s in db.query(Status).all()}
    for i, b in enumerate(body):
        if b.np_code not in np_svc.NP_STATUSES or b.status_id not in statuses:
            bad("Невідомий статус у правилі")
        db.add(NpStatusRule(np_code=b.np_code, status_id=b.status_id, sort=i * 10,
                            except_ids=sorted({int(x) for x in b.except_ids if int(x) in statuses})))
    audit.log(db, user, "settings", None, "update", {"поля": ["правила статусів НП"]})
    db.commit()
    return _settings_payload(request, db)


@router.put("/settings/shops", response_model=SettingsOut)
def shops_save(request: Request, body: list[ShopIn], db: Session = Depends(get_db), user: User = Depends(admin)):
    """Магазини маркетплейсів цілим списком. secret «********» — не змінювати."""
    by_id = {x.id: x for x in db.query(MarketplaceShop).all()}
    for b in body:
        x = by_id.get(b.id) if b.id else None
        if b.delete:
            if x is not None:
                db.delete(x)
            continue
        if x is None:
            x = MarketplaceShop(kind=b.kind)
            db.add(x)
        for f in ("name", "login", "office_id", "source_id", "import_status_id", "extra_field", "status_map",
                  "payment_map", "delivery_map", "is_active"):
            setattr(x, f, getattr(b, f))
        if b.secret is not None and b.secret != "********":
            x.secret, x.token = b.secret.strip(), ""
        x.since = parse_date(b.since) if b.since else None
    audit.log(db, user, "settings", None, "update", {"поля": ["маркетплейси"]})
    db.commit()
    return _settings_payload(request, db)


@router.post("/settings/shops/{sid}/check", response_model=ShopCheckOut)
def shop_check(sid: int, db: Session = Depends(get_db), user: User = Depends(admin)):
    from ..services import marketplaces as mp
    x = db.get(MarketplaceShop, sid)
    if x is None:
        raise HTTPException(404, "Магазин не знайдено")
    try:
        return mp.check(db, x)
    except mp.MarketplaceError as e:
        db.commit()
        bad(str(e), 422)


@router.post("/settings/shops/{sid}/sync", response_model=ShopSyncOut)
def shop_sync(sid: int, db: Session = Depends(get_db), user: User = Depends(admin)):
    from ..services import marketplaces as mp
    x = db.get(MarketplaceShop, sid)
    if x is None:
        raise HTTPException(404, "Магазин не знайдено")
    return mp.sync_shop(db, x)


@router.put("/settings/checkbox-cashiers", response_model=SettingsOut)
def cashiers_save(request: Request, body: list[CashierIn], db: Session = Depends(get_db), user: User = Depends(admin)):
    """Каси Checkbox цілим списком (порядок = порядок перевірки умов). Ключ і пароль «********» — не змінювати."""
    by_id = {c.id: c for c in db.query(CheckboxCashier).all()}
    for i, b in enumerate(body):
        c = by_id.get(b.id) if b.id else None
        if b.delete:
            if c is not None:
                db.delete(c)
            continue
        if c is None:
            c = CheckboxCashier()
            db.add(c)
        c.name, c.login, c.test_mode, c.auto_shift = b.name.strip(), b.login.strip(), b.test_mode, b.auto_shift
        c.condition, c.is_active, c.sort = b.condition, b.is_active, i * 10
        c.legal_entity_id = b.legal_entity_id or None
        c.condition_value = b.condition_value if b.condition != "none" else None
        for f in ("license_key", "password"):
            v = getattr(b, f)
            if v is not None and v != "********":
                setattr(c, f, v.strip())
                c.token = ""
    audit.log(db, user, "settings", None, "update", {"поля": ["каси Checkbox"]})
    db.commit()
    return _settings_payload(request, db)


@router.post("/settings/checkbox-cashiers/{cid}/check", response_model=CashierCheckOut)
def cashier_check(cid: int, db: Session = Depends(get_db), user: User = Depends(admin)):
    from ..services import checkbox as cb
    c = db.get(CheckboxCashier, cid)
    if c is None:
        raise HTTPException(404, "Касу не знайдено")
    try:
        shift = cb.Api(c)._req("GET", "/cashier/shift")
        c.last_error = ""
        db.commit()
    except cb.CheckboxError as e:
        c.last_error = str(e)[:1000]
        db.commit()
        bad(str(e), 422)
    state = (shift or {}).get("status") or "CLOSED"
    names = {"OPENED": "відкрита", "CLOSED": "закрита", "OPENING": "відкривається", "CLOSING": "закривається"}
    return {"shift": state, "message": f"Касир увійшов. Зміна {names.get(state, state)}."}


@router.post("/settings/sms-templates", response_model=SettingsOut)
def sms_template_save(request: Request, body: SmsTemplateIn, db: Session = Depends(get_db),
                      user: User = Depends(admin)):
    data = body.model_dump(exclude_unset=True)
    tid = to_int(data.get("id"))
    if data.get("delete") and tid:
        t = db.get(SmsTemplate, tid)
        if t:
            db.delete(t)
        db.commit()
        return _settings_payload(request, db)
    t = db.get(SmsTemplate, tid) if tid else SmsTemplate()
    t.status_id = to_int(data.get("status_id"))
    t.channel = data.get("channel") if data.get("channel") in ("sms", "viber", "hybrid") else "sms"
    t.text = str(data.get("text") or "").strip()
    t.is_active = bool(data.get("active", True))
    if not t.text or not db.get(Status, t.status_id):
        bad("Вкажіть статус і текст шаблону")
    if not tid:
        db.add(t)
    db.commit()
    return _settings_payload(request, db)


@router.post("/settings/sms-test", response_model=Ok)
def sms_test(body: SmsTestIn, db: Session = Depends(get_db), user: User = Depends(admin)):
    data = body.model_dump(exclude_unset=True)
    s = st.get_all(db)
    if not s.get("sms_token"):
        bad("Спершу вкажіть токен TurboSMS")
    ok, info = sms_svc.send_turbosms(s["sms_token"], normalize_phone(data.get("phone")), "Тестове повідомлення CRM",
                                     data.get("channel", "sms"), s.get("sms_sender", ""), s.get("viber_sender", ""))
    if not ok:
        bad(f"Помилка: {info}", 422)
    return {"ok": True}


@router.post("/users", response_model=UserOut)
def user_create(body: UserIn, db: Session = Depends(get_db), user: User = Depends(admin)):
    data = body.model_dump(exclude_unset=True)
    username, pw = str(data.get("username") or "").strip(), str(data.get("password") or "")
    if not username or len(pw) < 8:
        bad("Вкажіть логін і пароль (щонайменше 8 символів)")
    u = User(username=username[:64], full_name=str(data.get("full_name") or "").strip()[:128],
             role=data.get("role") if data.get("role") in ROLES else "manager", password_hash=hash_password(pw),
             offices=sorted({int(i) for i in (data.get("offices") or [])}))
    db.add(u)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        bad("Такий логін уже зайнятий", 409)
    audit.log(db, user, "user", u.id, "create", {"логін": u.username, "роль": u.role})
    db.commit()
    return j_user(u)


@router.patch("/users/{uid}", response_model=UserOut)
def user_update(uid: int, body: UserIn, db: Session = Depends(get_db), user: User = Depends(admin)):
    data = body.model_dump(exclude_unset=True)
    u = db.get(User, uid)
    if u is None:
        raise HTTPException(404, "Користувача не знайдено")
    if "full_name" in data:
        u.full_name = str(data["full_name"] or "").strip()[:128]
    if data.get("role") in ROLES:
        if u.id == user.id and data["role"] != "admin":
            bad("Не можна забрати права адміністратора в самого себе")
        u.role = data["role"]
    if "is_active" in data:
        if u.id == user.id and not data["is_active"]:
            bad("Не можна вимкнути власний обліковий запис")
        u.is_active = bool(data["is_active"])
    if data.get("password"):
        if len(str(data["password"])) < 8:
            bad("Пароль має містити щонайменше 8 символів")
        u.password_hash = hash_password(str(data["password"]))
    if data.get("offices") is not None:
        u.offices = sorted({int(i) for i in data["offices"]})
    audit.log(db, user, "user", u.id, "update", {"логін": u.username, "роль": u.role, "активний": u.is_active,
                                                  "пароль змінено": bool(data.get("password"))})
    db.commit()
    return j_user(u)


# Загальне збереження розділу — в кінці файлу, щоб не перехоплювати конкретні маршрути (/settings/statuses тощо)
@router.put("/settings/legal-entities", response_model=SettingsOut)
def legal_entities_save(request: Request, body: list[LegalEntityIn], db: Session = Depends(get_db), user: User = Depends(admin)):
    """Юридичні особи цілим списком. Рівно одна — за замовчуванням (для нових замовлень)."""
    from ..models import LegalEntity
    by_id = {x.id: x for x in db.query(LegalEntity).all()}
    for i, b in enumerate(body):
        x = by_id.get(b.id) if b.id else None
        if b.delete:
            if x is not None:
                if db.query(Order).filter(Order.legal_entity_id == x.id).first():
                    x.is_active, x.is_default = False, False
                else:
                    db.delete(x)
            continue
        if not b.name.strip():
            bad("Вкажіть назву юридичної особи")
        if x is None:
            x = LegalEntity()
            db.add(x)
        x.name, x.code, x.iban = b.name.strip()[:255], b.code.strip()[:20], b.iban.strip().replace(" ", "")[:34]
        x.code_label = b.code_label if b.code_label in ("РНОКПП", "ІПН", "ЄДРПОУ") else "РНОКПП"
        x.address, x.bank, x.phone = b.address.strip()[:255], b.bank.strip()[:160], b.phone.strip()[:40]
        x.vat_note, x.signer = (b.vat_note.strip() or "Без ПДВ")[:80], b.signer.strip()[:120]
        x.is_default, x.is_active, x.sort = b.is_default and b.is_active, b.is_active, (i + 1) * 10
    db.flush()
    rows = db.query(LegalEntity).order_by(LegalEntity.sort, LegalEntity.id).all()
    defaults = [x for x in rows if x.is_default]
    for x in rows:
        x.is_default = bool(defaults) and x is defaults[0]
    if rows and not defaults:
        first = next((x for x in rows if x.is_active), None)
        if first is not None:
            first.is_default = True
    audit.log(db, user, "settings", None, "update", {"поля": ["юридичні особи"]})
    db.commit()
    return _settings_payload(request, db)


@router.put("/settings/{section}", response_model=SettingsOut)
def settings_save(section: str, request: Request, data: dict[str, str | bool | int | None], db: Session = Depends(get_db),
                  user: User = Depends(admin)):
    keys = SECTION_KEYS.get(section)
    if not keys:
        raise HTTPException(404, "Невідомий розділ")
    changed = []
    for k in keys:
        if k not in data:
            continue
        v = data[k]
        val = ("1" if v in (True, "1", 1, "on") else "0") if k in CHECKBOXES else str(v if v is not None else "").strip()
        if k in st.SECRET_KEYS and val == "********":
            continue
        if k == "doc_logo" and val and (not val.startswith("data:image/png;base64,") or len(val) > 1_500_000):
            bad("Логотип: PNG до 1 МБ")
        if k == "doc_accent" and val and not re.fullmatch(r"#[0-9a-fA-F]{6}", val):
            bad("Колір документів: формат #RRGGBB")
        if k in ("invoice_days", "warranty_months", "lead_wait_warn_min", "lead_wait_bad_min", "lead_noanswer_remind_min") and val and not val.isdigit():
            bad("Вкажіть ціле число")
        if k == "lead_to_order_status" and val not in ("confirmed", "unsorted"):
            bad("Статус замовлення з ліда: confirmed або unsorted")
        if st.get(db, k) != val:
            st.set_value(db, k, val)
            changed.append(k)
    if changed:
        audit.log(db, user, "settings", None, "update", {"поля": changed})
    db.commit()
    return _settings_payload(request, db)

