"""Спільне для JSON API: доступ, захист від CSRF, перетворення об'єктів у JSON."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import Depends, HTTPException, Request

from ..deps import Forbidden, current_user
from ..models import (
    Order,
    OrderItem,
    Payment,
    Product,
    Purchase,
    Status,
    User,
)

API_HEADER = "x-crm"


def api_user(request: Request, user: User = Depends(current_user)) -> User:
    """Користувач API. Зміни (не GET) — лише із заголовком X-CRM: 1.

    Браузер не дозволить чужому сайту надіслати власний заголовок без дозволу CORS,
    тож це захищає від CSRF разом із cookie SameSite.
    """
    if request.method not in ("GET", "HEAD", "OPTIONS") and request.headers.get(API_HEADER) != "1":
        raise HTTPException(403, "Відсутній заголовок X-CRM")
    return user


def role(*roles: str):
    def dep(user: User = Depends(api_user)) -> User:
        if user.role not in roles:
            raise Forbidden()
        return user

    return dep


admin = role("admin")
sales = role("admin", "manager")
stock_team = role("admin", "warehouse")
staff = role("admin", "manager", "warehouse")


def bad(msg: str, code: int = 400):
    raise HTTPException(code, msg)


def iso(v: datetime | None) -> str | None:
    """UTC-час у форматі ISO з позначкою Z — браузер сам покаже у своєму часовому поясі."""
    return v.isoformat() + "Z" if v else None


def money(v) -> float:
    return float(v or 0)


def j_user(u: User | None) -> dict | None:
    if u is None:
        return None
    return {"id": u.id, "username": u.username, "name": u.display, "full_name": u.full_name, "role": u.role,
            "role_name": u.role_name, "is_active": u.is_active, "last_login_at": iso(u.last_login_at),
            "offices": [int(x) for x in (u.offices or [])]}


def j_status(s: Status) -> dict:
    return {"id": s.id, "code": s.code, "name": s.name, "color": s.color, "sort": s.sort,
            "stock_action": s.stock_action, "approved": s.counts_as_approved, "final": s.is_final,
            "system": s.is_system, "active": s.is_active, "stage": s.stage or "order"}


def j_variant(v) -> dict:
    return {"id": v.id, "name": v.name, "sku": v.sku or "", "attribute_ids": [int(x) for x in (v.attribute_ids or [])],
            "price": money(v.price) if v.price is not None else None, "stock": v.stock, "reserved": v.reserved,
            "available": v.available, "active": v.is_active}


def photo_url(file: str) -> str:
    return f"/media/products/{file}"


def j_product(p: Product) -> dict:
    return {"id": p.id, "sku": p.sku or "", "name": p.name, "price": money(p.price), "cost": money(p.cost),
            "weight": float(p.weight or 0), "stock": p.stock, "reserved": p.reserved, "available": p.available,
            "min_stock": p.min_stock, "length": float(p.length or 0), "width": float(p.width or 0),
            "height": float(p.height or 0), "ship_description": p.ship_description or "", "upsell": p.is_upsell,
            "upsell_for": [int(x) for x in (p.upsell_for or [])] if p.is_upsell else [], "active": p.is_active,
            "category_id": p.category_id, "manufacturer_id": p.manufacturer_id, "model": p.model or "",
            "countries": list(p.countries or []), "spec_price": money(p.spec_price), "sale_price": money(p.sale_price),
            "discount_percent": p.discount_percent, "wholesale_price": money(p.wholesale_price),
            "photo": photo_url(p.photos[0].file) if p.photos else None,
            "variants": [j_variant(v) for v in p.variants]}


def j_payment_method(m) -> dict:
    return {"id": m.id, "name": m.name, "icon": m.icon, "kind": m.kind, "checkbox_type": m.checkbox_type or "",
            "active": m.is_active, "sort": m.sort}


def j_source(x) -> dict:
    d = {"id": x.id, "name": x.name, "active": x.is_active, "sort": x.sort}
    if hasattr(x, "status_ids"):
        d["status_ids"] = [int(i) for i in (x.status_ids or [])]
    return d


def j_item(i: OrderItem) -> dict:
    return {"id": i.id, "product_id": i.product_id, "name": i.name, "price": money(i.price), "qty": i.qty,
            "upsell": i.is_upsell, "upsell_for": i.upsell_for_id, "upsell_for_name": i.upsell_for.name if i.upsell_for else "",
            "base_price": money(i.variant.price if i.variant is not None and i.variant.price is not None else i.product.sale_price) if i.product else None,
            "sku": (i.variant.sku if i.variant is not None and i.variant.sku else (i.product.sku if i.product and i.product.sku else "")),
            "available": (i.variant.available if i.variant is not None else i.product.available) if i.product else None,
            "variant_id": i.variant_id, "variant_name": i.variant.name if i.variant is not None else "",
            "photo": photo_url(i.product.photos[0].file) if i.product and i.product.photos else None}


def j_payment(p: Payment) -> dict:
    return {"id": p.id, "order_id": p.order_id, "kind": p.kind, "kind_name": p.kind_name, "amount": money(p.amount),
            "status": p.status, "status_name": p.status_name, "method": p.method, "reference": p.reference,
            "received_amount": money(p.received_amount) if p.received_amount is not None else None,
            "created_at": iso(p.created_at), "collected_at": iso(p.collected_at), "received_at": iso(p.received_at)}


ORDER_SCALARS = [
    "customer_name", "last_name", "first_name", "middle_name", "phone", "email", "comment", "delivery_method", "city_name", "city_ref", "warehouse_name",
    "warehouse_ref", "address", "postcode", "ttn", "carrier_ref", "delivery_state", "delivery_status",
    "payment_type", "extra1", "extra2", "extra3", "extra4", "site", "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "ip",
]


def j_order_row(o: Order) -> dict:
    """Легкий рядок для списку й канбану."""
    return {
        "id": o.id, "status_id": o.status_id, "manager_id": o.manager_id,
        "customer_name": o.customer_name, "phone": o.phone,
        "items": [{"name": i.name, "qty": i.qty, "upsell": i.is_upsell} for i in o.items],
        "total": money(o.total), "cod_amount": money(o.cod_amount), "payment_type": o.payment_type,
        "payment_method_id": o.payment_method_id, "source_id": o.source_id,
        "office_id": o.office_id, "np_account_id": o.np_account_id, "legal_entity_id": o.legal_entity_id, "reason_id": o.reason_id,
        "shop_id": o.shop_id, "external_id": o.external_id or "", "external_status": o.external_status or "", "mark_id": o.mark_id, "remind_at": iso(o.remind_at),
        "country": o.country or "UA",
        "delivery_method": o.delivery_method, "city_name": o.city_name, "ttn": o.ttn,
        "delivery_state": o.delivery_state or "", "delivery_status": o.delivery_status or "",
        "utm_source": o.utm_source, "utm_campaign": o.utm_campaign, "site": o.site,
        "duplicate_of_id": o.duplicate_of_id, "created_at": iso(o.created_at),
        "status_changed_at": iso(o.status_changed_at),
        "customer_id": o.customer_id, "blacklisted": bool(o.customer and o.customer.is_blacklisted),
    }


def j_order(o: Order) -> dict:
    d = {k: getattr(o, k) or "" for k in ORDER_SCALARS}
    d.update({
        "id": o.id, "status_id": o.status_id, "manager_id": o.manager_id,
        "manager": j_user(o.manager), "payment_method_id": o.payment_method_id, "source_id": o.source_id,
        "office_id": o.office_id, "np_account_id": o.np_account_id, "legal_entity_id": o.legal_entity_id, "reason_id": o.reason_id,
        "shop_id": o.shop_id, "external_id": o.external_id or "", "external_status": o.external_status or "", "mark_id": o.mark_id, "remind_at": iso(o.remind_at),
        "country": o.country or "UA",
        "delivery_cost": money(o.delivery_cost), "prepayment": money(o.prepayment), "discount": money(o.discount),
        "total": money(o.total), "cod_amount": money(o.cod_amount),
        "duplicate_of_id": o.duplicate_of_id, "stock_reserved": o.stock_reserved, "stock_shipped": o.stock_shipped,
        "created_at": iso(o.created_at), "updated_at": iso(o.updated_at), "shipped_at": iso(o.shipped_at),
        "delivered_at": iso(o.delivered_at), "delivery_checked_at": iso(o.delivery_checked_at),
        "version": o.updated_at.isoformat() if o.updated_at else "",
        "items": [j_item(i) for i in o.items],
        "payments": [j_payment(p) for p in o.payments],
        "comments": [{"id": c.id, "text": c.text, "user": c.user.display if c.user else "Система",
                      "created_at": iso(c.created_at)} for c in reversed(o.comments)],
    })
    return d


def j_purchase(p: Purchase, full: bool = False) -> dict:
    d = {"id": p.id, "supplier_id": p.supplier_id, "supplier": p.supplier.name if p.supplier else "",
         "status": p.status, "comment": p.comment, "total": money(p.total), "created_at": iso(p.created_at),
         "received_at": iso(p.received_at),
         "items": [{"id": i.id, "product_id": i.product_id, "name": i.product.name, "qty": i.qty,
                    "cost": money(i.cost)} for i in p.items]}
    return d


def to_dec(v) -> Decimal:
    from ..services.orders import to_money

    return to_money(v)
