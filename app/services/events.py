"""Події в реальному часі та дії «після коміту».

Будь-яка зміна замовлення чи товару (з інтерфейсу, API, воркера або webhook)
після успішного коміту публікується в Redis-канал `crm:events`. Сторінки,
підписані на /api/events (SSE), одразу оновлюють дані.

Без Redis (REDIS_URL порожній або сервер недоступний) публікація — тиха no-op.
"""
from __future__ import annotations

import json
import logging
from typing import Callable

import redis
from sqlalchemy import event
from sqlalchemy.orm import Session

from ..config import config

log = logging.getLogger("crm.events")
CHANNEL = "crm:events"
_client: redis.Redis | None = None


def client() -> redis.Redis | None:
    global _client
    if not config.REDIS_URL:
        return None
    if _client is None:
        _client = redis.Redis.from_url(config.REDIS_URL, socket_timeout=2, socket_connect_timeout=2)
    return _client


def publish(kind: str, **data) -> None:
    c = client()
    if c is None:
        return
    try:
        c.publish(CHANNEL, json.dumps({"type": kind, **data}, default=str))
    except redis.RedisError as e:  # подія не критична — запит не має падати
        log.warning("Не вдалося опублікувати подію %s: %s", kind, e)


# ------------------------------------------------------------ дії після коміту
def after_commit(db: Session, key: str, fn: Callable[[], None]) -> None:
    """Виконати fn лише після успішного коміту сесії (однаковий key — один раз)."""
    db.info.setdefault("after_commit", {})[key] = fn


def order_changed(db: Session, order_id: int | None) -> None:
    if order_id:
        after_commit(db, f"order:{order_id}", lambda oid=order_id: publish("order", id=oid))


def product_changed(db: Session, product_id: int | None) -> None:
    if product_id:
        after_commit(db, f"product:{product_id}", lambda pid=product_id: publish("product", id=pid))


@event.listens_for(Session, "after_commit")
def _run_after_commit(session: Session):
    hooks = session.info.pop("after_commit", None)
    if not hooks:
        return
    for fn in hooks.values():
        try:
            fn()
        except Exception:  # noqa: BLE001
            log.exception("Помилка дії після коміту")


@event.listens_for(Session, "after_rollback")
def _drop_after_rollback(session: Session):
    session.info.pop("after_commit", None)
