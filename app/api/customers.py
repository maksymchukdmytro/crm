"""API покупців: список з підсумками, картка з історією, групи, чорний список, заблоковані IP."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..models import COUNTRIES, BlockedIp, Customer, CustomerGroup, Order, User
from ..services import audit, customers as svc
from ..services.orders import normalize_phone
from .common import admin, bad, iso, j_order_row, sales
from .schemas import (
    BlockedIpIn, BlockedIpOut, CustomerDetailOut, CustomerGroupIn, CustomerGroupOut, CustomerIn, CustomerListOut,
)

router = APIRouter(prefix="/api", tags=["customers"])
SORTS = {"last": "last_at", "orders": "orders", "sum": "sum_delivered", "refused": "refused", "buyout": "buyout",
         "name": "name", "created": "created"}


def j_customer(c: Customer, s: dict | None = None) -> dict:
    s = s or svc.EMPTY_STATS
    return {
        "id": c.id, "phone": c.phone, "name": c.name, "email": c.email, "country": c.country,
        "group_id": c.group_id, "group": c.group.name if c.group else "", "group_color": c.group.color if c.group else "",
        "comment": c.comment, "blacklisted": c.is_blacklisted, "blacklist_reason": c.blacklist_reason,
        "created_at": iso(c.created_at),
        "orders": s["orders"], "delivered": s["delivered"], "refused": s["refused"], "cancelled": s["cancelled"],
        "sum_delivered": s["sum_delivered"], "sum_total": s["sum_total"], "buyout_rate": s["buyout_rate"],
        "first_order_at": iso(s["first_at"]), "last_order_at": iso(s["last_at"]),
    }


@router.get("/customers", response_model=CustomerListOut)
def customers(q: str = "", group: str = "", blacklist: str = "", sort: str = "last", desc: bool = True,
              min_orders: int = 0, offset: int = 0, limit: int = 100,
              db: Session = Depends(get_db), user: User = Depends(sales)):
    st = svc.stats_query(db).subquery()
    base = db.query(Customer).outerjoin(st, st.c.cid == Customer.id)
    if q:
        like = f"%{q.strip()}%"
        digits = "".join(ch for ch in q if ch.isdigit())
        conds = [Customer.name.ilike(like), Customer.email.ilike(like)]
        if len(digits) >= 3:
            conds.append(Customer.phone.contains(digits[-9:] if len(digits) > 9 else digits))
        base = base.filter(or_(*conds))
    if group == "none":
        base = base.filter(Customer.group_id.is_(None))
    elif group.isdigit():
        base = base.filter(Customer.group_id == int(group))
    if blacklist == "1":
        base = base.filter(Customer.is_blacklisted.is_(True))
    elif blacklist == "0":
        base = base.filter(Customer.is_blacklisted.is_(False))
    if min_orders:
        base = base.filter(func.coalesce(st.c.orders, 0) >= min_orders)
    total = base.count()
    done = func.coalesce(st.c.delivered, 0) + func.coalesce(st.c.refused, 0)
    keys = {
        "last_at": st.c.last_at, "orders": func.coalesce(st.c.orders, 0), "sum_delivered": func.coalesce(st.c.sum_delivered, 0),
        "refused": func.coalesce(st.c.refused, 0), "buyout": func.coalesce(st.c.delivered, 0) * 1.0 / func.nullif(done, 0),
        "name": Customer.name, "created": Customer.created_at,
    }
    col = keys[SORTS.get(sort, "last_at")]
    order = col.desc().nulls_last() if desc else col.asc().nulls_last()
    rows = (base.options(selectinload(Customer.group)).order_by(order, Customer.id.desc())
            .offset(max(0, offset)).limit(max(1, min(limit, 500))).all())
    stats = svc.stats_for(db, [c.id for c in rows])
    return {"total": total, "offset": offset, "rows": [j_customer(c, stats.get(c.id)) for c in rows]}


def _get(db: Session, cid: int) -> Customer:
    c = db.get(Customer, cid)
    if c is None:
        raise HTTPException(404, "Покупця не знайдено")
    return c


@router.get("/customers/{cid}", response_model=CustomerDetailOut)
def customer(cid: int, db: Session = Depends(get_db), user: User = Depends(sales)):
    c = _get(db, cid)
    from ..services.orders import visible_orders_query
    orders = (visible_orders_query(db, user).options(selectinload(Order.items)).filter(Order.customer_id == cid)
              .order_by(Order.id.desc()).limit(200).all())
    d = j_customer(c, svc.stats_for(db, [cid]).get(cid))
    d["history"] = [j_order_row(o) for o in orders]
    return d


def _apply(db: Session, c: Customer, data: dict, user: User):
    if "phone" in data:
        phone = normalize_phone(data["phone"])
        if len(phone) < 9:
            bad("Вкажіть коректний телефон")
        c.phone = phone
    for f, n in (("name", 255), ("email", 255), ("blacklist_reason", 255)):
        if f in data and data[f] is not None:
            setattr(c, f, str(data[f]).strip()[:n])
    if "comment" in data and data["comment"] is not None:
        c.comment = str(data["comment"]).strip()
    if "country" in data and data["country"]:
        if str(data["country"]).upper() not in COUNTRIES:
            bad("Невідома країна")
        c.country = str(data["country"]).upper()
    if "group_id" in data:
        gid = data["group_id"]
        if gid and db.get(CustomerGroup, int(gid)) is None:
            bad("Невідома група")
        c.group_id = int(gid) if gid else None
    if "blacklisted" in data and data["blacklisted"] is not None:
        if bool(data["blacklisted"]) != c.is_blacklisted:
            audit.log(db, user, "customer", c.id, "update", {"чорний список": "так" if data["blacklisted"] else "ні",
                                                             "причина": data.get("blacklist_reason") or c.blacklist_reason})
        c.is_blacklisted = bool(data["blacklisted"])
        if not c.is_blacklisted:
            c.blacklist_reason = ""


@router.post("/customers", response_model=CustomerDetailOut)
def customer_create(body: CustomerIn, db: Session = Depends(get_db), user: User = Depends(sales)):
    data = body.model_dump(exclude_unset=True)
    if not data.get("phone"):
        bad("Вкажіть телефон")
    c = Customer(group_id=svc.default_group_id(db))
    _apply(db, c, data, user)
    if db.query(Customer).filter(Customer.phone == c.phone).first():
        bad("Покупець з таким телефоном уже є", 409)
    db.add(c)
    db.flush()
    db.query(Order).filter(Order.phone == c.phone, Order.customer_id.is_(None)).update({"customer_id": c.id})
    db.commit()
    return customer(c.id, db, user)


@router.patch("/customers/{cid}", response_model=CustomerDetailOut)
def customer_update(cid: int, body: CustomerIn, db: Session = Depends(get_db), user: User = Depends(sales)):
    c = _get(db, cid)
    _apply(db, c, body.model_dump(exclude_unset=True), user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        bad("Покупець з таким телефоном уже є", 409)
    return customer(cid, db, user)


# ---------------------------------------------------------------- групи покупців
def _groups(db: Session) -> list[dict]:
    counts = dict(db.query(Customer.group_id, func.count(Customer.id)).group_by(Customer.group_id).all())
    return [{"id": g.id, "name": g.name, "color": g.color, "sort": g.sort, "customers": counts.get(g.id, 0)}
            for g in db.query(CustomerGroup).order_by(CustomerGroup.sort, CustomerGroup.id)]


@router.get("/customer-groups", response_model=list[CustomerGroupOut])
def groups(db: Session = Depends(get_db), user: User = Depends(sales)):
    return _groups(db)


@router.post("/customer-groups", response_model=list[CustomerGroupOut])
def group_save(body: CustomerGroupIn, db: Session = Depends(get_db), user: User = Depends(admin)):
    g = db.get(CustomerGroup, body.id) if body.id else CustomerGroup()
    if body.id and g is None:
        raise HTTPException(404, "Групу не знайдено")
    if not body.name.strip():
        bad("Вкажіть назву групи")
    g.name, g.color = body.name.strip()[:80], body.color or "#64748b"
    if body.sort is not None:
        g.sort = body.sort
    if not g.id:
        db.add(g)
    db.commit()
    return _groups(db)


@router.delete("/customer-groups/{gid}", response_model=list[CustomerGroupOut])
def group_delete(gid: int, db: Session = Depends(get_db), user: User = Depends(admin)):
    g = db.get(CustomerGroup, gid)
    if g is None:
        raise HTTPException(404, "Групу не знайдено")
    db.query(Customer).filter(Customer.group_id == gid).update({"group_id": None})
    db.delete(g)
    db.commit()
    return _groups(db)


# ---------------------------------------------------------------- заблоковані IP
def _ips(db: Session) -> list[dict]:
    return [{"id": x.id, "ip": x.ip, "comment": x.comment, "created_at": iso(x.created_at)}
            for x in db.query(BlockedIp).order_by(BlockedIp.id.desc())]


@router.get("/blocked-ips", response_model=list[BlockedIpOut])
def blocked_ips(db: Session = Depends(get_db), user: User = Depends(admin)):
    return _ips(db)


@router.post("/blocked-ips", response_model=list[BlockedIpOut])
def blocked_ip_add(body: BlockedIpIn, db: Session = Depends(get_db), user: User = Depends(admin)):
    import ipaddress
    try:
        ip = str(ipaddress.ip_address(body.ip.strip()))
    except ValueError:
        bad("Некоректна IP-адреса")
    if not db.query(BlockedIp).filter(BlockedIp.ip == ip).first():
        db.add(BlockedIp(ip=ip, comment=(body.comment or "").strip()[:255]))
        audit.log(db, user, "settings", None, "update", {"заблоковано IP": ip})
        db.commit()
    return _ips(db)


@router.delete("/blocked-ips/{bid}", response_model=list[BlockedIpOut])
def blocked_ip_delete(bid: int, db: Session = Depends(get_db), user: User = Depends(admin)):
    x = db.get(BlockedIp, bid)
    if x is not None:
        db.delete(x)
        db.commit()
    return _ips(db)
