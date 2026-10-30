"""Налаштування системи зберігаються в таблиці settings (ключ-значення)."""
import secrets

from sqlalchemy.orm import Session

from ..models import Setting

WARRANTY_TERMS = """Гарантійний строк — {months} міс. від дати продажу, якщо в таблиці для товару не вказано інший.
Протягом гарантійного строку продавець безоплатно усуває недоліки, що виникли з вини виробника, або замінює товар відповідно до Закону України «Про захист прав споживачів».
Для гарантійного обслуговування потрібні цей талон (або інший документ про купівлю: чек, видаткова накладна) і товар у повній комплектації.
Гарантія не поширюється на: механічні пошкодження, сліди удару чи падіння; потрапляння рідини, пилу, комах; порушення правил експлуатації, зберігання чи транспортування з інструкції; ремонт або розкриття особами, не уповноваженими продавцем; пошкодження від перепадів напруги, неоригінальних зарядних пристроїв чи аксесуарів; природний знос витратних частин (акумулятори, кабелі, чохли тощо).
Гарантійний строк продовжується на час, протягом якого товар перебував на ремонті.
Товар належної якості можна повернути або обміняти протягом 14 днів з дня покупки, якщо він не був у вжитку і збережено товарний вигляд, комплектність, пломби, ярлики та документ про купівлю (ст. 9 Закону «Про захист прав споживачів»), крім товарів з переліку, що не підлягають обміну.
Пересилання товару на гарантійне обслуговування — за рахунок продавця, якщо недолік гарантійний; якщо ні — за рахунок покупця."""

DEFAULTS: dict[str, str] = {
    # Загальні
    "company_name": "Моя CRM",
    # Документи (видаткова накладна, рахунок-фактура, гарантійний талон)
    "doc_prefix": "РН-", "invoice_prefix": "СФ-", "warranty_prefix": "ГТ-", "doc_unit": "шт.", "doc_accent": "#C1D0E4",
    "doc_site": "", "doc_note": "Дякуємо за покупку!", "doc_logo": "", "invoice_days": "3", "warranty_months": "12",
    "warranty_terms": WARRANTY_TERMS,
    "extra1_on": "1", "extra2_on": "1", "extra3_on": "1", "extra4_on": "1",  # які з полів 1–4 показувати
    "extra1_name": "Поле 1",  # назви додаткових полів замовлення
    "extra2_name": "Поле 2",
    "extra3_name": "Поле 3",
    "extra4_name": "Поле 4",
    "duplicate_days": "14",  # вікно пошуку дублів за телефоном, днів (0 — вимкнено)
    "auto_assign": "off",  # off / round_robin
    # розділ «Ліди» (UI-DESIGN §4.3): вимкнено — заявки з форм ідуть одразу в «Несортовані»
    "leads_enabled": "1",
    "lead_wait_warn_min": "5",
    "lead_wait_bad_min": "15",
    "lead_noanswer_remind_min": "30",
    "lead_to_order_status": "confirmed",  # confirmed / unsorted
    "doc_auto_issue": "shipped",  # коли видавати видаткову й гарантійний: shipped / print / off
    "doc_in_parcel": "0",  # «Накладну в посилку надруковано» в «Що лишилось»
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
    # Checkbox: у якому статусі замовлення автоматично створювати чек (id статусу, порожньо — вручну)
    "cb_sell_status": "",
    "cb_return_status": "",
    "cb_prepay_status": "",
    "cb_postpay_status": "",
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
