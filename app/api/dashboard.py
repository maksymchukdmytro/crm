"""Головна сторінка: ключові показники (сьогодні, місяць, покупці, що потребує уваги)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..services import dashboard as svc
from .common import sales
from .schemas import DashboardOut

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db), user: User = Depends(sales)):
    return svc.dashboard(db, user)
