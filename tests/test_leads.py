"""Ліди: вкладки й очікування, черга, результат дзвінка, створення замовлення, вимкнення розділу."""
from datetime import timedelta

from app.models import Order, Status, StatusReason, utcnow
from app.services import orders as svc

from .test_api import api, new_order  # noqa: F401 — фікстури


def _sid(db, code):
    return db.query(Status).filter(Status.code == code).one().id


def lead(api, db, products, **over):
    return new_order(api, products, status_id=_sid(db, "new"), **over)["id"]


def test_tabs_wait_and_queue(api, db, products):
    a = lead(api, db, products, phone="0501110001")
    b = lead(api, db, products, phone="0501110002")
    db.get(Order, a).created_at = utcnow() - timedelta(minutes=20)
    db.get(Order, b).created_at = utcnow() - timedelta(minutes=3)
    db.commit()
    d = api.get("/api/orders?stage=lead&tab=open&sort=wait").json()
    assert [x["id"] for x in d["items"]][:2] == [a, b]               # хто чекає найдовше — вгорі
    assert d["items"][0]["wait_minutes"] >= 19 and d["lead_tabs"]["open"] == 2 and d["lead_tabs"]["new"] == 2
    assert api.get("/api/leads/queue").json()["ids"][:2] == [a, b]


def test_lead_results(api, db, products):
    a = lead(api, db, products, phone="0501110003")
    r = api.post(f"/api/orders/{a}/lead-result", json={"result": "no_answer"}).json()
    o = db.get(Order, a)
    db.refresh(o)
    assert o.status.code == "no_answer" and o.call_attempts == 1 and o.remind_at > utcnow() + timedelta(minutes=25)
    assert a not in api.get("/api/leads/queue").json()["ids"]       # до нагадування — не в черзі
    assert r["order"]["id"] == a
    at = (utcnow() + timedelta(hours=2)).isoformat()
    api.post(f"/api/orders/{a}/lead-result", json={"result": "callback", "at": at})
    db.refresh(o)
    assert o.status.code == "callback" and o.call_attempts == 2
    # відмова вимагає причину, якщо причини налаштовано
    db.add(StatusReason(name="Дорого"))
    db.commit()
    assert api.post(f"/api/orders/{a}/lead-result", json={"result": "refused"}).status_code == 400
    rid = db.query(StatusReason).first().id
    assert api.post(f"/api/orders/{a}/lead-result", json={"result": "refused", "reason_id": rid}).status_code == 200
    db.refresh(o)
    assert o.status.code == "lead_refused" and o.reason_id == rid
    # дубль з посиланням на перший
    b = lead(api, db, products, phone="0501110004")
    assert api.post(f"/api/orders/{b}/lead-result", json={"result": "duplicate", "duplicate_of_id": a}).status_code == 200
    ob = db.get(Order, b)
    db.refresh(ob)
    assert ob.status.code == "duplicate" and ob.duplicate_of_id == a
    # уже не лід
    assert api.post(f"/api/orders/{b}/lead-result", json={"result": "no_answer"}).status_code == 400


def test_convert(api, db, products):
    a = lead(api, db, products, phone="0501110005", items=[])
    r = api.post(f"/api/orders/{a}/convert")
    assert r.status_code == 422 and "товар" in r.text
    b = lead(api, db, products, phone="0501110006")
    o = db.get(Order, b)
    o.payment_method_id = 4
    db.commit()
    r = api.post(f"/api/orders/{b}/convert")
    assert r.status_code == 200, r.text
    db.refresh(o)
    assert o.status.code == "confirmed" and o.converted_at is not None
    d = api.get("/api/orders?stage=lead&tab=converted&sort=wait").json()
    assert [x["id"] for x in d["items"]] == [b]


def test_disable_moves_open_leads(api, db, products):
    a = lead(api, db, products, phone="0501110007")
    assert api.get("/api/settings/leads/preview").json() == {"enabled": True, "open": 1}
    r = api.post("/api/settings/leads", json={"enabled": False, "move_open": True}).json()
    assert r == {"enabled": False, "moved": 1}
    o = db.get(Order, a)
    db.refresh(o)
    assert o.status.code == "unsorted"
    m = api.get("/api/meta").json()
    assert m["leads_enabled"] is False and m["counters"]["leads_new"] == 0
    # форма при вимкнених лідах — одразу в «Несортовані»
    assert svc.initial_status(db, "webhook").code == "unsorted"
    assert api.post("/api/settings/leads", json={"enabled": True}).json()["enabled"] is True


def test_lead_settings_validation(api):
    assert api.put("/api/settings/general", json={"lead_wait_warn_min": "7", "lead_to_order_status": "unsorted"}).status_code == 200
    assert api.put("/api/settings/general", json={"lead_wait_warn_min": "сім"}).status_code == 400
    assert api.put("/api/settings/general", json={"lead_to_order_status": "delivered"}).status_code == 400
