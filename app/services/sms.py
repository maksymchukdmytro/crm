"""SMS та Viber через TurboSMS (https://turbosms.ua/api.html).

Повідомлення спочатку ставляться в чергу (sms_messages), а фоновий воркер
відправляє їх. Так зміна статусу не гальмує, навіть коли сервіс SMS недоступний.
"""
import httpx
from sqlalchemy.orm import Session

from ..models import Order, SmsMessage, SmsTemplate, Status, utcnow
from . import settings as st

TURBOSMS_URL = "https://api.turbosms.ua/message/send.json"

PLACEHOLDERS = {
    "{name}": "ПІБ клієнта",
    "{first_name}": "Ім'я клієнта",
    "{order_id}": "Номер замовлення",
    "{total}": "Сума замовлення",
    "{cod}": "Сума накладеного платежу",
    "{ttn}": "Номер ТТН",
    "{carrier}": "Служба доставки",
    "{city}": "Місто",
    "{warehouse}": "Відділення",
    "{company}": "Назва компанії",
}


def _money(v) -> str:
    try:
        f = float(v or 0)
    except (TypeError, ValueError):
        return str(v)
    return f"{f:.0f}" if f == int(f) else f"{f:.2f}"


def render(text: str, order: Order, company: str = "") -> str:
    values = {
        "{name}": order.customer_name or "",
        "{first_name}": order.first_name,
        "{order_id}": str(order.id),
        "{total}": _money(order.total),
        "{cod}": _money(order.cod_amount),
        "{ttn}": order.ttn or "",
        "{carrier}": order.delivery_method_name,
        "{city}": order.city_name or "",
        "{warehouse}": order.warehouse_name or "",
        "{company}": company,
    }
    for k, v in values.items():
        text = text.replace(k, v)
    return text.strip()


def queue(db: Session, order: Order | None, phone: str, text: str, channel: str = "sms") -> SmsMessage:
    msg = SmsMessage(order_id=order.id if order else None, phone=phone, text=text, channel=channel)
    db.add(msg)
    return msg


def queue_for_status(db: Session, order: Order, status: Status):
    if not st.get_bool(db, "sms_enabled") or not order.phone:
        return
    templates = (
        db.query(SmsTemplate)
        .filter(SmsTemplate.status_id == status.id, SmsTemplate.is_active.is_(True))
        .all()
    )
    company = st.get(db, "company_name")
    for t in templates:
        text = render(t.text, order, company)
        if text:
            queue(db, order, order.phone, text, t.channel)


def send_turbosms(token: str, phone: str, text: str, channel: str, sms_sender: str, viber_sender: str,
                  client: httpx.Client | None = None) -> tuple[bool, str]:
    body: dict = {"recipients": [phone]}
    if channel in ("sms", "hybrid"):
        body["sms"] = {"sender": sms_sender, "text": text}
    if channel in ("viber", "hybrid"):
        body["viber"] = {"sender": viber_sender, "text": text}
    own = client is None
    client = client or httpx.Client(timeout=20)
    try:
        r = client.post(TURBOSMS_URL, json=body, headers={"Authorization": f"Bearer {token}"})
        data = r.json()
    except (httpx.HTTPError, ValueError) as e:
        return False, f"Помилка з'єднання: {e}"[:250]
    finally:
        if own:
            client.close()
    result = data.get("response_result") or data.get("result") or []
    if isinstance(result, list) and result:
        first = result[0] or {}
        if first.get("message_id"):
            return True, str(first["message_id"])
        return False, str(first.get("response_status") or data.get("response_status") or "Помилка")[:250]
    code = data.get("response_code")
    if code in (800, 801, 802, 803):
        return True, ""
    return False, str(data.get("response_status") or data)[:250]


def send_pending(db: Session, limit: int = 50, client: httpx.Client | None = None) -> int:
    """Відправляє повідомлення з черги. Повертає кількість успішно відправлених."""
    token = st.get(db, "sms_token")
    if not token:
        return 0
    sms_sender, viber_sender = st.get(db, "sms_sender"), st.get(db, "viber_sender")
    msgs = (
        db.query(SmsMessage)
        .filter(SmsMessage.status == "queued", SmsMessage.attempts < 3)
        .order_by(SmsMessage.id)
        .limit(limit)
        .all()
    )
    sent = 0
    for m in msgs:
        m.attempts += 1
        ok, info = send_turbosms(token, m.phone, m.text, m.channel, sms_sender, viber_sender, client)
        if ok:
            m.status, m.provider_id, m.sent_at, m.error = "sent", info, utcnow(), ""
            sent += 1
        else:
            m.error = info
            if m.attempts >= 3:
                m.status = "failed"
        db.commit()
    return sent
