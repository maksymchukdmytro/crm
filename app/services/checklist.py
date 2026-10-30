"""«Що лишилось» (UI-DESIGN §5.5): кроки, яких бракує саме цьому замовленню. Показуються лише ті, що стосуються замовлення,
і самі відмічаються, коли зроблені. action — що виконати по кліку на невиконаному кроці."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from ..models import CheckboxReceipt, Order, SmsMessage, SmsTemplate
from . import settings as st

PRE_ACCEPT = {"unsorted", "new", "no_answer", "callback", "duplicate", "lead_refused", "cancelled"}
AFTER_SHIP = {"shipped", "arrived", "delivered", "refused", "returned"}


def _item(key, label, done, hint="", action="", error=False):
    return {"key": key, "label": label, "state": "error" if error and not done else ("done" if done else "pending"),
            "hint": hint, "action": "" if done else action}


def build(db: Session, order: Order) -> list[dict]:
    code = order.status.code if order.status else ""
    if code in PRE_ACCEPT or not order.status:
        return []
    receipts = db.query(CheckboxReceipt).filter(CheckboxReceipt.order_id == order.id).all()
    done_kinds = {r.kind for r in receipts if r.status == "done"}
    method = order.payment_method
    kind = method.kind if method else order.payment_type
    has_prepay = kind in ("partial", "prepaid") or Decimal(order.prepayment or 0) > 0
    carrier = order.delivery_method not in ("pickup", "")
    try:
        from .checkbox import pick_cashier
        cashier = pick_cashier(db, order) is not None
    except Exception:  # noqa: BLE001
        cashier = False

    if code in AFTER_SHIP:  # після відправки — три пункти, їх відмічає трекінг
        cod = Decimal(order.cod_amount or 0) > 0
        got = code == "delivered" or order.delivery_state == "delivered"
        money_done = got and (not cod or any(p.kind == "cod" and p.status == "received" for p in order.payments))
        out = [_item("received", "Покупець забрав", got), _item("money", "Гроші надійшли", money_done)]
        if cashier and cod:
            out.append(_item("cod_receipt", "Чек післяплати пробито", "postpay" in done_kinds or "sell" in done_kinds, action="cod_receipt"))
        return out

    out = []
    short = order.status.stock_action in ("reserve", "ship") and not order.stock_reserved and not order.stock_shipped
    out.append(_item("reserve", "Товар зарезервовано", order.stock_reserved or order.stock_shipped,
                     hint="не вистачає на складі" if short else "", error=short))
    if has_prepay:
        received = sum((p.amount for p in order.payments if p.kind == "prepayment" and p.status == "received"), Decimal(0))
        need = Decimal(order.prepayment or 0) if kind == "partial" else Decimal(order.total or 0)
        out.append(_item("prepay", "Передоплата надійшла", received > 0 and received >= need > 0 or (received > 0 and need == 0), action="prepay_confirm"))
        if cashier:
            out.append(_item("prepay_receipt", "Чек на передоплату", "prepay" in done_kinds or "sell" in done_kinds, action="prepay_receipt"))
    if carrier:
        out.append(_item("ttn", "ТТН створено", bool(order.ttn), action="ttn"))
    if order.ttn:
        out.append(_item("label", "Наклейку надруковано", order.label_printed_at is not None, action="label"))
    if st.get(db, "doc_in_parcel") == "1":
        out.append(_item("waybill", "Накладну в посилку надруковано", _waybill_printed(db, order), action="waybill"))
    if order.ttn and order.delivery_method == "novaposhta":
        out.append(_item("registry", "У реєстрі НП", bool(order.np_registry_ref), action="registry"))
    if order.ttn and _ttn_template(db):
        sent = db.query(SmsMessage.id).filter(SmsMessage.order_id == order.id, SmsMessage.text.contains(order.ttn)).first() is not None
        out.append(_item("sms_ttn", "SMS з ТТН надіслано", sent, action="sms_ttn"))
    return out


def _ttn_template(db: Session) -> SmsTemplate | None:
    if not st.get(db, "sms_token"):
        return None
    return db.query(SmsTemplate).filter(SmsTemplate.is_active.is_(True), SmsTemplate.text.contains("{ttn}")).first()


def _waybill_printed(db: Session, order: Order) -> bool:
    try:
        from ..models import IssuedDocument  # з'явиться в кроці 6 (видаткові накладні)
    except ImportError:
        return False
    return db.query(IssuedDocument.id).filter(IssuedDocument.order_id == order.id, IssuedDocument.kind == "waybill",
                                               IssuedDocument.print_count > 0).first() is not None


def sms_ttn_text(db: Session) -> tuple[str, str]:
    t = _ttn_template(db)
    return (t.text, t.channel) if t else ("", "sms")
