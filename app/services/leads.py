"""Ліди (UI-DESIGN §4.3): вкладки, час очікування, черга дзвінків, результат дзвінка, створення замовлення, вимкнення розділу."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from ..models import Order, Status, User, utcnow
from . import audit, events
from . import orders as svc
from . import settings as st

OPEN_CODES = ("new", "no_answer", "callback")
TABS = {  # вкладка → коди статусів (None — особлива умова)
    "open": OPEN_CODES, "new": ("new",), "no_answer": ("no_answer",), "callback": ("callback",),
    "duplicate": ("duplicate",), "refused": ("lead_refused",), "converted": None, "all": None,
}


class LeadError(ValueError):
    pass


def enabled(db: Session) -> bool:
    return st.get(db, "leads_enabled") != "0"


def _ids(db: Session, codes) -> list[int]:
    return [i for (i,) in db.query(Status.id).filter(Status.code.in_(codes))]


def apply_tab(db: Session, q, tab: str):
    if tab == "converted":
        return q.filter(Order.converted_at.isnot(None))
    if tab == "all":
        return q.filter(or_(Order.status.has(Status.stage == "lead"), Order.converted_at.isnot(None)))
    return q.filter(Order.status_id.in_(_ids(db, TABS.get(tab) or OPEN_CODES)))


def tab_counts(db: Session, base) -> dict[str, int]:
    by_status = dict(base.with_entities(Order.status_id, func.count(Order.id)).group_by(Order.status_id).all())
    codes = {s.id: s.code for s in db.query(Status)}
    by_code: dict[str, int] = {}
    for sid, n in by_status.items():
        by_code[codes.get(sid, "")] = by_code.get(codes.get(sid, ""), 0) + n
    out = {t: sum(by_code.get(c, 0) for c in cs) for t, cs in TABS.items() if cs}
    out["converted"] = base.filter(Order.converted_at.isnot(None)).count()
    lead_ids = [s.id for s in db.query(Status).filter(Status.stage == "lead")]
    out["all"] = sum(n for sid, n in by_status.items() if sid in lead_ids) + out["converted"]
    return out


def wait_since(o: Order, now: datetime | None = None) -> datetime | None:
    """Від чого рахуємо очікування: від нагадування (передзвонити / після недодзвону), якщо його час настав, інакше від створення."""
    now = now or utcnow()
    if o.remind_at and o.remind_at <= now:
        return o.remind_at
    return o.created_at


def wait_minutes(o: Order, now: datetime | None = None) -> int | None:
    now = now or utcnow()
    if o.status is None or o.status.code not in OPEN_CODES:
        return None
    if o.remind_at and o.remind_at > now:
        return None  # чекає свого часу (передзвонити о …)
    ws = wait_since(o, now)
    return max(0, int((now - ws).total_seconds() // 60)) if ws else None


def wait_order(db: Session):
    """Сортування «хто чекає найдовше»: спершу ті, чий час настав, від найдовшого очікування; майбутні передзвони — унизу за часом."""
    now = utcnow()
    future = case((Order.remind_at > now, 1), else_=0)
    since = case((Order.remind_at <= now, Order.remind_at), else_=Order.created_at)
    return [future.asc(), case((Order.remind_at > now, Order.remind_at), else_=since).asc(), Order.id.asc()]


def queue(db: Session, user: User, flt: str = "all") -> list[int]:
    codes = {"new": ("new",), "callback": ("callback",)}.get(flt, OPEN_CODES)
    now = utcnow()
    q = (svc.visible_orders_query(db, user).filter(Order.status_id.in_(_ids(db, codes)))
         .filter(or_(Order.remind_at.is_(None), Order.remind_at <= now)))
    return [i for (i,) in q.with_entities(Order.id).order_by(*wait_order(db)).limit(500)]


def _status(db: Session, code: str) -> Status:
    s = svc.status_by_code(db, code)
    if s is None:
        raise LeadError(f"Немає статусу «{code}»")
    return s


def apply_result(db: Session, order: Order, user: User, result: str, at: datetime | None = None,
                 reason_id: int | None = None, duplicate_of_id: int | None = None, note: str = "") -> None:
    now = utcnow()
    if result == "no_answer":
        svc.change_status(db, order, _status(db, "no_answer"), user)
        order.call_attempts = (order.call_attempts or 0) + 1
        order.last_call_at = now
        order.remind_at = now + timedelta(minutes=st.get_int(db, "lead_noanswer_remind_min", 30) or 30)
    elif result == "callback":
        when = at or now + timedelta(minutes=st.get_int(db, "lead_noanswer_remind_min", 30) or 30)
        svc.change_status(db, order, _status(db, "callback"), user)
        order.call_attempts = (order.call_attempts or 0) + 1
        order.last_call_at = now
        order.remind_at = when
    elif result == "refused":
        from ..models import StatusReason
        has_reasons = db.query(StatusReason.id).filter(StatusReason.is_active.is_(True)).first() is not None
        if has_reasons and not reason_id:
            raise LeadError("Вкажіть причину відмови")
        if reason_id:
            order.reason_id = reason_id
        svc.change_status(db, order, svc.status_by_code(db, "lead_refused") or _status(db, "cancelled"), user)
        order.remind_at = None
    elif result == "duplicate":
        if duplicate_of_id:
            if duplicate_of_id == order.id or db.get(Order, duplicate_of_id) is None:
                raise LeadError("Перший лід чи замовлення не знайдено")
            order.duplicate_of_id = duplicate_of_id
        svc.change_status(db, order, _status(db, "duplicate"), user)
        order.remind_at = None
    else:
        raise LeadError("Невідомий результат дзвінка")
    if note:
        svc.add_comment(db, order, note, user)
    order.updated_at = now
    events.order_changed(db, order.id)


def convert(db: Session, order: Order, user: User) -> None:
    """«Створити замовлення» з ліда: перевірка товару, доставки й оплати; статус — з налаштування lead_to_order_status."""
    missing = []
    if not order.items:
        missing.append("товар")
    if not order.delivery_method or (order.delivery_method not in ("pickup",) and not (order.city_name or order.address or order.ttn)):
        missing.append("доставку")
    if not order.payment_method_id:
        missing.append("вид оплати")
    if missing:
        raise LeadError("Щоб створити замовлення, додайте " + ", ".join(missing))
    code = st.get(db, "lead_to_order_status") or "confirmed"
    target = svc.status_by_code(db, code) or _status(db, "confirmed")
    svc.change_status(db, order, target, user)
    order.converted_at = utcnow()
    order.remind_at = None
    audit.log(db, user, "order", order.id, "lead_convert", {"статус": target.name})
    events.order_changed(db, order.id)


def open_leads(db: Session):
    return db.query(Order).filter(Order.status_id.in_(_ids(db, OPEN_CODES)))


def disable(db: Session, user: User, move_open: bool) -> int:
    """Вимкнути розділ «Ліди». move_open — перенести відкриті ліди в «Несортовані» (із записом у журнал)."""
    moved = 0
    if move_open:
        target = _status(db, "unsorted")
        for o in open_leads(db).all():
            svc.change_status(db, o, target, user, reason="розділ «Ліди» вимкнено")
            o.remind_at = None
            moved += 1
    st.set_value(db, "leads_enabled", "0")
    audit.log(db, user, "settings", None, "leads_disable", {"перенесено": moved})
    return moved
