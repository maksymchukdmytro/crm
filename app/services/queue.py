"""Постановка задач у чергу arq (Redis) з синхронного коду.

Якщо Redis не налаштований або недоступний, enqueue() повертає False —
тоді виклик код виконує роботу сам (одразу в запиті), тож система працює і без черги.
"""
from __future__ import annotations

import asyncio
import logging

from ..config import config

log = logging.getLogger("crm.queue")


async def _enqueue(name: str, args: tuple, job_id: str | None, defer: float | None) -> bool:
    from arq import create_pool
    from arq.connections import RedisSettings

    pool = await create_pool(RedisSettings.from_dsn(config.REDIS_URL), retry=0)
    try:
        kwargs = {}
        if job_id:
            kwargs["_job_id"] = job_id
        if defer:
            kwargs["_defer_by"] = defer
        await pool.enqueue_job(name, *args, **kwargs)
        return True
    finally:
        await pool.aclose()


def available() -> bool:
    return bool(config.REDIS_URL)


def enqueue(name: str, *args, job_id: str | None = None, defer: float | None = None) -> bool:
    if not config.REDIS_URL:
        return False
    try:
        return asyncio.run(_enqueue(name, args, job_id, defer))
    except RuntimeError:
        # уже всередині циклу подій (напр. з async-коду) — виконати в окремому потоці
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(1) as ex:
            return ex.submit(asyncio.run, _enqueue(name, args, job_id, defer)).result()
    except Exception as e:  # noqa: BLE001 — Redis недоступний
        log.warning("Черга недоступна (%s): %s", name, e)
        return False


def kick_sms(db) -> None:
    """Після коміту попросити воркер відправити SMS з черги (кілька змін — одна задача)."""
    from .events import after_commit

    if config.REDIS_URL:
        after_commit(db, "kick_sms", lambda: enqueue("send_sms", job_id="sms:pending", defer=1))
