"""Статистика: графік статусів, основне / допродаж, товари, розрізи, цінові сегменти, замовлення, експорт CSV."""
from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..services import stats as svc
from ..formatting import today_local
from .common import sales
from .schemas import (
    StatsBreakdownOut, StatsOptionsOut, StatsOrdersOut, StatsOut, StatsProductsOut, StatsQuery, StatsSegmentsOut,
)

router = APIRouter(prefix="/api", tags=["stats"])
Filters = Annotated[StatsQuery, Query()]


def _f(q: StatsQuery) -> svc.StatsFilter:
    return svc.StatsFilter.parse({k: (str(v) if not isinstance(v, bool) else ("1" if v else "")) for k, v in q.model_dump().items()},
                                 today_local())


@router.get("/stats", response_model=StatsOut)
def stats(q: Filters, db: Session = Depends(get_db), user: User = Depends(sales)):
    return svc.stats(db, user, _f(q))


@router.get("/stats/products", response_model=StatsProductsOut)
def stats_products(q: Filters, db: Session = Depends(get_db), user: User = Depends(sales)):
    return {"rows": svc.products(db, user, _f(q))}


@router.get("/stats/breakdown", response_model=StatsBreakdownOut)
def stats_breakdown(q: Filters, dim: str = "source", db: Session = Depends(get_db), user: User = Depends(sales)):
    dim = dim if dim in svc.DIMENSIONS else "source"
    return {"dim": dim, "rows": svc.breakdown(db, user, _f(q), dim)}


@router.get("/stats/segments", response_model=StatsSegmentsOut)
def stats_segments(q: Filters, metric: str = "orders_total", db: Session = Depends(get_db), user: User = Depends(sales)):
    return svc.segments(db, user, _f(q), metric)


@router.get("/stats/orders", response_model=StatsOrdersOut)
def stats_orders(q: Filters, offset: int = 0, limit: int = 100, db: Session = Depends(get_db), user: User = Depends(sales)):
    return svc.orders_page(db, user, _f(q), offset, limit)


@router.get("/stats/options", response_model=StatsOptionsOut)
def stats_options(db: Session = Depends(get_db), user: User = Depends(sales)):
    return {
        "values": svc.options(db, user),
        "date_fields": {k: v[1] for k, v in svc.DATE_FIELDS.items()},
        "dimensions": svc.DIMENSIONS,
        "segment_metrics": svc.SEGMENT_METRICS,
    }


# ---------------------------------------------------------------- експорт у CSV (Excel відкриває з кирилицею)
def _csv(name: str, header: list[str], rows: list[list]) -> Response:
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(header)
    for r in rows:
        w.writerow(["" if v is None else (str(v).replace(".", ",") if isinstance(v, float) else v) for v in r])
    return Response("﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{name}.csv"'})


@router.get("/stats/export.csv", include_in_schema=False)
def stats_export(q: Filters, kind: str = "products", dim: str = "source",
                 db: Session = Depends(get_db), user: User = Depends(sales)):
    f = _f(q)
    period = f"{f.date_from:%Y%m%d}-{f.date_to:%Y%m%d}" if not f.all_time else "all"
    if kind == "breakdown":
        dim = dim if dim in svc.DIMENSIONS else "source"
        rows = svc.breakdown(db, user, f, dim)
        return _csv(f"stats-{dim}-{period}", [
            svc.DIMENSIONS[dim], "Замовлення", "Апрув", "Апрув, %", "Відправлено", "Отримано", "Відмови", "Викуп, %",
            "Сума", "Маржа", "Середній чек", "Допродажі, %"],
            [[r["label"], r["orders"], r["approved"], r["approve_rate"], r["shipped"], r["delivered"], r["refused"],
              r["buyout_rate"], r["sum"], r["margin"], r["avg_check"], r["upsell_rate"]] for r in rows])
    if kind == "orders":
        page = svc.orders_page(db, user, f, 0, svc.MAX_ORDERS_LIST)
        return _csv(f"stats-orders-{period}", [
            "№", "№ маркетплейсу", "Покупець", "Телефон", "Товари", "Сума", "Маржа", "Оплата", "Доставка", "ТТН",
            "Додане", "Підтвердження, хв", "Відправлене", "Отримане", "Змінене", "Відділ", "Менеджер", "Сайт",
            "utm_source", "utm_medium", "utm_term", "utm_content", "utm_campaign", "Поле 1", "Поле 2", "Поле 3", "Поле 4"],
            [[r["id"], r["external_id"], r["customer_name"], r["phone"],
              ", ".join(f"{i['name']} ×{i['qty']}" + (" (допродаж)" if i["is_upsell"] else "") for i in r["items"]),
              r["total"], r["margin"], r["payment"], r["delivery"], r["ttn"], _dt(r["created_at"]),
              round(r["confirm_secs"] / 60) if r["confirm_secs"] is not None else "", _dt(r["shipped_at"]),
              _dt(r["delivered_at"]), _dt(r["updated_at"]), r["office"], r["manager"], r["site"], r["utm_source"],
              r["utm_medium"], r["utm_term"], r["utm_content"], r["utm_campaign"], r["extra1"], r["extra2"],
              r["extra3"], r["extra4"]] for r in page["rows"]])
    rows = svc.products(db, user, f, limit=100_000)
    return _csv(f"stats-products-{period}", [
        "ID", "Артикул", "Товар", "Категорія", "Замовлень", "Кількість", "Основний", "Допродаж",
        "Сума", "Сума основного", "Сума допродажу", "Маржа", "Маржа основного", "Маржа допродажу"],
        [[r["product_id"], r["sku"], r["name"], r["category"], r["orders"], r["qty"], r["qty_main"], r["qty_upsell"],
          r["sum"], r["sum_main"], r["sum_upsell"], r["margin"], r["margin_main"], r["margin_upsell"]] for r in rows])


def _dt(iso: str | None) -> str:
    if not iso:
        return ""
    v = svc.to_local(datetime.fromisoformat(iso.rstrip("Z")))
    return f"{v:%d.%m.%Y %H:%M}"
