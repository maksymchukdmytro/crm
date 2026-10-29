from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..deps import admin_only
from ..models import AuditLog, User
from ..services.audit import ACTION_NAMES
from ..services.reports import period_bounds
from ..web import parse_date, render

router = APIRouter()
ENTITIES = {"order": "Замовлення", "product": "Товар", "purchase": "Закупівля", "user": "Користувач",
            "settings": "Налаштування"}
PER_PAGE = 100


@router.get("/audit")
def audit_page(request: Request, entity: str = "", user_id: int = 0, action: str = "", date_from: str = "",
               date_to: str = "", page: int = 1, db: Session = Depends(get_db), user: User = Depends(admin_only)):
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
    page = max(page, 1)
    rows = q.order_by(AuditLog.id.desc()).offset((page - 1) * PER_PAGE).limit(PER_PAGE + 1).all()
    users = db.query(User).order_by(User.username).all()
    ctx = {"rows": rows[:PER_PAGE], "has_next": len(rows) > PER_PAGE, "page": page, "users": users,
           "entities": ENTITIES, "actions": ACTION_NAMES,
           "f": {"entity": entity, "user_id": user_id, "action": action, "date_from": date_from, "date_to": date_to}}
    return render(request, "audit.html", ctx, active="audit")
