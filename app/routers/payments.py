"""Звірка грошей: накладені платежі, що очікуються, зібрані перевізником і зараховані."""
import csv
import io
from decimal import Decimal

from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload
from starlette.datastructures import FormData

from ..db import get_db
from ..deps import admin_only
from ..models import DELIVERY_METHODS, PAYMENT_STATUSES, Order, Payment, User
from ..services import payments as pay_svc
from ..services.orders import to_int
from ..web import flash, redirect, render, safe_next
from .orders import form_data

router = APIRouter()

TTN_HEADERS = ("ттн", "ен", "ен ", "номер", "number", "ttn", "декларац", "відправлення", "barcode", "штрихкод")
SUM_HEADERS = ("сума", "sum", "amount", "переказ", "післяплат", "наложен", "накладен", "до виплати")


class _Semicolon(csv.excel):
    delimiter = ";"


def _detect_columns(header: list[str]) -> tuple[int | None, int | None]:
    low = [h.strip().lower() for h in header]
    ttn_col = next((i for i, h in enumerate(low) if any(k in h for k in TTN_HEADERS)), None)
    sum_col = next((i for i, h in enumerate(low) if any(k in h for k in SUM_HEADERS) and i != ttn_col), None)
    return ttn_col, sum_col


def parse_registry(content: bytes) -> tuple[list[dict], str]:
    for enc in ("utf-8-sig", "cp1251"):
        try:
            text = content.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        return [], "Не вдалося прочитати файл (очікується CSV у UTF-8 або Windows-1251)"
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
    except csv.Error:
        dialect = _Semicolon
    rows = list(csv.reader(io.StringIO(text), dialect))
    if not rows:
        return [], "Файл порожній"
    ttn_col, sum_col = _detect_columns(rows[0])
    start = 1
    if ttn_col is None:
        # без заголовка: перша колонка — ТТН, друга — сума
        ttn_col, sum_col, start = 0, 1, 0
    result = []
    for r in rows[start:]:
        if len(r) <= ttn_col:
            continue
        result.append({"ttn": r[ttn_col], "amount": r[sum_col] if sum_col is not None and len(r) > sum_col else ""})
    return result, ""


@router.get("/payments")
def payments_page(request: Request, status: str = "collected", method: str = "", db: Session = Depends(get_db),
                  user: User = Depends(admin_only)):
    q = (db.query(Payment).options(selectinload(Payment.order).selectinload(Order.status))
         .filter(Payment.kind == "cod"))
    if status:
        q = q.filter(Payment.status == status)
    if method:
        q = q.filter(Payment.method == method)
    rows = q.order_by(Payment.id.desc()).limit(500).all()
    totals = dict(db.query(Payment.status, func.coalesce(func.sum(Payment.amount), 0))
                  .filter(Payment.kind == "cod").group_by(Payment.status).all())
    counts = dict(db.query(Payment.status, func.count(Payment.id)).filter(Payment.kind == "cod")
                  .group_by(Payment.status).all())
    ctx = {"rows": rows, "f_status": status, "f_method": method, "totals": totals, "counts": counts,
           "statuses": PAYMENT_STATUSES, "methods": DELIVERY_METHODS,
           "report": request.session.pop("_import_report", None)}
    return render(request, "payments/index.html", ctx, active="payments")


@router.post("/payments/receive")
def payments_receive(request: Request, form: FormData = Depends(form_data), db: Session = Depends(get_db),
                     user: User = Depends(admin_only)):
    ids = [to_int(x) for x in form.getlist("ids") if to_int(x)]
    n = 0
    for p in db.query(Payment).filter(Payment.id.in_(ids)).all():
        if p.status in ("expected", "collected"):
            pay_svc.mark_received(db, p, user, reference=(form.get("reference") or "")[:255])
            n += 1
    db.commit()
    flash(request, f"Позначено як отримані: {n}")
    return redirect(safe_next(form.get("back"), "/payments"))


@router.post("/payments/import")
async def payments_import(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db),
                          user: User = Depends(admin_only)):
    content = await file.read()
    rows, err = parse_registry(content)
    if err:
        flash(request, err, "error")
        return redirect("/payments")
    report = pay_svc.import_registry(db, rows, user)
    db.commit()

    def ser(items):
        return [{k: (str(v) if isinstance(v, Decimal) else v) for k, v in it.items()} for it in items[:300]]

    request.session["_import_report"] = {k: ser(v) for k, v in report.items()}
    flash(request, f"Зараховано: {len(report['matched'])}, розбіжність суми: {len(report['mismatch'])}, "
                   f"не знайдено ТТН: {len(report['not_found'])}, вже були зараховані: {len(report['already'])}",
          "warn" if report["mismatch"] or report["not_found"] else "ok")
    return redirect("/payments?status=received")
