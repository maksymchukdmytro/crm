"""Налаштування системи зберігаються в таблиці settings (ключ-значення)."""
import secrets

from sqlalchemy.orm import Session

from ..models import Setting

DEFAULTS: dict[str, str] = {
    # Загальні
    "company_name": "Моя CRM",
    "extra1_name": "Поле 1",  # назви додаткових полів замовлення
    "extra2_name": "Поле 2",
    "extra3_name": "Поле 3",
    "extra4_name": "Поле 4",
    "duplicate_days": "14",  # вікно пошуку дублів за телефоном, днів (0 — вимкнено)
    "auto_assign": "off",  # off / round_robin
    "managers_see_own_only": "0",
    "auto_status_from_tracking": "1",  # змінювати статус замовлення за трекінгом
    "tracking_interval_min": "60",
    "low_stock_warning": "1",
    # Прийом заявок
    "webhook_key": "",
    # Нова Пошта
    "np_api_key": "",
    "np_sender_ref": "",
    "np_contact_ref": "",
    "np_sender_phone": "",
    "np_city_ref": "",
    "np_city_name": "",
    "np_warehouse_ref": "",
    "np_warehouse_name": "",
    "np_cod_mode": "backward",  # backward — грошовий переказ, afterpayment — контроль оплати
    "np_payer": "Recipient",  # хто платить за доставку: Recipient / Sender
    "np_default_weight": "0.5",
    "np_seat_size": "20x15x10",  # розміри посилки, см (Д×Ш×В) — для OptionsSeat
    "np_description": "Товар",
    # Укрпошта
    "up_bearer": "",
    "up_token": "",
    "up_tracking_bearer": "",
    "up_sender_uuid": "",
    "up_sandbox": "0",
    "up_type": "STANDARD",
    # Meest
    "meest_username": "",
    "meest_password": "",
    "meest_sender_branch_id": "",
    "meest_sender_name": "",
    "meest_sender_phone": "",
    # SMS (TurboSMS)
    "sms_token": "",
    "sms_sender": "",
    "viber_sender": "",
    "sms_enabled": "0",
    # Моніторинг і сповіщення
    "alert_tg_token": "",
    "alert_tg_chat": "",
    "alert_no_leads_hours": "0",  # 0 — не стежити
    # Службові
    "rr_last_manager_id": "0",
    "alert_state": "",
    "worker_heartbeat": "",
}

SECRET_KEYS = {"np_api_key", "up_bearer", "up_token", "up_tracking_bearer", "meest_password", "sms_token", "alert_tg_token"}
INTERNAL_KEYS = {"rr_last_manager_id", "alert_state", "worker_heartbeat"}


def get_all(db: Session) -> dict[str, str]:
    data = dict(DEFAULTS)
    for s in db.query(Setting).all():
        data[s.key] = s.value or ""
    return data


def get(db: Session, key: str) -> str:
    s = db.get(Setting, key)
    if s is not None:
        return s.value or ""
    return DEFAULTS.get(key, "")


def get_int(db: Session, key: str, default: int = 0) -> int:
    try:
        return int(get(db, key) or default)
    except ValueError:
        return default


def get_bool(db: Session, key: str) -> bool:
    return get(db, key) in ("1", "true", "on", "yes")


def set_value(db: Session, key: str, value: str):
    s = db.get(Setting, key)
    if s is None:
        db.add(Setting(key=key, value=value))
    else:
        s.value = value


def ensure_webhook_key(db: Session) -> str:
    key = get(db, "webhook_key")
    if not key:
        key = secrets.token_urlsafe(24)
        set_value(db, "webhook_key", key)
    return key
