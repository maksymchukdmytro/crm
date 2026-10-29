"""Аналітика: апрув, викуп, виручка і прибуток у розрізі джерел, менеджерів, товарів і днів."""
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session, selectinload

from ..config import config
from ..models import Order, Status

DIMENSIONS = {
    "utm_source": "Джерело (utm_source)",
    "utm_campaign": "Кампанія (utm_campaign)",
    "utm_medium": "Канал (utm_medium)",
    "utm_content": "Оголошення (utm_content)",
    "site": "Сайт / лендинг",
    "manager": "Менеджер",
    "delivery_method": "Служба доставки",
}


def period_bounds(date_from: date, date_to: date) -> tuple[datetime, datetime]:
    """Межі періоду в UTC з урахуванням часового поясу відображення."""
    tz = ZoneInfo(config.DISPLAY_TZ)
    start = datetime.combine(date_from, datetime.min.time(), tz).astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    end = datetime.combine(date_to + timedelta(days=1), datetime.min.time(), tz)
    return start, end.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)


class Bucket:
    __slots__ = ("leads", "unique", "approved", "shipped", "delivered", "refused",
                 "revenue", "cost", "delivery", "approved_sum")

    def __init__(self):
        self.leads = self.unique = self.approved = self.shipped = self.delivered = self.refused = 0
        self.revenue = self.cost = self.delivery = self.approved_sum = Decimal(0)

    def add(self, o: Order, st: Status):
        self.leads += 1
        if o.duplicate_of_id is None and st.code != "duplicate":
            self.unique += 1
        if st.counts_as_approved:
            self.approved += 1
            self.approved_sum += Decimal(o.total or 0)
        if o.shipped_at or st.code in ("shipped", "delivered", "refused", "returned"):
            self.shipped += 1
        if st.code == "delivered" or o.delivery_state == "delivered":
            self.delivered += 1
            self.revenue += Decimal(o.total or 0)
            self.cost += o.items_cost
            self.delivery += Decimal(o.delivery_cost or 0)
        elif st.code in ("refused", "returned") or o.delivery_state in ("refused", "returned"):
            self.refused += 1

    @property
    def approve_rate(self) -> float:
        return self.approved / self.unique * 100 if self.unique else 0.0

    @property
    def buyout_rate(self) -> float:
        done = self.delivered + self.refused
        return self.delivered / done * 100 if done else 0.0

    @property
    def profit(self) -> Decimal:
        return self.revenue - self.cost

    @property
    def avg_check(self) -> Decimal:
        return (self.approved_sum / self.approved).quantize(Decimal("0.01")) if self.approved else Decimal(0)


def _key(o: Order, dim: str) -> str:
    if dim == "manager":
        return o.manager.display if o.manager else "Не призначено"
    if dim == "delivery_method":
        return o.delivery_method_name
    return getattr(o, dim, "") or "(не вказано)"


def build(db: Session, date_from: date, date_to: date, dimension: str = "utm_source",
          manager_id: int | None = None) -> dict:
    start, end = period_bounds(date_from, date_to)
    q = (
        db.query(Order)
        .options(selectinload(Order.items), selectinload(Order.manager), selectinload(Order.status))
        .filter(Order.created_at >= start, Order.created_at < end)
    )
    if manager_id:
        q = q.filter(Order.manager_id == manager_id)
    orders = q.all()

    total = Bucket()
    groups: dict[str, Bucket] = defaultdict(Bucket)
    days: dict[date, Bucket] = defaultdict(Bucket)
    products: dict[str, dict] = defaultdict(lambda: {"qty": 0, "revenue": Decimal(0), "cost": Decimal(0),
                                                     "upsell_qty": 0, "orders": 0})
    tz = ZoneInfo(config.DISPLAY_TZ)
    for o in orders:
        st = o.status
        total.add(o, st)
        groups[_key(o, dimension)].add(o, st)
        local_day = o.created_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz).date()
        days[local_day].add(o, st)
        if st.counts_as_approved:
            for it in o.items:
                p = products[it.name]
                p["qty"] += it.qty
                p["orders"] += 1
                p["revenue"] += Decimal(it.price or 0) * it.qty
                p["cost"] += Decimal(it.cost or 0) * it.qty
                if it.is_upsell:
                    p["upsell_qty"] += it.qty

    day_rows = []
    d = date_from
    while d <= date_to:
        day_rows.append((d, days.get(d, Bucket())))
        d += timedelta(days=1)

    return {
        "total": total,
        "groups": sorted(groups.items(), key=lambda kv: kv[1].leads, reverse=True),
        "days": day_rows,
        "max_day_leads": max((b.leads for _, b in day_rows), default=0),
        "products": sorted(products.items(), key=lambda kv: kv[1]["revenue"], reverse=True),
        "count": len(orders),
    }
