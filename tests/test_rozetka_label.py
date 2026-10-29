"""ROZETKA Delivery: замовлення з ТТН RMP-… — окрема служба, друк маркування через API Rozetka."""
import json

import httpx

from app.models import Order

from .test_api import api  # noqa: F401 — фікстура

PDF = b"%PDF-1.4 rozetka label"


def _mock(monkeypatch, fail=False):
    from app.services import marketplaces as mp
    seen = []

    def handler(req: httpx.Request):
        u = str(req.url)
        if u.endswith("/sites"):
            return httpx.Response(200, json={"success": True, "content": {"access_token": "TOK"}})
        if "/orders/search" in u:
            return httpx.Response(200, json={"success": True, "content": {"orders": [{
                "id": 905850200, "status": 26, "amount_with_discount": "1700.00", "ttn": "RMP-965555286",
                "recipient_title": {"last_name": "Сізова", "first_name": "Анна"}, "recipient_phone": "380965537688",
                "delivery": {"delivery_service_name": "ROZETKA Delivery", "city": {"name_ua": "Запоріжжя"}},
                "purchases": [{"item_name": "Софтбокс", "quantity": 1, "price": "1700.00", "item": {}}],
                "payment": {"payment_method_name": "Оплата під час отримання"}}], "_meta": {"pageCount": 1}}})
        if u.endswith("/delivery-rozetka/ttn-print-batch"):
            seen.append(json.loads(req.content))
            if fail:
                return httpx.Response(200, json={"success": False, "errors": {"message": "ttn_not_found", "code": 1110}})
            return httpx.Response(200, content=PDF, headers={"Content-Type": "application/pdf"})
        return httpx.Response(404, json={"success": False, "errors": {"message": "not found"}})

    monkeypatch.setattr(mp, "_client", httpx.Client(transport=httpx.MockTransport(handler)))
    return seen


def _import(api, db):
    s = api.put("/api/settings/shops", json=[{"kind": "rozetka", "name": "Antony_store", "login": "seller", "secret": "pass"}]).json()
    api.post(f"/api/settings/shops/{s['shops'][0]['id']}/sync")
    return db.query(Order).filter(Order.external_id == "905850200").one()


def test_rozetka_delivery_label(api, db, monkeypatch):
    seen = _mock(monkeypatch)
    o = _import(api, db)
    assert o.delivery_method == "rozetka" and o.ttn == "RMP-965555286"
    card = api.get(f"/api/orders/{o.id}").json()
    assert card["label"] == "rozetka"
    r = api.get(f"/api/orders/{o.id}/label")
    assert r.status_code == 200 and r.content == PDF and r.headers["content-type"] == "application/pdf"
    assert seen == [{"track_numbers": ["RMP-965555286"]}]


def test_rozetka_label_error_is_readable(api, db, monkeypatch):
    _mock(monkeypatch, fail=True)
    o = _import(api, db)
    r = api.get(f"/api/orders/{o.id}/label")
    assert r.status_code == 422 and "ttn_not_found" in r.text


def test_no_label_without_ttn(api, db, products):
    from .test_orders import create_via_ui  # noqa: F401
    o = db.query(Order).first()
    if o is None:
        return
    o.ttn = ""
    db.commit()
    assert api.get(f"/api/orders/{o.id}").json()["label"] == ""
    assert api.get(f"/api/orders/{o.id}/label").status_code == 404
