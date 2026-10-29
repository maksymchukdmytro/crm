"""«Перевірка оплати» в ТТН Нової Пошти: чи збігається те, що стоїть у накладній, із видом оплати замовлення.

Вид оплати каже, що має бути в ТТН (`PaymentMethod.np_cod`): контроль оплати (NovaPay), грошовий переказ або
без післяплати. Оплачене повністю замовлення (вид оплати «оплачено») — завжди без післяплати.
Що стоїть у ТТН насправді (`Order.ttn_cod_kind/ttn_cod_sum`) — з відповіді НП при створенні в CRM
або з трекінгу (getStatusDocuments), тож перевіряються й ТТН, створені в кабінеті НП.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from ..models import NP_COD_KINDS, Order

ZERO = Decimal(0)


def _dec(v) -> Decimal:
    try:
        return Decimal(str(v or 0).replace(",", ".")).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return ZERO


def cod_from_np(raw: dict | None) -> tuple[str, Decimal] | None:
    """Що стоїть у ТТН за відповіддю трекінгу НП; None — НП не віддала потрібних полів (чужа ТТН без телефону тощо)."""
    if not raw or not any(k in raw for k in ("AfterpaymentOnGoodsCost", "RedeliverySum", "Redelivery")):
        return None
    control = _dec(raw.get("AfterpaymentOnGoodsCost"))
    if control > 0:
        return "control", control
    backward = _dec(raw.get("RedeliverySum"))
    if str(raw.get("Redelivery") or "0") == "1" and backward > 0:
        return "backward", backward
    return "none", ZERO


def expected(order: Order) -> str:
    """Що має стояти в ТТН: control / backward / none, або "" — не перевіряти."""
    if order.delivery_method != "novaposhta":
        return ""
    m = order.payment_method
    if order.payment_type == "prepaid" or (m is not None and m.kind == "prepaid"):
        return "none"
    return (m.np_cod if m is not None else "") or ""


def _money(v: Decimal) -> str:
    s = f"{v:,.2f}".replace(",", " ").replace(".00", "")
    return f"{s} ₴"


def check(order: Order) -> dict | None:
    """{state: ok | bad | wait, text} або None, якщо для замовлення перевірка не потрібна."""
    need = expected(order)
    if not need:
        return None
    name = NP_COD_KINDS[need]
    if not order.ttn:
        return {"state": "wait", "text": f"ТТН ще немає. Має бути: {name}"}
    kind, have = order.ttn_cod_kind or "", _dec(order.ttn_cod_sum)
    if not kind:
        return {"state": "wait", "text": f"Нова Пошта ще не повернула дані ТТН. Має бути: {name}"}
    amount = _dec(order.cod_amount)
    if need == "none":
        if kind == "none":
            return {"state": "ok", "text": "Оплачено — у ТТН немає післяплати"}
        return {"state": "bad", "text": f"Замовлення оплачене, а в ТТН {NP_COD_KINDS[kind]} {_money(have)}"}
    if kind != need:
        what = NP_COD_KINDS[kind] if kind != "none" else "немає післяплати"
        return {"state": "bad", "text": f"Має бути {name} {_money(amount)}, а в ТТН — {what}"}
    if have != amount:
        return {"state": "bad", "text": f"{name.capitalize()}: у ТТН {_money(have)}, а до сплати {_money(amount)}"}
    return {"state": "ok", "text": f"{name.capitalize()} {_money(have)} — збігається"}
