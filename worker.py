"""Фоновий воркер: відправка SMS з черги і оновлення статусів посилок.

Запуск: python worker.py (у Docker — окремий контейнер `worker`).
"""
import logging
import signal
import time

from app import db as dbmod
from app.config import config
from app.services import delivery, sms

logging.basicConfig(level=logging.INFO, format="%(asctime)s worker %(levelname)s %(message)s")
log = logging.getLogger("worker")
_running = True


def _stop(*_):
    global _running
    _running = False


def tick():
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
            stats = delivery.sync_tracking(db)
            if stats["checked"]:
                log.info("Трекінг: перевірено %s, змінено %s", stats["checked"], stats["changed"])
            for e in stats["errors"]:
                log.warning("Трекінг: %s", e)
        except Exception:  # noqa: BLE001
            db.rollback()
            log.exception("Помилка оновлення трекінгу")


def main():
    dbmod.init_engine()
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    log.info("Воркер запущено, інтервал %s с", config.WORKER_TICK)
    while _running:
        tick()
        for _ in range(config.WORKER_TICK):
            if not _running:
                break
            time.sleep(1)


if __name__ == "__main__":
    main()
