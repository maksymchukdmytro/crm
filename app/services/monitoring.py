"""Моніторинг: Sentry, метрики Prometheus, пульс воркера, стан системи і сповіщення в Telegram.

Усе вмикається налаштуваннями й без них нічого не ламає:
  SENTRY_DSN            — помилки й повільні запити у Sentry (web і воркер)
  METRICS_TOKEN         — /api/metrics для Prometheus / Grafana
  Налаштування → Система — Telegram-бот для сповіщень і поріг «немає заявок N год»
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import httpx
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from ..config import config
from ..models import Order, SmsMessage, utcnow
from . import settings as st

log = logging.getLogger("crm.monitoring")
ROOT = Path(__file__).resolve().parent.parent.parent
HEARTBEAT_KEY = "crm:worker:heartbeat"
TRACK_KEY = "crm:track:"  # + код перевізника
WORKER_STALE = 180  # секунд без пульсу — воркер вважається зупиненим


def version() -> str:
    f = ROOT / "VERSION"
    return f.read_text().strip() if f.exists() else "dev"


# ---------------------------------------------------------------- Sentry
def init_sentry(component: str) -> bool:
    if not config.SENTRY_DSN:
        return False
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    integrations = [SqlalchemyIntegration(), LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)]
    if component == "worker":
        from sentry_sdk.integrations.arq import ArqIntegration
        integrations.append(ArqIntegration())
    else:
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
        integrations += [StarletteIntegration(), FastApiIntegration()]
    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        environment=config.SENTRY_ENV,
        release=f"crm@{version().split(' ')[0]}",
        traces_sample_rate=config.SENTRY_TRACES_RATE,
        send_default_pii=False,  # телефони й імена клієнтів у Sentry не надсилаємо
        integrations=integrations,
    )
    sentry_sdk.set_tag("component", component)
    return True


# ---------------------------------------------------------------- Redis-помічники
def _redis():
    from .events import client
    return client()


def beat(db: Session | None = None) -> None:
    """Пульс воркера: Redis (якщо є) або таблиця налаштувань."""
    now = utcnow().isoformat()
    r = _redis()
    if r is not None:
        try:
            r.set(HEARTBEAT_KEY, now, ex=WORKER_STALE * 2)
            return
        except Exception as e:  # noqa: BLE001
            log.warning("Пульс у Redis не записано: %s", e)
    if db is not None:
        st.set_value(db, "worker_heartbeat", now)
        db.commit()


def worker_seen_at(db: Session) -> datetime | None:
    raw = None
    r = _redis()
    if r is not None:
        try:
            raw = r.get(HEARTBEAT_KEY)
            raw = raw.decode() if isinstance(raw, bytes) else raw
        except Exception:  # noqa: BLE001
            raw = None
    raw = raw or st.get(db, "worker_heartbeat")
    try:
        return datetime.fromisoformat(raw) if raw else None
    except ValueError:
        return None


def save_track_stats(carrier: str, stats: dict) -> None:
    r = _redis()
    if r is None:
        return
    key = TRACK_KEY + carrier
    try:
        prev = json.loads(r.get(key) or "{}")
        fails = (prev.get("consecutive_errors", 0) + 1) if stats.get("errors") else 0
        r.set(key, json.dumps({"at": utcnow().isoformat(), "checked": stats.get("checked", 0),
                               "changed": stats.get("changed", 0), "errors": stats.get("errors", [])[:3],
                               "consecutive_errors": fails}, ensure_ascii=False), ex=86400)
    except Exception as e:  # noqa: BLE001
        log.warning("Статистику трекінгу не збережено: %s", e)


def track_stats() -> dict:
    from ..carriers import CARRIERS
    r = _redis()
    out = {}
    if r is None:
        return out
    for code in CARRIERS:
        try:
            raw = r.get(TRACK_KEY + code)
            if raw:
                out[code] = json.loads(raw)
        except Exception:  # noqa: BLE001
            pass
    return out


def queue_length() -> int | None:
    r = _redis()
    if r is None:
        return None
    try:
        return int(r.zcard("arq:queue"))
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------- перевірки
def checks(db: Session) -> dict[str, dict]:
    res: dict[str, dict] = {}
    try:
        db.execute(text("SELECT 1"))
        res["database"] = {"ok": True, "detail": "PostgreSQL відповідає"}
    except Exception as e:  # noqa: BLE001
        res["database"] = {"ok": False, "detail": str(e)[:200]}
    if config.REDIS_URL:
        try:
            _redis().ping()
            res["redis"] = {"ok": True, "detail": "черга й події працюють"}
        except Exception as e:  # noqa: BLE001
            res["redis"] = {"ok": False, "detail": f"недоступний: {e}"[:200]}
    else:
        res["redis"] = {"ok": True, "detail": "не налаштований — задачі виконуються одразу, інтерфейс оновлюється раз на 30 с"}
    seen = worker_seen_at(db)
    age = (utcnow() - seen).total_seconds() if seen else None
    res["worker"] = {"ok": age is not None and age < WORKER_STALE,
                     "detail": f"останній пульс {int(age)} с тому" if age is not None else "ще не запускався"}
    return res


def system_status(db: Session) -> dict:
    day_start = utcnow() - timedelta(hours=24)
    sms = dict(db.query(SmsMessage.status, func.count(SmsMessage.id))
               .filter(SmsMessage.created_at >= day_start).group_by(SmsMessage.status).all())
    last = db.query(func.max(Order.created_at)).scalar()
    seen = worker_seen_at(db)
    return {
        "version": version(),
        "checks": checks(db),
        "queue_length": queue_length(),
        "worker_seen_at": seen.isoformat() + "Z" if seen else None,
        "tracking": track_stats() or None,
        "sms": {k: int(v) for k, v in sms.items()},
        "orders_today": db.query(func.count(Order.id)).filter(Order.created_at >= day_start).scalar() or 0,
        "last_order_at": last.isoformat() + "Z" if last else None,
        "alerts": list(_alert_state(db).keys()),
        "sentry": bool(config.SENTRY_DSN),
        "metrics_url": f"{config.ROOT_PATH}/api/metrics" if config.METRICS_TOKEN else None,
    }


# ---------------------------------------------------------------- сповіщення
def send_telegram(token: str, chat: str, text_: str, client: httpx.Client | None = None) -> tuple[bool, str]:
    own = client is None
    client = client or httpx.Client(timeout=15)
    try:
        r = client.post(f"https://api.telegram.org/bot{token}/sendMessage",
                        json={"chat_id": chat, "text": text_, "disable_web_page_preview": True})
        data = r.json()
        return bool(data.get("ok")), str(data.get("description", ""))
    except (httpx.HTTPError, ValueError) as e:
        return False, str(e)
    finally:
        if own:
            client.close()


def _alert_state(db: Session) -> dict:
    try:
        return json.loads(st.get(db, "alert_state") or "{}")
    except ValueError:
        return {}


def evaluate(db: Session, now: datetime | None = None) -> dict[str, str]:
    """Поточні проблеми: {ключ: текст}. Ключ стабільний, поки проблема триває."""
    now = now or utcnow()
    problems: dict[str, str] = {}
    since = now - timedelta(minutes=30)
    failed = (db.query(SmsMessage).filter(SmsMessage.status == "failed", SmsMessage.created_at >= since)
              .order_by(SmsMessage.id.desc()).all())
    if failed:
        problems["sms_failed"] = f"Не вдалося надіслати SMS/Viber: {len(failed)} за 30 хв. Остання помилка: {failed[0].error or '—'}"
    from ..carriers import CARRIERS
    for code, s in track_stats().items():
        if s.get("consecutive_errors", 0) >= 3:
            name = CARRIERS[code].name if code in CARRIERS else code
            err = (s.get("errors") or ["—"])[0]
            problems[f"track_{code}"] = f"Трекінг «{name}» не працює вже {s['consecutive_errors']} перевірки поспіль: {err}"
    ql = queue_length()
    if ql is not None and ql > 200:
        problems["queue"] = f"Черга задач переповнена: {ql} задач чекають (воркер не встигає або зупинився)"
    hours = st.get_int(db, "alert_no_leads_hours", 0)
    if hours > 0:
        from zoneinfo import ZoneInfo
        local = now.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(config.DISPLAY_TZ))
        if 8 <= local.hour < 22:  # уночі заявок і не має бути
            last = db.query(func.max(Order.created_at)).scalar()
            if last is None or now - last > timedelta(hours=hours):
                ago = f"{(now - last).total_seconds() / 3600:.1f} год" if last else "жодної"
                problems["no_leads"] = f"Немає нових заявок уже {ago} — перевірте лендинги, форму і рекламу"
    return problems


def run_alerts(db: Session, client: httpx.Client | None = None, now: datetime | None = None) -> dict:
    """Надсилає сповіщення про нові проблеми й про відновлення. Повертає {"opened": [...], "resolved": [...]}."""
    current = evaluate(db, now)
    state = _alert_state(db)
    opened = [k for k in current if k not in state]
    resolved = [k for k in state if k not in current]
    token, chat = st.get(db, "alert_tg_token"), st.get(db, "alert_tg_chat")
    company = st.get(db, "company_name")
    if token and chat:
        for k in opened:
            send_telegram(token, chat, f"⚠️ {company}: {current[k]}", client)
        for k in resolved:
            send_telegram(token, chat, f"✅ {company}: відновлено — {state[k].get('text', k)}", client)
    new_state = {k: state.get(k, {"since": (now or utcnow()).isoformat(), "text": v}) for k, v in current.items()}
    if new_state != state:
        st.set_value(db, "alert_state", json.dumps(new_state, ensure_ascii=False))
        db.commit()
    return {"opened": opened, "resolved": resolved}


# ---------------------------------------------------------------- метрики Prometheus
_metrics = None


def metrics():
    """Лічильники HTTP-запитів. У кількох процесах uvicorn — режим multiprocess (PROMETHEUS_MULTIPROC_DIR)."""
    global _metrics
    if _metrics is None:
        from prometheus_client import Counter, Histogram
        _metrics = {
            "requests": Counter("crm_http_requests_total", "HTTP-запити", ["method", "route", "status"]),
            "latency": Histogram("crm_http_request_duration_seconds", "Тривалість HTTP-запитів", ["route"],
                                 buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)),
        }
    return _metrics


def observe(method: str, route: str, status: int, seconds: float) -> None:
    try:
        m = metrics()
        m["requests"].labels(method, route, str(status)).inc()
        m["latency"].labels(route).observe(seconds)
    except Exception:  # noqa: BLE001 — метрики не повинні ламати запити
        pass


def render_metrics(db: Session) -> bytes:
    from prometheus_client import CollectorRegistry, generate_latest
    from prometheus_client.core import GaugeMetricFamily

    metrics()  # лічильники HTTP мають існувати, навіть якщо запитів ще не було
    if os.getenv("PROMETHEUS_MULTIPROC_DIR"):
        from prometheus_client import multiprocess
        http_registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(http_registry)  # сума по всіх процесах uvicorn
    else:
        from prometheus_client import REGISTRY as http_registry  # один процес

    snapshot = system_status(db)

    class State:
        def collect(self):
            g = GaugeMetricFamily("crm_component_up", "Компонент працює (1) чи ні (0)", labels=["component"])
            for name, c in snapshot["checks"].items():
                g.add_metric([name], 1 if c["ok"] else 0)
            yield g
            if snapshot["queue_length"] is not None:
                yield GaugeMetricFamily("crm_queue_length", "Задач у черзі arq", value=snapshot["queue_length"])
            yield GaugeMetricFamily("crm_orders_24h", "Нових замовлень за 24 год", value=snapshot["orders_today"])
            if snapshot["last_order_at"]:
                last = datetime.fromisoformat(snapshot["last_order_at"].rstrip("Z"))
                yield GaugeMetricFamily("crm_last_order_age_seconds", "Секунд від останньої заявки",
                                        value=(utcnow() - last).total_seconds())
            sms = GaugeMetricFamily("crm_sms_24h", "SMS/Viber за 24 год за статусом", labels=["status"])
            for k, v in snapshot["sms"].items():
                sms.add_metric([k], v)
            yield sms
            tr = GaugeMetricFamily("crm_tracking_consecutive_errors", "Помилок трекінгу поспіль", labels=["carrier"])
            for k, v in (snapshot["tracking"] or {}).items():
                tr.add_metric([k], v.get("consecutive_errors", 0))
            yield tr
            yield GaugeMetricFamily("crm_alerts_active", "Активних сповіщень", value=len(snapshot["alerts"]))

    state_registry = CollectorRegistry()  # окремий реєстр на кожен запит — без конфліктів при паралельних запитах
    state_registry.register(State())
    return generate_latest(http_registry) + generate_latest(state_registry)


def timed() -> float:
    return time.perf_counter()
