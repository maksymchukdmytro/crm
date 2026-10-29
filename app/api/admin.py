"""API: оплати й звірка, звіти, журнал дій, налаштування, користувачі."""
from __future__ import annotations

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
from ..models import ROLES, STOCK_ACTIONS, AuditLog, Order, Payment, SmsMessage, SmsTemplate, Status, User
from ..routers.payments import parse_registry
from ..routers.settings import CHECKBOXES, SECTION_KEYS
from ..security import hash_password
from ..services import audit
from ..services import payments as pay_svc
from ..services import reports as rep
from ..services import settings as st
from ..services import sms as sms_svc
from ..services.audit import ACTION_NAMES
from ..services.orders import normalize_phone, to_int
from ..services.reports import period_bounds
from ..web import f_details, parse_date, today_local
from .schemas import SystemOut, AuditOut, DoneOut, Ok, PaymentsOut, ReceiveIn, RegistryOut, ReportOut, SettingsOut, SmsTemplateIn, SmsTestIn, StatusIn, UserIn, UserOut
from .common import admin, bad, iso, j_payment, j_status, j_user, sales

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


# ---------------------------------------------------------------- налаштування
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
    }


@router.get("/settings", response_model=SettingsOut)
def settings_get(request: Request, db: Session = Depends(get_db), user: User = Depends(admin)):
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
        if st.get(db, k) != val:
            st.set_value(db, k, val)
            changed.append(k)
    if changed:
        audit.log(db, user, "settings", None, "update", {"поля": changed})
    db.commit()
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
             role=data.get("role") if data.get("role") in ROLES else "manager", password_hash=hash_password(pw))
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
    audit.log(db, user, "user", u.id, "update", {"логін": u.username, "роль": u.role, "активний": u.is_active,
                                                  "пароль змінено": bool(data.get("password"))})
    db.commit()
    return j_user(u)
