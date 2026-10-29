"""API: прийом заявок з лендингів (webhook) і внутрішні довідники для інтерфейсу."""
import hmac
import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from ..carriers import CarrierError
from ..carriers.novaposhta import NovaPoshta
from ..db import get_db
from ..deps import staff
from ..models import User
from ..services import orders as svc
from ..services import settings as st

router = APIRouter()

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, X-Api-Key",
}

ALIASES = {
    "customer_name": ("name", "customer_name", "fio", "full_name", "pib"),
    "last_name": ("last_name", "surname", "lastname"),
    "first_name": ("first_name", "firstname"),
    "middle_name": ("middle_name", "patronymic", "middlename"),
    "phone": ("phone", "tel", "telephone", "phone_number"),
    "email": ("email",),
    "comment": ("comment", "comments", "message", "note"),
    "site": ("site", "landing", "domain"),
    "city_name": ("city",),
    "warehouse_name": ("warehouse", "branch"),
    "utm_source": ("utm_source",),
    "utm_medium": ("utm_medium",),
    "utm_campaign": ("utm_campaign",),
    "utm_content": ("utm_content",),
    "utm_term": ("utm_term",),
}


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else ""


def _parse_items(payload: dict) -> list[dict]:
    """Товари можна передати списком products або полями product_id / sku / product."""
    raw = payload.get("products") or payload.get("items")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            raw = None
    items = []
    if isinstance(raw, list):
        for p in raw:
            if isinstance(p, dict):
                items.append({"product_id": p.get("product_id") or p.get("id"), "sku": p.get("sku"),
                              "name": p.get("name"), "qty": p.get("qty") or p.get("count") or 1,
                              "price": p.get("price"), "is_upsell": p.get("upsell") or p.get("is_upsell")})
    else:
        pid = payload.get("product_id")
        sku = payload.get("sku") or payload.get("product_sku")
        name = payload.get("product") or payload.get("product_name")
        if pid or sku or name:
            items.append({"product_id": pid, "sku": sku, "name": name,
                          "qty": payload.get("qty") or payload.get("count") or 1, "price": payload.get("price")})
    return items


@router.options("/api/v1/orders")
def webhook_options():
    return Response(status_code=204, headers=CORS)


@router.post("/api/v1/orders")
async def webhook(request: Request, db: Session = Depends(get_db)):
    ctype = request.headers.get("content-type", "")
    if "application/json" in ctype:
        try:
            payload = await request.json()
        except ValueError:
            return JSONResponse({"ok": False, "error": "Некоректний JSON"}, 400, headers=CORS)
        if not isinstance(payload, dict):
            return JSONResponse({"ok": False, "error": "Очікується JSON-об'єкт"}, 400, headers=CORS)
    else:
        form = await request.form()
        payload = {k: v for k, v in form.items()}
    key = request.query_params.get("key") or request.headers.get("x-api-key") or str(payload.get("key", ""))
    if not hmac.compare_digest(key.encode(), st.ensure_webhook_key(db).encode()):
        return JSONResponse({"ok": False, "error": "Невірний ключ"}, 403, headers=CORS)

    data = {}
    for field, names in ALIASES.items():
        for n in names:
            if payload.get(n):
                data[field] = str(payload[n])
                break
    if payload.get("delivery") in ("novaposhta", "ukrposhta", "meest", "pickup", "courier"):
        data["delivery_method"] = payload["delivery"]
    data["ip"] = _client_ip(request)
    phone = svc.normalize_phone(data.get("phone"))
    if len(phone) < 9:
        return JSONResponse({"ok": False, "error": "Не вказано коректний телефон"}, 422, headers=CORS)

    order = svc.create_order(db, data, _parse_items(payload), user=None, source="webhook")
    db.commit()

    redirect_to = payload.get("redirect") or request.query_params.get("redirect")
    if redirect_to and str(redirect_to).startswith(("http://", "https://")) and "application/json" not in ctype:
        return RedirectResponse(str(redirect_to), status_code=303)
    return JSONResponse({"ok": True, "order_id": order.id, "duplicate": bool(order.duplicate_of_id)}, headers=CORS)


# ---------- внутрішні довідники (лише для авторизованих) -------------------
def _np(db: Session) -> NovaPoshta:
    return NovaPoshta(st.get_all(db))


@router.get("/api/np/cities")
def np_cities(q: str = "", db: Session = Depends(get_db), user: User = Depends(staff)):
    try:
        return {"ok": True, "items": _np(db).search_cities(q) if len(q) >= 2 else []}
    except CarrierError as e:
        return {"ok": False, "error": str(e)}


@router.get("/api/np/warehouses")
def np_warehouses(city_ref: str, q: str = "", db: Session = Depends(get_db), user: User = Depends(staff)):
    try:
        return {"ok": True, "items": _np(db).search_warehouses(city_ref, q)}
    except CarrierError as e:
        return {"ok": False, "error": str(e)}
