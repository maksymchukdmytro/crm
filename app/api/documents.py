"""API видаткових накладних (UI-DESIGN §6): реєстр документів, видача з номером, знімок для PDF, друк, перевипуск, анулювання, експорт."""
from __future__ import annotations

import csv
import io
from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..models import IssuedDocument, LegalEntity, Order, User
from ..services import documents as svc
from ..services import orders as order_svc
from ..services.reports import period_bounds
from .common import bad, iso, staff
from .schemas import DocListOut, IssuedDocOut, IssuedDocWithSnapOut

router = APIRouter(prefix="/api", tags=["documents"])
KIND_ALIAS = {"waybill": "waybill", "invoice": "invoice", "warranty": "warranty", "nakladna": "waybill", "rahunok": "invoice", "garantiya": "warranty"}


def _period(period: str) -> tuple:
    """«2026-10» — місяць; «2026-10-01..2026-10-29» — свій період; порожньо — поточний місяць."""
    today = date.today()
    try:
        if ".." in period:
            a, b = period.split("..", 1)
            return period_bounds(date.fromisoformat(a), date.fromisoformat(b))
        if len(period) == 7:
            y, m = map(int, period.split("-"))
            start = date(y, m, 1)
        else:
            start = today.replace(day=1)
    except ValueError:
        start = today.replace(day=1)
    end = (start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    return period_bounds(start, end)


def _visible_ids(db: Session, user: User):
    return order_svc.visible_orders_query(db, user).with_entities(Order.id).subquery()


def _j(d: IssuedDocument, order: Order | None = None) -> dict:
    return {"id": d.id, "kind": d.kind, "number_text": d.number_text, "issued_at": iso(d.issued_at), "order_id": d.order_id,
            "customer": (d.snapshot or {}).get("order", {}).get("buyer", ""), "total": float(d.total or 0), "state": d.state,
            "entity_id": d.legal_entity_id, "entity": d.legal_entity.name if d.legal_entity else "",
            "changed": svc.is_changed(d, order), "print_count": d.print_count or 0, "replaced_by_id": d.replaced_by_id}


def _q(db: Session, user: User, entity: int, period: str, q: str, has_invoice: str, status: str):
    start, end = _period(period)
    base = (db.query(IssuedDocument).options(selectinload(IssuedDocument.legal_entity))
            .filter(IssuedDocument.kind == "waybill", IssuedDocument.issued_at >= start, IssuedDocument.issued_at < end,
                    or_(IssuedDocument.order_id.is_(None), IssuedDocument.order_id.in_(_visible_ids(db, user).select()))))
    if q:
        digits = "".join(ch for ch in q if ch.isdigit())
        conds = [IssuedDocument.number_text.ilike(f"%{q}%")]
        if digits:
            conds.append(IssuedDocument.order_id == int(digits[:9]))
        names = db.query(Order.id).filter(Order.customer_name.ilike(f"%{q}%")).subquery()
        conds.append(IssuedDocument.order_id.in_(names.select()))
        base = base.filter(or_(*conds))
    if has_invoice == "1":
        inv = db.query(IssuedDocument.order_id).filter(IssuedDocument.kind == "invoice", IssuedDocument.state == "active").subquery()
        base = base.filter(IssuedDocument.order_id.in_(inv.select()))
    if status:
        sids = [int(x) for x in status.split(",") if x.isdigit()]
        oids = db.query(Order.id).filter(Order.status_id.in_(sids)).subquery()
        base = base.filter(IssuedDocument.order_id.in_(oids.select()))
    tabs_base = base
    if entity:
        base = base.filter(IssuedDocument.legal_entity_id == entity)
    return base, tabs_base


@router.get("/documents", response_model=DocListOut)
def list_documents(entity: int = 0, period: str = "", q: str = "", has_invoice: str = "", status: str = "", offset: int = 0, limit: int = 200,
                   db: Session = Depends(get_db), user: User = Depends(staff)):
    base, tabs_base = _q(db, user, entity, period, q.strip(), has_invoice, status)
    rows = base.order_by(IssuedDocument.issued_at.desc(), IssuedDocument.id.desc()).offset(offset).limit(min(limit, 500)).all()
    oids = [d.order_id for d in rows if d.order_id]
    orders = {o.id: o for o in db.query(Order).options(selectinload(Order.items)).filter(Order.id.in_(oids))} if oids else {}
    others = {}
    for d in db.query(IssuedDocument).filter(IssuedDocument.order_id.in_(oids), IssuedDocument.kind.in_(("invoice", "warranty")),
                                             IssuedDocument.state == "active").all() if oids else []:
        others.setdefault(d.order_id, {})[d.kind] = d.id
    out = []
    for d in rows:
        r = _j(d, orders.get(d.order_id))
        r["docs"] = {"waybill": d.id, "invoice": others.get(d.order_id, {}).get("invoice"), "warranty": others.get(d.order_id, {}).get("warranty")}
        out.append(r)
    active = base.filter(IssuedDocument.state == "active")
    by_entity = dict(tabs_base.with_entities(IssuedDocument.legal_entity_id, func.count(IssuedDocument.id)).group_by(IssuedDocument.legal_entity_id).all())
    names = {e.id: e.name for e in db.query(LegalEntity)}
    return {"rows": out, "total": base.count(),
            "sum": float(active.with_entities(func.coalesce(func.sum(IssuedDocument.total), 0)).scalar() or 0),
            "count_active": active.count(),
            "entities": [{"id": k, "name": names.get(k, "Без юрособи"), "count": v} for k, v in by_entity.items() if k is not None]
                        + ([{"id": 0, "name": "Без юрособи", "count": by_entity[None]}] if None in by_entity else []),
            "all": sum(by_entity.values())}


@router.get("/documents/export")
def export_documents(entity: int = 0, period: str = "", q: str = "", has_invoice: str = "", status: str = "",
                     db: Session = Depends(get_db), user: User = Depends(staff)):
    """Реєстр видаткових для бухгалтера: CSV з «;» і BOM — відкривається в Excel без налаштувань."""
    base, _ = _q(db, user, entity, period, q.strip(), has_invoice, status)
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["№ накладної", "Дата", "Замовлення", "Покупець", "Юрособа", "Сума", "Стан"])
    for d in base.order_by(IssuedDocument.issued_at, IssuedDocument.id):
        w.writerow([d.number_text, d.issued_at.strftime("%d.%m.%Y") if d.issued_at else "", d.order_id or "",
                    (d.snapshot or {}).get("order", {}).get("buyer", ""), d.legal_entity.name if d.legal_entity else "",
                    f"{Decimal(d.total or 0):.2f}".replace(".", ","), "чинна" if d.state == "active" else "анульована"])
    return Response("﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="vydatkovi-{period or "misiac"}.csv"'})


def _doc(db: Session, doc_id: int, user: User) -> IssuedDocument:
    d = db.get(IssuedDocument, doc_id)
    if d is None:
        bad("Документ не знайдено", 404)
    if d.order_id:
        o = db.get(Order, d.order_id)
        if o is not None and not order_svc.can_view(db, user, o):
            bad("Документ не знайдено", 404)
    return d


def _with_snap(db: Session, d: IssuedDocument) -> dict:
    order = db.get(Order, d.order_id) if d.order_id else None
    return {**_j(d, order), "snapshot": d.snapshot or {}}


@router.post("/orders/{order_id}/documents/{kind}", response_model=IssuedDocWithSnapOut)
def issue_document(order_id: int, kind: str, db: Session = Depends(get_db), user: User = Depends(staff)):
    """Видати документ (або повернути чинний) — кнопки «Друк ▾» у картці."""
    k = KIND_ALIAS.get(kind)
    if not k:
        bad("Невідомий тип документа")
    order = db.get(Order, order_id)
    if order is None or not order_svc.can_view(db, user, order):
        bad("Замовлення не знайдено", 404)
    try:
        d = svc.issue(db, order, k, user)
    except svc.DocumentError as e:
        bad(str(e))
    db.commit()
    return _with_snap(db, d)


@router.get("/documents/{doc_id}", response_model=IssuedDocWithSnapOut)
def get_document(doc_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    return _with_snap(db, _doc(db, doc_id, user))


@router.post("/documents/{doc_id}/printed", response_model=IssuedDocOut)
def document_printed(doc_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    d = _doc(db, doc_id, user)
    svc.printed(db, d)
    db.commit()
    return _j(d)


@router.post("/documents/{doc_id}/reissue", response_model=IssuedDocWithSnapOut)
def document_reissue(doc_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    d = _doc(db, doc_id, user)
    if d.state != "active":
        bad("Документ уже анульовано")
    try:
        new = svc.reissue(db, d, user)
    except svc.DocumentError as e:
        bad(str(e))
    db.commit()
    return _with_snap(db, new)


@router.post("/documents/{doc_id}/void", response_model=IssuedDocOut)
def document_void(doc_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    d = _doc(db, doc_id, user)
    svc.void(db, d, user)
    db.commit()
    return _j(d)
