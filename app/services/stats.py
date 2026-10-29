"""Статистика замовлень (як у LP-CRM і більше): графік статусів за часом, основне / допродаж, товари,
розрізи (джерело, менеджер, UTM…), цінові сегменти, список замовлень. Усе рахується в SQL — швидко
й на сотнях тисяч замовлень. Видимість замовлень (свої / відділи) береться з visible_orders_query."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import Integer, and_, case, cast, func, literal, or_, select
from sqlalchemy.orm import Query, Session, selectinload

from ..config import config
from ..models import (
    COUNTRIES, DELIVERY_METHODS, MarketplaceShop, Office, Order, OrderItem, OrderSource, PaymentMethod, Product,
    Status, StatusReason, User, utcnow,
)
from .orders import visible_orders_query
from .reports import period_bounds

EMPTY = "__empty__"  # значення фільтра «Пусте поле»
UTC = ZoneInfo("UTC")

# тип дати: поле замовлення і назва (як у LP-CRM + власні)
DATE_FIELDS: dict[str, tuple[str, str]] = {
    "created": ("created_at", "Додане"),
    "assigned": ("assigned_at", "Закріплене"),
    "confirmed": ("confirmed_at", "Підтверджене"),
    "shipped": ("shipped_at", "Відправлене"),
    "delivered": ("delivered_at", "Отримане"),
    "status": ("status_changed_at", "Зміна статусу"),
    "changed": ("updated_at", "Змінене"),
}
GROUPS = ("auto", "hour", "day", "week", "month")

# фільтри: параметр → (колонка, тип); тип id — числа, str — рядки
ID_FILTERS = {
    "status": "status_id", "reason": "reason_id", "payment": "payment_method_id", "office": "office_id",
    "source": "source_id", "manager": "manager_id", "shop": "shop_id", "np_account": "np_account_id", "mark": "mark_id",
    "legal_entity": "legal_entity_id",
}
STR_FILTERS = {
    "delivery": "delivery_method", "country": "country", "site": "site",
    "utm_source": "utm_source", "utm_medium": "utm_medium", "utm_term": "utm_term",
    "utm_content": "utm_content", "utm_campaign": "utm_campaign",
    "extra1": "extra1", "extra2": "extra2", "extra3": "extra3", "extra4": "extra4",
}
OPTION_FIELDS = ("site", "utm_source", "utm_medium", "utm_term", "utm_content", "utm_campaign",
                 "extra1", "extra2", "extra3", "extra4")

# розрізи: ключ → назва (порядок — як у випадному списку)
DIMENSIONS: dict[str, str] = {
    "source": "Джерело", "utm_source": "utm_source", "utm_medium": "utm_medium", "utm_campaign": "utm_campaign",
    "utm_content": "utm_content", "utm_term": "utm_term", "site": "Сайт", "manager": "Менеджер", "office": "Відділ",
    "legal_entity": "Юрособа", "payment": "Вид оплати", "delivery": "Доставка", "country": "Країна", "reason": "Причина / атрибут статусу",
    "shop": "Магазин маркетплейсу", "extra1": "Додаткове поле 1", "extra2": "Додаткове поле 2",
    "extra3": "Додаткове поле 3", "extra4": "Додаткове поле 4", "weekday": "День тижня", "hour": "Година доби",
}
WEEKDAYS = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"]

SEGMENT_METRICS = {
    "orders_total": "Загальна вартість замовлення",
    "offer_total": "Вартість основного товару (оферу)",
    "upsell_total": "Вартість допродажів у замовленні",
    "upsell_rate": "Відсоток замовлень з допродажем",
    "return_rate": "Відсоток відмов і повернень",
}
MAX_ORDERS_LIST = 100_000


def _split(v: str | None) -> list[str]:
    return [x.strip() for x in (v or "").split(",") if x.strip()]


@dataclass
class StatsFilter:
    date_field: str = "created"
    date_from: date | None = None
    date_to: date | None = None
    all_time: bool = False
    group: str = "auto"
    ids: dict[str, tuple[list[int], bool]] = field(default_factory=dict)  # параметр → (id, чи «пусте поле»)
    strs: dict[str, tuple[list[str], bool]] = field(default_factory=dict)
    products: list[int] = field(default_factory=list)
    categories: list[int] = field(default_factory=list)
    upsell: str = ""  # with / without
    search: str = ""  # пошук у додаткових полях і коментарі

    @classmethod
    def parse(cls, raw: dict[str, str | None], today: date) -> "StatsFilter":
        f = cls()
        df = raw.get("date_field") or "created"
        f.date_field = df if df in DATE_FIELDS else "created"
        g = raw.get("group") or "auto"
        f.group = g if g in GROUPS else "auto"
        f.all_time = str(raw.get("all_time") or "").lower() in ("1", "true", "yes")

        def d(v):
            try:
                return date.fromisoformat(v) if v else None
            except ValueError:
                return None

        f.date_to = d(raw.get("date_to")) or today
        f.date_from = d(raw.get("date_from")) or (f.date_to - timedelta(days=29))
        if f.date_from > f.date_to:
            f.date_from, f.date_to = f.date_to, f.date_from
        for key in ID_FILTERS:
            vals = _split(raw.get(key))
            if vals:
                f.ids[key] = ([int(x) for x in vals if x.isdigit()], EMPTY in vals)
        for key in STR_FILTERS:
            vals = _split(raw.get(key))
            if vals:
                f.strs[key] = ([x for x in vals if x != EMPTY], EMPTY in vals)
        f.products = [int(x) for x in _split(raw.get("product")) if x.isdigit()]
        f.categories = [int(x) for x in _split(raw.get("category")) if x.isdigit()]
        f.upsell = raw.get("upsell") or ""
        f.search = (raw.get("search") or "").strip()
        return f

    @property
    def column(self):
        return getattr(Order, DATE_FIELDS[self.date_field][0])


def tz() -> ZoneInfo:
    return ZoneInfo(config.DISPLAY_TZ)


def local_expr(col):
    """Колонка (UTC без поясу) → місцевий час відображення, у SQL."""
    return func.timezone(config.DISPLAY_TZ, func.timezone("UTC", col))


def to_local(v: datetime | None) -> datetime | None:
    return v.replace(tzinfo=UTC).astimezone(tz()).replace(tzinfo=None) if v else None


def apply_filters(q: Query, f: StatsFilter, with_period: bool = True) -> Query:
    """Фільтри статистики, крім періоду (його додає period())."""
    for key, (ids, empty) in f.ids.items():
        col = getattr(Order, ID_FILTERS[key])
        conds = []
        if ids:
            conds.append(col.in_(ids))
        if empty:
            conds.append(col.is_(None))
        if conds:
            q = q.filter(or_(*conds))
    for key, (vals, empty) in f.strs.items():
        col = getattr(Order, STR_FILTERS[key])
        conds = []
        if vals:
            conds.append(col.in_(vals))
        if empty:
            conds.append(or_(col.is_(None), col == ""))
        if conds:
            q = q.filter(or_(*conds))
    if f.products:
        q = q.filter(Order.items.any(OrderItem.product_id.in_(f.products)))
    if f.categories and hasattr(Product, "category_id"):
        cats = set(f.categories)
        from ..models import Category  # етап 6: категорії разом із підкатегоріями
        cats |= {c.id for c in q.session.query(Category).filter(Category.parent_id.in_(f.categories))}
        q = q.filter(Order.items.any(OrderItem.product.has(Product.category_id.in_(cats))))
    if f.upsell == "with":
        q = q.filter(Order.items.any(OrderItem.is_upsell.is_(True)))
    elif f.upsell == "without":
        q = q.filter(~Order.items.any(OrderItem.is_upsell.is_(True)))
    if f.search:
        like = f"%{f.search}%"
        q = q.filter(or_(Order.extra1.ilike(like), Order.extra2.ilike(like), Order.extra3.ilike(like),
                         Order.extra4.ilike(like), Order.comment.ilike(like)))
    return q


def bounds(db: Session, user: User, f: StatsFilter) -> tuple[datetime, datetime, date, date]:
    """Межі періоду (UTC) і дати для показу. «Весь час» — від найранішого замовлення у вибірці."""
    if f.all_time:
        q = apply_filters(visible_orders_query(db, user), f)
        first = q.with_entities(func.min(f.column)).scalar()
        d_from = to_local(first).date() if first else datetime.now(tz()).date()
        d_to = datetime.now(tz()).date()
    else:
        d_from, d_to = f.date_from, f.date_to
    start, end = period_bounds(d_from, d_to)
    return start, end, d_from, d_to


def base_query(db: Session, user: User, f: StatsFilter, start: datetime, end: datetime) -> Query:
    col = f.column
    return apply_filters(visible_orders_query(db, user), f).filter(col.isnot(None), col >= start, col < end)


def pick_group(f: StatsFilter, d_from: date, d_to: date) -> str:
    if f.group != "auto":
        return f.group
    days = (d_to - d_from).days + 1
    if days <= 1:
        return "hour"
    if days <= 120:
        return "day"
    if days <= 730:
        return "week"
    return "month"


def bucket_keys(group: str, d_from: date, d_to: date) -> list[datetime]:
    """Усі відрізки періоду, навіть порожні, щоб графік не «склеював» дні без замовлень."""
    out: list[datetime] = []
    if group == "hour":
        t = datetime.combine(d_from, datetime.min.time())
        end = datetime.combine(d_to + timedelta(days=1), datetime.min.time())
        while t < end and len(out) < 24 * 31:
            out.append(t)
            t += timedelta(hours=1)
    elif group == "day":
        t = d_from
        while t <= d_to and len(out) < 3700:
            out.append(datetime.combine(t, datetime.min.time()))
            t += timedelta(days=1)
    elif group == "week":
        t = d_from - timedelta(days=d_from.weekday())
        while t <= d_to and len(out) < 600:
            out.append(datetime.combine(t, datetime.min.time()))
            t += timedelta(days=7)
    else:
        t = d_from.replace(day=1)
        while t <= d_to and len(out) < 400:
            out.append(datetime.combine(t, datetime.min.time()))
            t = (t.replace(day=28) + timedelta(days=4)).replace(day=1)
    return out


def per_order_items():
    """Підсумки позицій кожного замовлення: кількість, виручка й собівартість основного продажу і допродажу."""
    up = OrderItem.is_upsell.is_(True)
    rev = OrderItem.price * OrderItem.qty
    cost = OrderItem.cost * OrderItem.qty
    return (
        select(
            OrderItem.order_id.label("order_id"),
            func.coalesce(func.sum(case((up, 0), else_=OrderItem.qty)), 0).label("qty_main"),
            func.coalesce(func.sum(case((up, OrderItem.qty), else_=0)), 0).label("qty_up"),
            func.coalesce(func.sum(case((up, 0), else_=rev)), 0).label("rev_main"),
            func.coalesce(func.sum(case((up, rev), else_=0)), 0).label("rev_up"),
            func.coalesce(func.sum(case((up, 0), else_=cost)), 0).label("cost_main"),
            func.coalesce(func.sum(case((up, cost), else_=0)), 0).label("cost_up"),
        )
        .group_by(OrderItem.order_id)
        .subquery("poi")
    )


def _flags():
    approved = Status.counts_as_approved.is_(True)
    delivered = or_(Status.code == "delivered", Order.delivery_state == "delivered")
    refused = and_(~delivered, or_(Status.code.in_(("refused", "returned")),
                                   Order.delivery_state.in_(("refused", "returned"))))
    duplicate = or_(Order.duplicate_of_id.isnot(None), Status.code == "duplicate")
    return approved, delivered, refused, duplicate


def aggregates(poi):
    """Набір агрегатів, спільний для підсумку й розрізів."""
    approved, delivered, refused, duplicate = _flags()
    one = lambda cond: func.coalesce(func.sum(case((cond, 1), else_=0)), 0)  # noqa: E731
    z = lambda c: func.coalesce(func.sum(c), 0)  # noqa: E731
    confirm_secs = func.extract("epoch", Order.confirmed_at - Order.created_at)
    return [
        func.count(Order.id).label("orders"),
        one(duplicate).label("duplicates"),
        one(and_(duplicate, ~approved)).label("dup_open"),
        one(approved).label("approved"),
        one(Order.shipped_at.isnot(None)).label("shipped"),
        one(delivered).label("delivered"),
        one(refused).label("refused"),
        one(poi.c.qty_up > 0).label("orders_upsell"),
        z(poi.c.qty_main).label("qty_main"),
        z(poi.c.qty_up).label("qty_up"),
        z(poi.c.rev_main).label("rev_main"),
        z(poi.c.rev_up).label("rev_up"),
        z(poi.c.cost_main).label("cost_main"),
        z(poi.c.cost_up).label("cost_up"),
        z(Order.discount).label("discount"),
        func.avg(case((and_(Order.confirmed_at.isnot(None), Order.confirmed_at >= Order.created_at), confirm_secs))).label("confirm_avg"),
    ]


def _with_aggregates(q: Query, poi) -> Query:
    return (q.outerjoin(poi, poi.c.order_id == Order.id)
            .join(Status, Status.id == Order.status_id)
            .with_entities(*aggregates(poi)))


def _f(v) -> float:
    return float(round(Decimal(v or 0), 2))


def summary_from(row) -> dict:
    """Підсумок у тих самих термінах, що LP-CRM, плюс апрув, викуп і час підтвердження."""
    n = int(row.orders or 0)
    considered = n - int(row.dup_open or 0)  # дублі, які так і не підтвердили, апрув не псують
    qty_main, qty_up = int(row.qty_main or 0), int(row.qty_up or 0)
    qty = qty_main + qty_up
    disc = Decimal(row.discount or 0)
    sum_main = Decimal(row.rev_main or 0) - disc  # знижка зменшує основний продаж
    sum_up = Decimal(row.rev_up or 0)
    margin_main = Decimal(row.rev_main or 0) - Decimal(row.cost_main or 0) - disc
    margin_up = Decimal(row.rev_up or 0) - Decimal(row.cost_up or 0)
    total, margin = sum_main + sum_up, margin_main + margin_up
    delivered, refused = int(row.delivered or 0), int(row.refused or 0)
    up = int(row.orders_upsell or 0)
    pct = lambda a, b: round(a * 100 / b, 1) if b else 0.0  # noqa: E731
    return {
        "orders": n, "orders_plain": n - up, "orders_upsell": up, "upsell_rate": pct(up, n),
        "qty": qty, "qty_main": qty_main, "qty_upsell": qty_up, "qty_upsell_rate": pct(qty_up, qty),
        "margin": _f(margin), "margin_main": _f(margin_main), "margin_upsell": _f(margin_up),
        "margin_avg": _f(margin / n) if n else 0.0,
        "sum": _f(total), "sum_main": _f(sum_main), "sum_upsell": _f(sum_up),
        "avg_check": _f(total / n) if n else 0.0,
        "duplicates": int(row.duplicates or 0), "approved": int(row.approved or 0),
        "approve_rate": pct(int(row.approved or 0), considered), "shipped": int(row.shipped or 0),
        "delivered": delivered, "refused": refused, "buyout_rate": pct(delivered, delivered + refused),
        "confirm_avg_min": round(float(row.confirm_avg) / 60, 1) if row.confirm_avg is not None else None,
    }


def stats(db: Session, user: User, f: StatsFilter) -> dict:
    start, end, d_from, d_to = bounds(db, user, f)
    q = base_query(db, user, f, start, end)
    group = pick_group(f, d_from, d_to)
    col = f.column

    # графік: (відрізок, статус) → кількість
    bucket = func.date_trunc(group, local_expr(col)).label("b")
    rows = q.with_entities(bucket, Order.status_id, func.count(Order.id)).group_by(bucket, Order.status_id).all()
    series: dict[datetime, dict[int, int]] = {k: {} for k in bucket_keys(group, d_from, d_to)}
    by_status: dict[int, int] = {}
    for b, sid, c in rows:
        series.setdefault(b, {})[sid] = series.get(b, {}).get(sid, 0) + c
        by_status[sid] = by_status.get(sid, 0) + c
    total = sum(by_status.values()) or 1

    poi = per_order_items()
    summary = summary_from(_with_aggregates(q, poi).one())

    # попередній період такої самої довжини — для порівняння
    prev = None
    if not f.all_time:
        span = end - start
        pq = base_query(db, user, f, start - span, start)
        prev = summary_from(_with_aggregates(pq, poi).one())
        p_days = (d_to - d_from).days + 1
        prev["date_from"] = (d_from - timedelta(days=p_days)).isoformat()
        prev["date_to"] = (d_from - timedelta(days=1)).isoformat()

    return {
        "date_from": d_from.isoformat(), "date_to": d_to.isoformat(), "date_field": f.date_field, "group": group,
        "series": [{"t": k.isoformat(timespec="minutes"), "total": sum(v.values()),
                    "by_status": {str(s): c for s, c in v.items()}} for k, v in sorted(series.items())],
        "statuses": [{"status_id": s, "count": c, "share": round(c * 100 / total, 1)}
                     for s, c in sorted(by_status.items(), key=lambda x: -x[1])],
        "summary": summary, "prev": prev,
    }


def products(db: Session, user: User, f: StatsFilter, limit: int = 1000) -> list[dict]:
    """Товари в замовленнях вибірки: кількість, сума, маржа — усього, основний продаж і допродаж."""
    start, end, _, _ = bounds(db, user, f)
    ids = base_query(db, user, f, start, end).with_entities(Order.id).subquery()
    up = OrderItem.is_upsell.is_(True)
    rev, cost = OrderItem.price * OrderItem.qty, OrderItem.cost * OrderItem.qty
    z = lambda c: func.coalesce(func.sum(c), 0)  # noqa: E731
    key = case((OrderItem.product_id.is_(None), OrderItem.name), else_=literal(""))
    rows = (
        db.query(
            OrderItem.product_id, func.max(OrderItem.name).label("item_name"), key.label("k"),
            func.count(func.distinct(OrderItem.order_id)).label("orders"),
            z(case((up, 0), else_=OrderItem.qty)).label("qty_main"), z(case((up, OrderItem.qty), else_=0)).label("qty_up"),
            z(case((up, 0), else_=rev)).label("rev_main"), z(case((up, rev), else_=0)).label("rev_up"),
            z(case((up, 0), else_=cost)).label("cost_main"), z(case((up, cost), else_=0)).label("cost_up"),
        )
        .filter(OrderItem.order_id.in_(select(ids.c.id)))
        .group_by(OrderItem.product_id, key)
        .all()
    )
    pmap = {p.id: p for p in db.query(Product).filter(Product.id.in_([r.product_id for r in rows if r.product_id]))}
    out = []
    for r in rows:
        p = pmap.get(r.product_id)
        mm = Decimal(r.rev_main) - Decimal(r.cost_main)
        mu = Decimal(r.rev_up) - Decimal(r.cost_up)
        out.append({
            "product_id": r.product_id, "name": p.name if p else r.item_name, "sku": (p.sku or "") if p else "",
            "category": _category_name(p), "orders": int(r.orders),
            "qty": int(r.qty_main) + int(r.qty_up), "qty_main": int(r.qty_main), "qty_upsell": int(r.qty_up),
            "sum": _f(Decimal(r.rev_main) + Decimal(r.rev_up)), "sum_main": _f(r.rev_main), "sum_upsell": _f(r.rev_up),
            "margin": _f(mm + mu), "margin_main": _f(mm), "margin_upsell": _f(mu),
        })
    out.sort(key=lambda x: (-x["qty"], -x["sum"]))
    return out[:limit]


def _category_name(p: Product | None) -> str:
    cat = getattr(p, "category", None) if p else None
    return cat.name if cat is not None else ""


def _dim_expr(dim: str):
    if dim == "weekday":
        return cast(func.extract("isodow", local_expr(Order.created_at)), Integer)
    if dim == "hour":
        return cast(func.extract("hour", local_expr(Order.created_at)), Integer)
    if dim in STR_FILTERS:
        return getattr(Order, STR_FILTERS[dim])
    return getattr(Order, ID_FILTERS[dim])


def _dim_labels(db: Session, dim: str, keys: list) -> dict:
    ids = [k for k in keys if k is not None]
    from ..models import LegalEntity
    models = {"source": OrderSource, "office": Office, "payment": PaymentMethod, "reason": StatusReason, "legal_entity": LegalEntity}
    if dim in models:
        return {x.id: x.name for x in db.query(models[dim]).filter(models[dim].id.in_(ids))}
    if dim == "manager":
        return {u.id: u.display for u in db.query(User).filter(User.id.in_(ids))}
    if dim == "shop":
        return {s.id: f"{s.kind.capitalize()} · {s.name}" for s in db.query(MarketplaceShop).filter(MarketplaceShop.id.in_(ids))}
    if dim == "delivery":
        return {k: DELIVERY_METHODS.get(k, k) for k in ids}
    if dim == "country":
        return {k: COUNTRIES.get(k, k) for k in ids}
    if dim == "weekday":
        return {k: WEEKDAYS[k - 1] for k in ids if 1 <= k <= 7}
    if dim == "hour":
        return {k: f"{k:02d}:00–{k:02d}:59" for k in ids}
    return {k: k for k in ids}


def breakdown(db: Session, user: User, f: StatsFilter, dim: str) -> list[dict]:
    """Розріз вибірки: на кожне значення — замовлення, апрув, викуп, сума, маржа, середній чек, допродажі."""
    if dim not in DIMENSIONS:
        dim = "source"
    start, end, _, _ = bounds(db, user, f)
    q = base_query(db, user, f, start, end)
    poi = per_order_items()
    key = _dim_expr(dim).label("k")
    rows = (q.outerjoin(poi, poi.c.order_id == Order.id).join(Status, Status.id == Order.status_id)
            .with_entities(key, *aggregates(poi)).group_by(key).all())
    keys = [None if r.k in ("", None) else r.k for r in rows]
    labels = _dim_labels(db, dim, keys)
    out = []
    for r, k in zip(rows, keys):
        s = summary_from(r)
        out.append({"key": EMPTY if k is None else str(k), "label": "Пусте поле" if k is None else str(labels.get(k, k)), **s})
    if dim in ("weekday", "hour"):
        out.sort(key=lambda x: int(x["key"]) if x["key"].isdigit() else 99)
    else:
        out.sort(key=lambda x: -x["orders"])
    return out


def segments(db: Session, user: User, f: StatsFilter, metric: str) -> dict:
    """Цінові сегменти (аналог «Показників ринків» LP-CRM, але на власних замовленнях)."""
    if metric not in SEGMENT_METRICS:
        metric = "orders_total"
    start, end, _, _ = bounds(db, user, f)
    q = base_query(db, user, f, start, end)
    poi = per_order_items()
    approved, delivered, refused, _dup = _flags()
    rows = (q.outerjoin(poi, poi.c.order_id == Order.id).join(Status, Status.id == Order.status_id)
            .with_entities(Order.total, poi.c.rev_main, poi.c.rev_up, Order.discount, delivered.label("dl"), refused.label("rf"))
            .limit(MAX_ORDERS_LIST).all())
    pts = []
    for r in rows:
        main = float(Decimal(r.rev_main or 0) - Decimal(r.discount or 0))
        up = float(r.rev_up or 0)
        value = {"offer_total": main, "upsell_total": up}.get(metric, float(r.total or 0))
        if metric == "upsell_total" and up <= 0:
            continue
        pts.append((value, up > 0, bool(r.dl), bool(r.rf)))
    if not pts:
        return {"metric": metric, "step": 0, "buckets": []}
    vals = sorted(p[0] for p in pts)
    hi = vals[min(len(vals) - 1, int(len(vals) * 0.98))]  # відкидаємо 2% найдорожчих, щоб не розтягувати вісь
    step = _nice_step(hi / 24 if hi > 0 else 1)
    n = max(1, int(hi // step) + 1)
    buckets = [{"from": i * step, "to": (i + 1) * step, "orders": 0, "upsell": 0, "delivered": 0, "refused": 0} for i in range(n)]
    over = {"from": n * step, "to": None, "orders": 0, "upsell": 0, "delivered": 0, "refused": 0}
    for v, has_up, dl, rf in pts:
        b = buckets[int(v // step)] if v < n * step else over
        b["orders"] += 1
        b["upsell"] += has_up
        b["delivered"] += dl
        b["refused"] += rf
    if over["orders"]:
        buckets.append(over)
    for b in buckets:
        b["upsell_rate"] = round(b["upsell"] * 100 / b["orders"], 1) if b["orders"] else 0
        done = b["delivered"] + b["refused"]
        b["return_rate"] = round(b["refused"] * 100 / done, 1) if done else 0
    return {"metric": metric, "step": step, "buckets": buckets}


def _nice_step(raw: float) -> float:
    for base in (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 2500, 5000, 10000, 20000, 50000):
        if raw <= base:
            return float(base)
    return float(round(raw, -4))


def orders_page(db: Session, user: User, f: StatsFilter, offset: int = 0, limit: int = 100) -> dict:
    """Розширений режим: перелік замовлень вибірки з товарами, датами й мітками — як у LP-CRM."""
    start, end, _, _ = bounds(db, user, f)
    q = base_query(db, user, f, start, end)
    total = q.count()
    items = (q.options(selectinload(Order.items), selectinload(Order.manager), selectinload(Order.payment_method))
             .order_by(f.column.desc(), Order.id.desc()).offset(max(0, offset)).limit(max(1, min(limit, 500))).all())
    offices = {o.id: o.name for o in db.query(Office)}
    return {"total": total, "offset": offset, "rows": [order_row(o, offices) for o in items]}


def order_row(o: Order, offices: dict[int, str]) -> dict:
    iso = lambda v: v.isoformat() + "Z" if v else None  # noqa: E731
    rev = sum((Decimal(i.price or 0) * i.qty for i in o.items), Decimal(0))
    cost = sum((Decimal(i.cost or 0) * i.qty for i in o.items), Decimal(0))
    confirm = None
    if o.confirmed_at and o.confirmed_at >= o.created_at:
        confirm = int((o.confirmed_at - o.created_at).total_seconds())
    return {
        "id": o.id, "external_id": o.external_id, "status_id": o.status_id,
        "customer_name": o.customer_name, "phone": o.phone,
        "items": [{"name": i.name, "qty": i.qty, "price": _f(i.price), "cost": _f(i.cost), "is_upsell": bool(i.is_upsell)}
                  for i in o.items],
        "total": _f(o.total), "margin": _f(rev - cost - Decimal(o.discount or 0)),
        "payment": o.payment_method.name if o.payment_method else "", "delivery": DELIVERY_METHODS.get(o.delivery_method, o.delivery_method),
        "ttn": o.ttn, "created_at": iso(o.created_at), "confirm_secs": confirm, "assigned_at": iso(o.assigned_at),
        "shipped_at": iso(o.shipped_at), "delivered_at": iso(o.delivered_at), "updated_at": iso(o.updated_at),
        "office": offices.get(o.office_id, "") if o.office_id else "", "manager": o.manager.display if o.manager else "",
        "site": o.site, "utm_source": o.utm_source, "utm_medium": o.utm_medium, "utm_term": o.utm_term,
        "utm_content": o.utm_content, "utm_campaign": o.utm_campaign,
        "extra1": o.extra1, "extra2": o.extra2, "extra3": o.extra3, "extra4": o.extra4,
    }


def options(db: Session, user: User) -> dict[str, list[dict]]:
    """Значення для фільтрів-рядків (сайт, UTM, додаткові поля): що траплялося за останні 2 роки."""
    since = utcnow() - timedelta(days=730)
    base = visible_orders_query(db, user).filter(Order.created_at >= since)
    out: dict[str, list[dict]] = {}
    for name in OPTION_FIELDS:
        col = getattr(Order, name)
        rows = (base.with_entities(col, func.count(Order.id)).filter(col.isnot(None), col != "")
                .group_by(col).order_by(func.count(Order.id).desc()).limit(300).all())
        out[name] = [{"value": v, "count": c} for v, c in rows]
    return out
