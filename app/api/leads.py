"""API лідів: черга дзвінків, результат дзвінка, створення замовлення з ліда, перемикач розділу «Ліди»."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..services import audit, leads
from ..services import orders as svc
from ..services import settings as st
from .common import admin, bad, sales
from .orders import _full, _get
from .schemas import LeadQueueOut, LeadResultIn, LeadStepOut, LeadsPreviewOut, LeadsToggleIn, LeadsToggleOut

router = APIRouter(prefix="/api", tags=["leads"])


def _next(db: Session, user: User, current: int) -> int | None:
    return next((i for i in leads.queue(db, user) if i != current), None)


@router.get("/leads/queue", response_model=LeadQueueOut)
def lead_queue(filter: str = "all", db: Session = Depends(get_db), user: User = Depends(sales)):
    """Черга дзвінків для вікна ліда: хто чекає найдовше; передзвони й недодзвони — коли настане час."""
    return {"ids": leads.queue(db, user, filter)}


@router.post("/orders/{order_id}/lead-result", response_model=LeadStepOut)
def lead_result(order_id: int, body: LeadResultIn, db: Session = Depends(get_db), user: User = Depends(sales)):
    order = _get(db, order_id, user)
    if order.status is None or order.status.code not in leads.OPEN_CODES:
        bad("Лід уже закрито або це не лід")
    d = body.model_dump(exclude_unset=True)
    at = svc.parse_dt(d["at"]) if d.get("at") else None
    try:
        leads.apply_result(db, order, user, d["result"], at=at, reason_id=d.get("reason_id"),
                           duplicate_of_id=d.get("duplicate_of_id"), note=d.get("note") or "")
    except leads.LeadError as e:
        bad(str(e))
    audit.log(db, user, "order", order.id, "lead_result", {"результат": d["result"]})
    db.commit()
    return {"order": _full(db, order), "next_id": _next(db, user, order.id)}


@router.post("/orders/{order_id}/convert", response_model=LeadStepOut)
def lead_convert(order_id: int, db: Session = Depends(get_db), user: User = Depends(sales)):
    order = _get(db, order_id, user)
    if order.status is None or order.status.code not in leads.OPEN_CODES:
        bad("Лід уже закрито або це не лід")
    try:
        leads.convert(db, order, user)
    except leads.LeadError as e:
        bad(str(e), 422)
    db.commit()
    return {"order": _full(db, order), "next_id": _next(db, user, order.id)}


@router.get("/settings/leads/preview", response_model=LeadsPreviewOut)
def leads_preview(db: Session = Depends(get_db), user: User = Depends(admin)):
    return {"enabled": leads.enabled(db), "open": leads.open_leads(db).count()}


@router.post("/settings/leads", response_model=LeadsToggleOut)
def leads_toggle(body: LeadsToggleIn, db: Session = Depends(get_db), user: User = Depends(admin)):
    moved = 0
    if body.enabled:
        st.set_value(db, "leads_enabled", "1")
        audit.log(db, user, "settings", None, "leads_enable", {})
    else:
        moved = leads.disable(db, user, body.move_open)
    db.commit()
    return {"enabled": body.enabled, "moved": moved}
