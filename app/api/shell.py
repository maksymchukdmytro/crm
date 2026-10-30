"""API каркаса нового інтерфейсу: налаштування користувача, поточний відділ, збережені фільтри, лічильники меню, сповіщення."""
from __future__ import annotations

from datetime import timedelta
from urllib.parse import parse_qsl, urlencode

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from ..db import get_db
from ..models import Order, OrderComment, SavedFilter, Status, User, utcnow
from ..routers.orders import _apply
from ..services import orders as svc
from ..services import prefs
from ..services import settings as st
from .common import api_user, bad, iso, staff
from .schemas import (
    CountersOut, NotificationsOut, Ok, OfficeIn, PrefIn, SavedFilterIn, SavedFilterOut,
)

router = APIRouter(prefix="/api", tags=["shell"])

SECTIONS = ("orders", "leads", "products", "customers", "invoices")
LIST_FILTERS = ("status", "q", "manager", "date_from", "date_to", "delivery", "source", "dup", "pay", "stage")


# ------------------------------------------------------------------ налаштування користувача
@router.get("/me/prefs", response_model=dict)
def get_prefs(db: Session = Depends(get_db), user: User = Depends(api_user)):
    return prefs.all_for(db, user)


@router.put("/me/prefs/{key}", response_model=Ok)
def put_pref(key: str, body: PrefIn, db: Session = Depends(get_db), user: User = Depends(api_user)):
    try:
        prefs.put(db, user, key, body.value)
    except ValueError as e:
        bad(str(e))
    db.commit()
    return {"ok": True}


@router.put("/me/office", response_model=Ok)
def set_office(body: OfficeIn, db: Session = Depends(get_db), user: User = Depends(api_user)):
    """Перемикач відділу в боковій панелі. null — усі доступні відділи."""
    oid = body.office_id
    if oid is not None:
        allowed = [int(x) for x in (user.offices or [])]
        if user.role != "admin" and allowed and oid not in allowed:
            bad("Цей відділ вам недоступний", 403)
    prefs.put(db, user, "office", oid)
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------------ лічильники меню
def _count_query(db: Session, user: User, query: str) -> int:
    f = {k: "" for k in LIST_FILTERS}
    for k, v in parse_qsl(query.lstrip("?"), keep_blank_values=False):
        if k in f:
            f[k] = v.strip()
    return _apply(svc.visible_orders_query(db, user), f).count()


def counters(db: Session, user: User) -> dict:
    vis = svc.visible_orders_query(db, user)
    codes = {s.code: s.id for s in db.query(Status).all()}
    leads_on = st.get_all(db).get("leads_enabled", "1") != "0"
    leads_new = vis.filter(Order.status_id == codes["new"]).count() if leads_on and "new" in codes else 0
    unsorted = vis.filter(Order.status_id == codes["unsorted"]).count() if "unsorted" in codes else 0
    due = vis.filter(Order.remind_at.isnot(None), Order.remind_at <= utcnow()).count()
    saved = {}
    for sf in _saved(db, user):
        if sf.section in ("orders", "leads"):
            try:
                saved[str(sf.id)] = _count_query(db, user, sf.query)
            except Exception:  # noqa: BLE001 — зламаний фільтр не має ламати меню
                saved[str(sf.id)] = 0
    return {"leads_new": leads_new, "orders_unsorted": unsorted, "reminders_due": due, "saved": saved}


@router.get("/counters", response_model=CountersOut)
def get_counters(db: Session = Depends(get_db), user: User = Depends(staff)):
    return counters(db, user)


# ------------------------------------------------------------------ збережені фільтри
def _saved(db: Session, user: User):
    return (db.query(SavedFilter).filter((SavedFilter.user_id == user.id) | SavedFilter.is_shared.is_(True))
            .order_by(SavedFilter.sort, SavedFilter.id).all())


def _j(sf: SavedFilter, user: User) -> dict:
    return {"id": sf.id, "section": sf.section, "name": sf.name, "color": sf.color, "query": sf.query, "sort": sf.sort,
            "is_shared": sf.is_shared, "mine": sf.user_id == user.id}


def _own(db: Session, user: User, fid: int) -> SavedFilter:
    sf = db.get(SavedFilter, fid)
    if sf is None or (sf.user_id != user.id and user.role != "admin"):
        bad("Фільтр не знайдено", 404)
    return sf


def _clean(sf: SavedFilter, data: dict, user: User):
    if "name" in data:
        name = str(data["name"] or "").strip()[:80]
        if not name:
            bad("Вкажіть назву фільтра")
        sf.name = name
    if "section" in data:
        if data["section"] not in SECTIONS:
            bad("Невідомий розділ")
        sf.section = data["section"]
    if "color" in data:
        c = str(data["color"] or "")
        if not (len(c) in (4, 7, 9) and c.startswith("#")):
            bad("Колір має бути у форматі #RRGGBB")
        sf.color = c
    if "query" in data:
        q = str(data["query"] or "").lstrip("?")[:2000]
        sf.query = urlencode([(k, v) for k, v in parse_qsl(q) if k in LIST_FILTERS or k in ("tab", "view", "sort")])
    if "sort" in data and data["sort"] is not None:
        sf.sort = int(data["sort"])
    if "is_shared" in data and data["is_shared"] is not None:
        if data["is_shared"] and user.role != "admin":
            bad("Спільні фільтри створює адміністратор", 403)
        sf.is_shared = bool(data["is_shared"])


@router.get("/saved-filters", response_model=list[SavedFilterOut])
def list_saved(section: str = "", db: Session = Depends(get_db), user: User = Depends(staff)):
    return [_j(x, user) for x in _saved(db, user) if not section or x.section == section]


@router.post("/saved-filters", response_model=SavedFilterOut)
def create_saved(body: SavedFilterIn, db: Session = Depends(get_db), user: User = Depends(staff)):
    data = body.model_dump(exclude_unset=True)
    if db.query(SavedFilter).filter(SavedFilter.user_id == user.id).count() >= 30:
        bad("Не більше 30 збережених фільтрів")
    sf = SavedFilter(user_id=user.id, section="orders", name="", color="#2E6BE6", query="")
    data.setdefault("name", "")
    _clean(sf, data, user)
    db.add(sf)
    db.commit()
    return _j(sf, user)


@router.patch("/saved-filters/{fid}", response_model=SavedFilterOut)
def update_saved(fid: int, body: SavedFilterIn, db: Session = Depends(get_db), user: User = Depends(staff)):
    sf = _own(db, user, fid)
    _clean(sf, body.model_dump(exclude_unset=True), user)
    db.commit()
    return _j(sf, user)


@router.delete("/saved-filters/{fid}", response_model=Ok)
def delete_saved(fid: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    db.delete(_own(db, user, fid))
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------------ сповіщення (дзвіночок) і коментарі колег
@router.get("/notifications", response_model=NotificationsOut)
def notifications(db: Session = Depends(get_db), user: User = Depends(staff)):
    vis = svc.visible_orders_query(db, user)
    due = (vis.filter(Order.remind_at.isnot(None), Order.remind_at <= utcnow() + timedelta(hours=1))
           .order_by(Order.remind_at).limit(30).all())
    ids = vis.with_entities(Order.id).subquery()
    comments = (db.query(OrderComment).options(joinedload(OrderComment.user), joinedload(OrderComment.order))
                .filter(OrderComment.order_id.in_(ids.select()), OrderComment.created_at >= utcnow() - timedelta(days=7),
                        (OrderComment.user_id != user.id) | OrderComment.user_id.is_(None))
                .order_by(OrderComment.id.desc()).limit(30).all())
    now = utcnow()
    return {
        "reminders": [{"order_id": o.id, "customer": o.customer_name or o.phone, "at": iso(o.remind_at), "due": o.remind_at <= now}
                      for o in due],
        "comments": [{"id": c.id, "order_id": c.order_id, "customer": c.order.customer_name if c.order else "",
                      "user": c.user.display if c.user else "Система", "text": c.text[:300], "at": iso(c.created_at)}
                     for c in comments],
    }
