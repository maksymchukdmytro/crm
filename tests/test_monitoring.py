"""Моніторинг: перевірки стану, метрики, сповіщення в Telegram."""
import json
from datetime import datetime, timedelta

import httpx
import pytest
from fastapi.testclient import TestClient

from app.models import Order, SmsMessage, Status, utcnow
from app.services import monitoring
from app.services import settings as st

from .test_api import H, api  # noqa: F401  (фікстура)


def test_healthz_full_reflects_worker(app, db):
    with TestClient(app) as c:
        assert c.get("/healthz").json() == {"ok": True}
        r = c.get("/healthz/full")
        assert r.status_code == 503 and r.json()["checks"]["worker"]["ok"] is False
        monitoring.beat(db)  # без Redis пульс пишеться в налаштування
        r = c.get("/healthz/full")
        assert r.status_code == 200 and r.json()["checks"]["database"]["ok"]


def test_system_endpoint(api, db):  # noqa: F811
    monitoring.beat(db)
    s = api.get("/api/system").json()
    assert s["checks"]["worker"]["ok"] and s["sentry"] is False and s["queue_length"] is None
    assert "orders_today" in s and s["alerts"] == []


def test_metrics_access(monkeypatch, app, db):
    from app.config import config
    with TestClient(app) as c:
        assert c.get("/api/metrics").status_code == 401
        monkeypatch.setattr(config, "METRICS_TOKEN", "secret-token")
        assert c.get("/api/metrics", headers={"Authorization": "Bearer wrong"}).status_code == 401
        r = c.get("/api/metrics", headers={"Authorization": "Bearer secret-token"})
        assert r.status_code == 200
        body = r.text
        assert 'crm_component_up{component="database"} 1.0' in body
        assert "crm_http_requests_total" in body and "crm_orders_24h" in body


def _tg():
    sent = []

    def handler(request):
        sent.append(json.loads(request.content)["text"])
        return httpx.Response(200, json={"ok": True})
    return sent, httpx.Client(transport=httpx.MockTransport(handler))


def test_alerts_open_and_resolve(db):
    st.set_value(db, "alert_tg_token", "T")
    st.set_value(db, "alert_tg_chat", "1")
    db.add(SmsMessage(phone="380501112233", text="x", status="failed", error="NO_MONEY"))
    db.commit()
    sent, client = _tg()
    res = monitoring.run_alerts(db, client)
    assert res["opened"] == ["sms_failed"] and "NO_MONEY" in sent[0]
    # проблема триває — повторно не надсилаємо
    monitoring.run_alerts(db, client)
    assert len(sent) == 1
    # через годину збій уже не в межах 30 хв — сповіщення про відновлення
    later = utcnow() + timedelta(hours=1)
    res = monitoring.run_alerts(db, client, now=later)
    assert res["resolved"] == ["sms_failed"] and sent[-1].startswith("✅")


def test_no_leads_alert_daytime_only(db):
    st.set_value(db, "alert_no_leads_hours", "3")
    db.add(Order(status_id=db.query(Status).first().id, phone="380501112233", created_at=utcnow() - timedelta(hours=5)))
    db.commit()
    from zoneinfo import ZoneInfo
    def at(hour):  # момент за київським часом → UTC без tz
        local = datetime.now(ZoneInfo("Europe/Kyiv")).replace(hour=hour, minute=0, second=0, microsecond=0)
        return local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    day = at(14)
    db.query(Order).update({Order.created_at: day - timedelta(hours=5)})
    db.commit()
    assert "no_leads" in monitoring.evaluate(db, now=day)
    night = at(3)
    db.query(Order).update({Order.created_at: night - timedelta(hours=5)})
    db.commit()
    assert "no_leads" not in monitoring.evaluate(db, now=night)


def test_alert_test_endpoint(monkeypatch, api, db):  # noqa: F811
    assert api.post("/api/system/alert-test").status_code == 400
    api.put("/api/settings/alerts", json={"alert_tg_token": "T", "alert_tg_chat": "42", "alert_no_leads_hours": "2"})
    assert st.get(db, "alert_no_leads_hours") == "2"
    monkeypatch.setattr(monitoring, "send_telegram", lambda *a, **k: (True, ""))
    assert api.post("/api/system/alert-test").json() == {"ok": True}
    s = api.get("/api/settings").json()
    assert s["values"]["alert_tg_token"] == "********" and "alert_state" not in s["values"]


@pytest.mark.parametrize("dsn", [""])
def test_sentry_off_without_dsn(dsn):
    assert monitoring.init_sentry("web") is False
