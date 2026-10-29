"""Головна сторінка, значки позначок, увімкнення полів 1–4."""
from app.models import OrderMark

from .test_api import api  # noqa: F401 — фікстура
from .test_orders import create_via_ui


def test_dashboard_numbers(api, admin, db, products):
    create_via_ui(admin, products)
    create_via_ui(admin, products, phone="0679998877")
    create_via_ui(admin, products)  # дубль за телефоном — у продажі не рахується
    d = api.get("/api/dashboard").json()
    assert d["today"]["orders"] == 2 and d["today"]["sum"] == 2 * 897
    assert d["month"]["orders"] >= 2 and d["month"]["sum"] >= 2 * 897
    assert d["customers"]["total"] >= 1 and d["customers"]["new"] >= 1
    assert d["attention"]["leads_new"] >= 2  # нові — у статусі «Новий»
    assert len(d["days"]) >= 1 and d["days"][-1]["orders"] == 2
    assert d["top"] and d["top"][0]["qty"] >= 2
    assert any(u["name"] for u in d["team"])  # адміністратор бачить команду


def test_marks_have_icons_and_can_be_changed(api, db):
    m = db.query(OrderMark).filter_by(name="Терміново").one()
    assert (m.icon, m.color) == ("alert", "#dc2626")
    marks = api.get("/api/meta").json()["marks"]
    assert next(x for x in marks if x["name"] == "Терміново")["icon"] == "alert"
    body = [{"id": m.id, "name": "Терміново", "active": True, "sort": 0, "icon": "flame", "color": "#ea580c"}]
    assert api.put("/api/settings/dir/marks", json=body).status_code == 200
    db.expire_all()
    assert (db.get(OrderMark, m.id).icon, db.get(OrderMark, m.id).color) == ("flame", "#ea580c")
    bad = [{"id": m.id, "name": "Терміново", "active": True, "sort": 0, "color": "red"}]
    assert api.put("/api/settings/dir/marks", json=bad).status_code == 422


def test_extra_fields_can_be_switched_off(api):
    assert api.get("/api/meta").json()["extra_on"] == [True, True, True, True]
    r = api.put("/api/settings/fields", json={"extra1_name": "Магазин", "extra3_on": "0", "extra4_on": "0"})
    assert r.status_code == 200, r.text
    meta = api.get("/api/meta").json()
    assert meta["extra_on"] == [True, True, False, False] and meta["extra_fields"][0] == "Магазин"
