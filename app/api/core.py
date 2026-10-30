"""API: вхід, профіль, довідники для інтерфейсу, події в реальному часі (SSE)."""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session, selectinload

from ..carriers import CARRIERS
from ..config import config
from ..db import get_db
from ..models import (
    DELIVERY_METHODS,
    DELIVERY_STATES,
    PAYMENT_KINDS,
    PAYMENT_STATUSES,
    PAYMENT_TYPES,
    CHECKBOX_PAYMENTS,
    COUNTRIES,
    ROLES,
    STOCK_ACTIONS,
    MarketplaceShop,
    Office,
    OrderMark,
    OrderSource,
    PaymentMethod,
    StatusReason,
    Product,
    Status,
    User,
    utcnow,
)
from ..security import hash_password, throttle, verify_password
from ..services import audit, prefs
from ..services import np as np_svc
from ..services import settings as st
from ..services.events import CHANNEL
from .schemas import LoginIn, LoginOut, MeIn, MetaOut, NameSplitOut, Ok, UserOut
from .shell import counters as shell_counters
from .common import api_user, bad, j_payment_method, j_product, j_source, j_status, j_user

router = APIRouter(prefix="/api", tags=["core"])

NAV = [  # розділ, ролі
    ("home", ("admin", "manager")),
    ("leads", ("admin", "manager")),
    ("orders", ("admin", "manager", "warehouse")),
    ("board", ("admin", "manager", "warehouse")),
    ("customers", ("admin", "manager")),
    ("products", ("admin", "manager", "warehouse")),
    ("warehouse", ("admin", "warehouse")),
    ("purchases", ("admin", "warehouse")),
    ("payments", ("admin",)),
    ("stats", ("admin", "manager")),
    ("reports", ("admin", "manager")),
    ("audit", ("admin",)),
    ("settings", ("admin",)),
    ("system", ("admin",)),
]


@router.post("/auth/login", response_model=LoginOut)
def login(request: Request, body: LoginIn, db: Session = Depends(get_db)):
    data = body.model_dump(exclude_unset=True)
    if request.headers.get("x-crm") != "1":
        return JSONResponse({"error": "Відсутній заголовок X-CRM"}, 403)
    username = str(data.get("username", "")).strip()
    ip = request.client.host if request.client else "?"
    key = f"{ip}:{username.lower()}"
    if throttle.blocked(key):
        return JSONResponse({"error": "Забагато спроб. Спробуйте через 10 хвилин."}, 429)
    user = db.query(User).filter(User.username == username).one_or_none()
    if user is None or not user.is_active or not verify_password(str(data.get("password", "")), user.password_hash):
        throttle.fail(key)
        return JSONResponse({"error": "Невірний логін або пароль"}, 401)
    throttle.reset(key)
    request.session.clear()
    request.session["uid"] = user.id
    user.last_login_at = utcnow()
    audit.log(db, user, "user", user.id, "login", {"ip": ip})
    db.commit()
    return {"user": j_user(user)}


@router.post("/auth/logout", response_model=Ok)
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(api_user)):
    return j_user(user)


@router.patch("/me", response_model=UserOut)
def me_update(body: MeIn, db: Session = Depends(get_db), user: User = Depends(api_user)):
    data = body.model_dump(exclude_unset=True)
    if data.get("full_name"):
        user.full_name = str(data["full_name"]).strip()[:128]
    if data.get("new_password"):
        if not verify_password(str(data.get("old_password", "")), user.password_hash):
            bad("Поточний пароль невірний")
        if len(str(data["new_password"])) < 8:
            bad("Новий пароль має містити щонайменше 8 символів")
        user.password_hash = hash_password(str(data["new_password"]))
    db.commit()
    return j_user(user)


def _active(db: Session, model):
    return db.query(model).filter(model.is_active.is_(True)).order_by(model.sort, model.id).all()


@router.get("/meta", response_model=MetaOut)
def meta(db: Session = Depends(get_db), user: User = Depends(api_user)):
    s = st.get_all(db)
    statuses = db.query(Status).order_by(Status.sort, Status.id).all()
    managers = (db.query(User).filter(User.is_active.is_(True), User.role.in_(["admin", "manager"]))
                .order_by(User.full_name, User.username).all())
    products = (db.query(Product).options(selectinload(Product.variants), selectinload(Product.photos))
                .filter(Product.is_active.is_(True)).order_by(Product.is_upsell, Product.name).all())
    from ..models import Category, CheckboxCashier, CustomerGroup, LegalEntity, Manufacturer
    from ..models import LegalEntityAccount
    accounts: dict[int, list] = {}
    for a in db.query(LegalEntityAccount).filter(LegalEntityAccount.is_active.is_(True)).order_by(LegalEntityAccount.sort, LegalEntityAccount.id):
        accounts.setdefault(a.legal_entity_id, []).append({"id": a.id, "name": a.name, "kind": a.kind})
    with_cashier = {c for (c,) in db.query(CheckboxCashier.legal_entity_id).filter(
        CheckboxCashier.is_active.is_(True), CheckboxCashier.legal_entity_id.isnot(None))}
    return {
        "user": j_user(user),
        "company": s.get("company_name") or "CRM",
        "nav": [k for k, roles in NAV if user.role in roles],
        "statuses": [j_status(x) for x in statuses],
        "managers": [j_user(m) for m in managers],
        "products": [j_product(p) for p in products],
        "delivery_methods": DELIVERY_METHODS,
        "delivery_states": DELIVERY_STATES,
        "payment_types": PAYMENT_TYPES,
        "payment_methods": [j_payment_method(m) for m in db.query(PaymentMethod).filter(PaymentMethod.is_active.is_(True))
                            .order_by(PaymentMethod.sort, PaymentMethod.id)],
        "order_sources": [j_source(x) for x in db.query(OrderSource).filter(OrderSource.is_active.is_(True))
                          .order_by(OrderSource.sort, OrderSource.id)],
        "offices": [j_source(x) for x in _active(db, Office)],
        "reasons": [j_source(x) for x in _active(db, StatusReason)],
        "marks": [j_source(x) for x in _active(db, OrderMark)],
        "countries": COUNTRIES,
        "extra_fields": [s.get(f"extra{i}_name") or f"Поле {i}" for i in range(1, 5)],
        "extra_on": [s.get(f"extra{i}_on", "1") != "0" for i in range(1, 5)],
        "checkbox_payments": CHECKBOX_PAYMENTS,
        "payment_kinds": PAYMENT_KINDS,
        "payment_statuses": PAYMENT_STATUSES,
        "stock_actions": STOCK_ACTIONS,
        "roles": ROLES,
        "carriers": {code: {"name": cls.name, "beta": cls.beta,
                            "configured": cls(np_svc.carrier_settings(db) if code == "novaposhta" else s).configured()}
                     for code, cls in CARRIERS.items()},
        "shops": {str(x.id): f"{'Rozetka' if x.kind == 'rozetka' else 'Prom'} · {x.name}".rstrip(" ·")
                  for x in db.query(MarketplaceShop).all()},
        "np_accounts": [{"id": a.id, "name": a.name or f"Ключ {a.id}", "office_id": a.office_id, "is_default": a.is_default}
                        for a in np_svc.accounts(db)],
        "sms_ready": bool(s.get("sms_token")),
        "managers_see_own_only": s.get("managers_see_own_only") == "1",
        "realtime": bool(config.REDIS_URL),
        "root": config.ROOT_PATH,
        "categories": [{"id": c.id, "name": c.name, "parent_id": c.parent_id}
                       for c in db.query(Category).filter(Category.is_active.is_(True)).order_by(Category.sort, Category.name)],
        "manufacturers": [{"id": m.id, "name": m.name}
                          for m in db.query(Manufacturer).filter(Manufacturer.is_active.is_(True)).order_by(Manufacturer.name)],
        "customer_groups": [{"id": g.id, "name": g.name, "color": g.color}
                            for g in db.query(CustomerGroup).order_by(CustomerGroup.sort, CustomerGroup.id)],
        "legal_entities": [{"id": x.id, "name": x.name, "is_default": x.is_default, "has_cashier": x.id in with_cashier,
                            "accounts": accounts.get(x.id, [])}
                           for x in db.query(LegalEntity).filter(LegalEntity.is_active.is_(True)).order_by(LegalEntity.sort, LegalEntity.id)],
        "checkbox_ready": bool(with_cashier) or db.query(CheckboxCashier).filter(CheckboxCashier.is_active.is_(True)).count() > 0,
        "office": prefs.current_office(db, user),
        "leads_enabled": s.get("leads_enabled", "1") != "0",
        "lead_wait_warn_min": int(s.get("lead_wait_warn_min") or 5),
        "lead_wait_bad_min": int(s.get("lead_wait_bad_min") or 15),
        "counters": shell_counters(db, user),
        "prefs": prefs.all_for(db, user),
    }


@router.get("/events")
async def events_stream(request: Request, user: User = Depends(api_user)):
    """Server-Sent Events: зміни замовлень і товарів. Без Redis — 204 (інтерфейс перейде на опитування)."""
    if not config.REDIS_URL:
        return JSONResponse(None, 204)
    import redis.asyncio as aioredis

    async def gen():
        r = aioredis.from_url(config.REDIS_URL)
        ps = r.pubsub()
        await ps.subscribe(CHANNEL)
        yield "retry: 3000\n\n"
        idle = 0.0
        try:
            while True:
                if await request.is_disconnected():
                    break
                msg = await ps.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if msg and msg.get("type") == "message":
                    data = msg["data"].decode() if isinstance(msg["data"], bytes) else msg["data"]
                    try:
                        ev = json.loads(data)
                    except ValueError:
                        continue
                    # особисті повідомлення (помилки фонових задач) — лише своєму користувачу
                    if ev.get("user_id") and ev["user_id"] != user.id:
                        continue
                    yield f"data: {data}\n\n"
                    idle = 0
                else:
                    idle += 1
                    if idle >= 15:  # серцебиття, щоб проксі не закривав з'єднання
                        yield ": ping\n\n"
                        idle = 0
                await asyncio.sleep(0)
        finally:
            try:
                await ps.unsubscribe(CHANNEL)
                await ps.aclose()
                await r.aclose()
            except Exception:  # noqa: BLE001
                pass

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/names/split", response_model=NameSplitOut)
def names_split(q: str = "", user: User = Depends(api_user)):
    """Розбір ПІБ одним рядком — для підказки в картці замовлення (що буде прізвищем, ім'ям, по батькові)."""
    from ..services.names import join_name, split_full_name
    last, first, middle = split_full_name(q[:255])
    return {"last_name": last, "first_name": first, "middle_name": middle, "full": join_name(last, first, middle)}
