"""Фонові задачі на arq (Redis).

Запуск воркера:  arq app.tasks.WorkerSettings   (або python worker.py — сам обере arq чи запасний цикл)

Задачі:
  send_sms            відправити повідомлення з черги (ставиться після кожного нового SMS)
  create_ttn          створити ТТН для замовлення (масове створення не блокує інтерфейс)
  track_carrier       оновити статуси посилок одного перевізника
  track_all  (cron)   раз на 5 хв ставить track_carrier для кожного налаштованого перевізника
  sweep_sms  (cron)   раз на хвилину — підстраховка, якщо задачу send_sms не вдалося поставити
Синхронна робота з базою виконується в окремому потоці (asyncio.to_thread).
"""
from __future__ import annotations

import asyncio
import logging

from arq import cron, func
from arq.connections import RedisSettings

from . import db as dbmod
from .carriers import CARRIERS, CarrierError, get_carrier
from .config import config
from .models import Order, User
from .services import delivery, events, monitoring, sms
from .services import settings as st

log = logging.getLogger("crm.tasks")


def _sms_job() -> int:
    with dbmod.SessionLocal() as db:
        return sms.send_pending(db)


def _ttn_job(order_id: int, user_id: int | None) -> dict:
    with dbmod.SessionLocal() as db:
        order = db.get(Order, order_id)
        user = db.get(User, user_id) if user_id else None
        if order is None or order.ttn:
            return {"order_id": order_id, "skipped": True}
        try:
            ttn = delivery.create_ttn(db, order, user)
            db.commit()
            return {"order_id": order_id, "ttn": ttn}
        except CarrierError as e:
            db.rollback()
            events.publish("toast", kind="error", user_id=user_id, text=f"№{order_id}: {e}")
            return {"order_id": order_id, "error": str(e)}


def _track_job(carrier: str) -> dict:
    with dbmod.SessionLocal() as db:
        stats = delivery.sync_tracking(db, carrier=carrier)
    monitoring.save_track_stats(carrier, stats)
    return stats


def _alerts_job() -> dict:
    with dbmod.SessionLocal() as db:
        return monitoring.run_alerts(db)


def _configured_carriers() -> list[str]:
    with dbmod.SessionLocal() as db:
        s = st.get_all(db)
    return [code for code in CARRIERS if get_carrier(code, s).configured()]


async def send_sms(ctx) -> int:
    sent = await asyncio.to_thread(_sms_job)
    if sent:
        log.info("SMS відправлено: %s", sent)
    return sent


async def create_ttn(ctx, order_id: int, user_id: int | None = None) -> dict:
    return await asyncio.to_thread(_ttn_job, order_id, user_id)


async def track_carrier(ctx, carrier: str) -> dict:
    stats = await asyncio.to_thread(_track_job, carrier)
    if stats["checked"]:
        log.info("Трекінг %s: перевірено %s, змінено %s", carrier, stats["checked"], stats["changed"])
    for e in stats["errors"]:
        log.warning("Трекінг %s: %s", carrier, e)
    return stats


async def track_all(ctx) -> None:
    for code in await asyncio.to_thread(_configured_carriers):
        # однаковий _job_id: поки попередня перевірка цього перевізника не завершилась, нова не ставиться
        await ctx["redis"].enqueue_job("track_carrier", code, _job_id=f"track:{code}")


async def sweep_sms(ctx) -> None:
    await ctx["redis"].enqueue_job("send_sms", _job_id="sms:pending")


async def heartbeat(ctx) -> None:
    await asyncio.to_thread(monitoring.beat)


async def alerts(ctx) -> None:
    res = await asyncio.to_thread(_alerts_job)
    if res["opened"] or res["resolved"]:
        log.info("Сповіщення: нові %s, відновлено %s", res["opened"], res["resolved"])


async def startup(ctx) -> None:
    dbmod.init_engine()
    monitoring.init_sentry("worker")
    monitoring.beat()
    log.info("Воркер arq запущено")


class WorkerSettings:
    functions = [
        func(send_sms, keep_result=0, max_tries=3),
        func(create_ttn, keep_result=600, max_tries=1, timeout=90),
        func(track_carrier, keep_result=0, max_tries=1, timeout=600),
    ]
    cron_jobs = [
        cron(track_all, minute=set(range(0, 60, 5)), run_at_startup=True),
        cron(sweep_sms, second={10}),
        cron(heartbeat, second={0, 30}),
        cron(alerts, second={40}),
    ]
    on_startup = startup
    max_jobs = 10
    redis_settings = RedisSettings.from_dsn(config.REDIS_URL or "redis://localhost:6379/0")
