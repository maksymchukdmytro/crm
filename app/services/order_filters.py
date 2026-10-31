"""Фільтри списку замовлень: однакові для списку, лічильників вкладок і експорту CSV."""
from sqlalchemy import or_

from ..formatting import parse_date
from ..models import Order, Status, utcnow
from . import orders as svc
from .reports import period_bounds

FILTER_KEYS = ("status", "q", "manager", "date_from", "date_to", "delivery", "source", "dup", "pay")


def apply(q, f: dict, with_status: bool = True):
    """Фільтри списку замовлень (рядок пошуку, менеджер, джерело, дати, доставка…) — спільні для списку, лічильників і експорту."""
    if f.get("stage") in ("lead", "order"):  # розділ «Ліди» / «Замовлення»
        q = q.filter(Order.status.has(Status.stage == f["stage"]))
    if with_status and f.get("status"):
        q = q.filter(Order.status_id == svc.to_int(f["status"]))
    text = f.get("q")
    if text:
        digits = "".join(ch for ch in text if ch.isdigit())
        conds = [Order.customer_name.ilike(f"%{text}%"), Order.ttn.contains(text.replace(" ", ""))]
        if digits and len(digits) >= 5:
            conds.append(Order.phone.contains(digits[-9:] if len(digits) > 9 else digits))
        if digits and len(digits) <= 9 and digits == text.strip().lstrip("#"):
            conds.append(Order.id == int(digits))
        q = q.filter(or_(*conds))
    if f.get("manager"):  # кілька через кому; «none» — без менеджера
        vals = [x for x in f["manager"].split(",") if x]
        ids = [svc.to_int(x) for x in vals if svc.to_int(x)]
        conds = ([Order.manager_id.in_(ids)] if ids else []) + ([Order.manager_id.is_(None)] if "none" in vals else [])
        if conds:
            q = q.filter(or_(*conds))
    # фільтри-чипи нового інтерфейсу: id через кому
    for key, col in (("src", Order.source_id), ("entity", Order.legal_entity_id), ("pm", Order.payment_method_id), ("mark", Order.mark_id)):
        if f.get(key):
            vals = [x for x in f[key].split(",") if x]
            ids = [svc.to_int(x) for x in vals if svc.to_int(x)]
            conds = ([col.in_(ids)] if ids else []) + ([col.is_(None)] if "none" in vals else [])
            if conds:
                q = q.filter(or_(*conds))
    if f.get("remind") == "due":
        q = q.filter(Order.remind_at.isnot(None), Order.remind_at <= utcnow())
    if f.get("ttn") == "none":
        q = q.filter(Order.ttn == "")
    elif f.get("ttn") == "has":
        q = q.filter(Order.ttn != "")
    d1, d2 = parse_date(f.get("date_from")), parse_date(f.get("date_to"))
    if d1 or d2:
        start, end = period_bounds(d1 or d2, d2 or d1)
        q = q.filter(Order.created_at >= start, Order.created_at < end)
    if f.get("delivery"):
        q = q.filter(Order.delivery_method == f["delivery"])
    if f.get("source"):
        q = q.filter(or_(Order.utm_source == f["source"], Order.site == f["source"]))
    if f.get("dup") == "1":
        q = q.filter(Order.duplicate_of_id.is_not(None))
    if f.get("pay"):
        q = q.filter(Order.payment_type == f["pay"])
    return q
