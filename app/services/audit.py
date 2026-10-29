from decimal import Decimal

from sqlalchemy.orm import Session

from ..models import AuditLog, User

ACTION_NAMES = {
    "create": "Створено",
    "update": "Змінено",
    "status": "Статус",
    "items": "Товари",
    "assign": "Менеджер",
    "comment": "Коментар",
    "ttn_create": "Створено ТТН",
    "ttn_delete": "Видалено ТТН",
    "tracking": "Трекінг",
    "payment": "Оплата",
    "sms": "SMS",
    "login": "Вхід",
    "delete": "Видалено",
    "receive": "Оприбутковано",
    "adjust": "Коригування",
}


def _clean(v):
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, dict):
        return {k: _clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_clean(x) for x in v]
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return v


def log(db: Session, user: User | None, entity: str, entity_id: int | None, action: str, details: dict | None = None):
    db.add(
        AuditLog(
            user_id=user.id if user else None,
            entity=entity,
            entity_id=entity_id,
            action=action,
            details=_clean(details) if details else None,
        )
    )


def diff(obj, data: dict, fields: list[str]) -> dict:
    """Застосовує зміни до об'єкта і повертає словник {поле: [було, стало]}."""
    changes = {}
    for f in fields:
        if f not in data:
            continue
        old, new = getattr(obj, f), data[f]
        if isinstance(old, Decimal) or isinstance(new, Decimal):
            if Decimal(str(old or 0)) == Decimal(str(new or 0)):
                continue
        elif (old or "") == (new or "") and type(old) is type(new):
            continue
        elif old == new:
            continue
        changes[f] = [old, new]
        setattr(obj, f, new)
    return changes
