"""Фоновий воркер CRM.

З Redis (REDIS_URL задано) — черга задач arq (app/tasks.py): SMS, ТТН, трекінг паралельно по перевізниках.
Без Redis — запасний простий цикл: раз на WORKER_TICK секунд SMS і трекінг.

Запуск: python worker.py (у Docker/systemd — окрема служба).
"""
import logging
import signal
import time

from app import db as dbmod
from app.config import config
from app.services import delivery, monitoring, sms

logging.basicConfig(level=logging.INFO, format="%(asctime)s worker %(levelname)s %(message)s")
log = logging.getLogger("worker")
_running = True


def _stop(*_):
    global _running
    _running = False


def tick():
    with dbmod.SessionLocal() as db:
        try:
            monitoring.beat(db)
            monitoring.run_alerts(db)
        except Exception:  # noqa: BLE001
            db.rollback()
            log.exception("Помилка моніторингу")
    with dbmod.SessionLocal() as db:
        try:
            sent = sms.send_pending(db)
            if sent:
                log.info("SMS відправлено: %s", sent)
        except Exception:  # noqa: BLE001 — воркер не повинен падати
            db.rollback()
            log.exception("Помилка відправки SMS")
    with dbmod.SessionLocal() as db:
        try:
            from app.services import marketplaces
            for sid, st_ in marketplaces.sync_all(db).items():
                if st_["new"] or st_["error"]:
                    log.info("Маркетплейс %s: нових %s, помилка: %s", sid, st_["new"], st_["error"] or "—")
        except Exception:  # noqa: BLE001
            db.rollback()
            log.exception("Помилка синхронізації маркетплейсів")
    with dbmod.SessionLocal() as db:
        try:
            stats = delivery.sync_tracking(db)
            if stats["checked"]:
                log.info("Трекінг: перевірено %s, змінено %s", stats["checked"], stats["changed"])
            for e in stats["errors"]:
                log.warning("Трекінг: %s", e)
        except Exception:  # noqa: BLE001
            db.rollback()
            log.exception("Помилка оновлення трекінгу")


def legacy_loop():
    dbmod.init_engine()
    monitoring.init_sentry("worker")
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    log.info("Воркер без Redis (простий цикл), інтервал %s с", config.WORKER_TICK)
    while _running:
        tick()
        for _ in range(config.WORKER_TICK):
            if not _running:
                break
            time.sleep(1)


def main():
    if config.REDIS_URL:
        from arq.worker import run_worker

        from app.tasks import WorkerSettings

        run_worker(WorkerSettings)
    else:
        legacy_loop()


if __name__ == "__main__":
    main()
