"""Нова Пошта: акаунти (ключі ФОП), вибір ключа для замовлення, правила статусів ТТН."""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import NpAccount, NpStatusRule, Order
from . import settings as st

# Статуси ТТН Нової Пошти (код getStatusDocuments → назва), як у списку правил LP-CRM
NP_STATUSES = {
    "1": "Відправник самостійно створив накладну, але ще не надав до відправки",
    "2": "Видалено",
    "3": "Номер не знайдено",
    "4": "Відправлення у місті відправника",
    "41": "Відправлення у місті відправника (міжобласна доставка)",
    "5": "Відправлення прямує до міста одержувача",
    "6": "Відправлення у місті одержувача, очікуйте повідомлення про прибуття",
    "7": "Прибув на відділення",
    "8": "Прибув на відділення (завантажено в поштомат)",
    "9": "Відправлення отримано",
    "10": "Відправлення отримано, грошовий переказ надійде протягом доби",
    "11": "Відправлення отримано. Грошовий переказ видано одержувачу",
    "14": "Відправлення передано до огляду одержувачу",
    "101": "На шляху до одержувача",
    "102": "Відмова від отримання (створено повернення)",
    "103": "Відмова одержувача",
    "104": "Змінено адресу",
    "105": "Припинено зберігання",
    "106": "Одержано і створено ЄН зворотної доставки",
    "111": "Невдала спроба доставки (немає одержувача на адресі)",
    "112": "Дата доставки перенесена одержувачем",
}

# поля акаунта → ключі налаштувань, які читає перевізник NovaPoshta
_MAP = {
    "api_key": "np_api_key", "sender_ref": "np_sender_ref", "contact_ref": "np_contact_ref",
    "sender_phone": "np_sender_phone", "city_ref": "np_city_ref", "city_name": "np_city_name",
    "warehouse_ref": "np_warehouse_ref", "warehouse_name": "np_warehouse_name", "payer": "np_payer",
    "cargo_type": "np_cargo_type", "service_type": "np_service_type", "cod_mode": "np_cod_mode",
    "cod_payer": "np_cod_payer", "seat_size": "np_seat_size", "description": "np_description",
}


def account_settings(base: dict[str, str], acc: NpAccount | None) -> dict[str, str]:
    """Налаштування для перевізника: загальні + параметри вибраного ключа НП."""
    s = dict(base)
    if acc is None:
        return s
    for field, key in _MAP.items():
        s[key] = str(getattr(acc, field) or "")
    s["np_default_weight"] = str(acc.default_weight or "0.5")
    for flag in ("info_comment", "info_items", "info_item_ids"):
        s[f"np_{flag}"] = "1" if getattr(acc, flag) else "0"
    s["np_account_id"] = str(acc.id)
    return s


def accounts(db: Session, active_only: bool = True) -> list[NpAccount]:
    q = db.query(NpAccount)
    if active_only:
        q = q.filter(NpAccount.is_active.is_(True))
    return q.order_by(NpAccount.is_default.desc(), NpAccount.id).all()


def pick_account(db: Session, order: Order | None = None) -> NpAccount | None:
    """Ключ для замовлення: вибраний у замовленні → юрособи замовлення → закріплений за відділом → основний."""
    if order is not None and order.np_account_id:
        acc = db.get(NpAccount, order.np_account_id)
        if acc is not None:
            return acc
    accs = accounts(db)
    if order is not None:
        from .checkbox import order_entity
        entity = order_entity(db, order)
        if entity is not None:
            for a in accs:
                if a.legal_entity_id == entity.id:
                    return a
    if order is not None and order.office_id:
        for a in accs:
            if a.office_id == order.office_id:
                return a
    return accs[0] if accs else None


def carrier_settings(db: Session, order: Order | None = None) -> dict[str, str]:
    base = st.get_all(db)
    if order is None or order.delivery_method == "novaposhta":
        return account_settings(base, pick_account(db, order))
    return base


def rules(db: Session) -> list[NpStatusRule]:
    return db.query(NpStatusRule).order_by(NpStatusRule.sort, NpStatusRule.id).all()


def add_to_registry(db: Session, orders: list[Order], user=None) -> dict:
    """Реєстр НП (ScanSheet): ТТН одного ключа за день потрапляють в один реєстр. Номер реєстру — у orders.np_registry_ref.
    → {"done": n, "errors": [...], "registries": {account_id: number}}"""
    from datetime import date as _date
    from . import audit, events
    from .delivery import carrier_for
    out = {"done": 0, "errors": [], "registries": {}}
    by_acc: dict[int, list[Order]] = {}
    for o in orders:
        if o.delivery_method != "novaposhta" or not o.ttn:
            out["errors"].append(f"№{o.id}: немає ТТН Нової Пошти")
            continue
        if o.np_registry_ref:
            continue
        if not o.carrier_ref:
            out["errors"].append(f"№{o.id}: ТТН створена не через CRM — додайте в реєстр у кабінеті НП")
            continue
        acc = pick_account(db, o)
        by_acc.setdefault(acc.id if acc else 0, []).append(o)
    today = _date.today().isoformat()
    for acc_id, items in by_acc.items():
        carrier = carrier_for(db, items[0])
        key = f"np_registry_{acc_id}_{today}"
        saved = st.get(db, key)  # «ref|number» реєстру цього ключа на сьогодні
        ref, number = (saved.split("|", 1) + [""])[:2] if saved else ("", "")
        try:
            r = carrier.registry_add([o.carrier_ref for o in items], ref)
        except Exception as e:  # noqa: BLE001 — помилка НП не ламає інші ключі
            out["errors"].append(f"Реєстр НП: {e}")
            continue
        ref, number = r["ref"] or ref, r["number"] or number
        if ref:
            st.set_value(db, key, f"{ref}|{number}")
        out["errors"] += r["errors"]
        for o in items:
            o.np_registry_ref = number or ref[:40]
            audit.log(db, user, "order", o.id, "registry", {"реєстр": o.np_registry_ref})
            events.order_changed(db, o.id)
            out["done"] += 1
        out["registries"][acc_id] = number or ref
    return out
