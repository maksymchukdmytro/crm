"""Налаштування користувача (user_prefs): колонки списків, щільність, згорнута панель, поточний відділ."""
from __future__ import annotations

import json
import re

from sqlalchemy.orm import Session

from ..models import Office, User, UserPref

KEY_RE = re.compile(r"^[a-z0-9_.-]{1,60}$")
MAX_BYTES = 20_000


def all_for(db: Session, user: User) -> dict:
    return {p.key: p.value for p in db.query(UserPref).filter(UserPref.user_id == user.id)}


def get(db: Session, user: User, key: str, default=None):
    p = db.get(UserPref, (user.id, key))
    return default if p is None else p.value


def put(db: Session, user: User, key: str, value) -> None:
    if not KEY_RE.match(key):
        raise ValueError("Невірна назва налаштування")
    if len(json.dumps(value, ensure_ascii=False)) > MAX_BYTES:
        raise ValueError("Завелике значення налаштування")
    p = db.get(UserPref, (user.id, key))
    if value is None:
        if p is not None:
            db.delete(p)
        return
    if p is None:
        db.add(UserPref(user_id=user.id, key=key, value=value))
    else:
        p.value = value


def current_office(db: Session, user: User) -> int | None:
    """Відділ, вибраний у боковій панелі (обмежує списки, лічильники, статистику). None — усі доступні."""
    cached = getattr(user, "_office_pref", "unset")
    if cached != "unset":
        return cached
    v = get(db, user, "office")
    oid = int(v) if isinstance(v, (int, str)) and str(v).isdigit() else None
    if oid is not None:
        allowed = [int(x) for x in (user.offices or [])]
        office = db.get(Office, oid)
        if office is None or not office.is_active or (user.role != "admin" and allowed and oid not in allowed):
            oid = None
    try:
        user._office_pref = oid  # кеш на час запиту (об'єкт користувача живе один запит)
    except AttributeError:
        pass
    return oid
