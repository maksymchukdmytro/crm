from datetime import timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import sales
from ..models import User
from ..services import reports as rep
from ..web import parse_date, render, today_local

router = APIRouter()


@router.get("/reports")
def reports(request: Request, date_from: str = "", date_to: str = "", dim: str = "utm_source", manager: int = 0,
            db: Session = Depends(get_db), user: User = Depends(sales)):
    t = today_local()
    d2 = parse_date(date_to, t)
    d1 = parse_date(date_from, d2 - timedelta(days=29))
    if d1 > d2:
        d1, d2 = d2, d1
    if (d2 - d1).days > 366:
        d1 = d2 - timedelta(days=366)
    if dim not in rep.DIMENSIONS:
        dim = "utm_source"
    if user.role == "manager":
        manager = user.id  # менеджер бачить лише власну статистику
    data = rep.build(db, d1, d2, dim, manager or None)
    managers = db.query(User).filter(User.role.in_(["admin", "manager"])).order_by(User.full_name).all()
    ctx = {"r": data, "date_from": d1, "date_to": d2, "dim": dim, "dims": rep.DIMENSIONS, "f_manager": manager,
           "managers": managers}
    return render(request, "reports/index.html", ctx, active="reports")
