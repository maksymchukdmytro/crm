"""Каркас нового інтерфейсу: налаштування користувача, перемикач відділу, збережені фільтри, лічильники, сповіщення."""
from datetime import timedelta

from app.models import Office, Order, utcnow

from .test_api import api, api_manager, new_order  # noqa: F401 — фікстури


def test_prefs_roundtrip(api):
    assert api.get("/api/me/prefs").json() == {}
    assert api.put("/api/me/prefs/orders.columns", json={"value": ["id", "customer", "total"]}).status_code == 200
    assert api.put("/api/me/prefs/sidebar.collapsed", json={"value": True}).status_code == 200
    assert api.get("/api/me/prefs").json() == {"orders.columns": ["id", "customer", "total"], "sidebar.collapsed": True}
    assert api.get("/api/meta").json()["prefs"]["sidebar.collapsed"] is True
    assert api.put("/api/me/prefs/sidebar.collapsed", json={"value": None}).status_code == 200  # null — видалити
    assert "sidebar.collapsed" not in api.get("/api/me/prefs").json()
    assert api.put("/api/me/prefs/BAD KEY", json={"value": 1}).status_code in (400, 404)
    assert api.put("/api/me/prefs/big", json={"value": "x" * 30000}).status_code == 400


def test_office_switch_limits_lists(api, db, products):
    a, b = Office(name="Сайт"), Office(name="Prom")
    db.add_all([a, b])
    db.commit()
    o1 = new_order(api, products)["id"]
    o2 = new_order(api, products, phone="0672223344")["id"]
    db.get(Order, o1).office_id = a.id
    db.get(Order, o2).office_id = b.id
    db.commit()
    assert {o1, o2} <= {x["id"] for x in api.get("/api/orders").json()["items"]}
    assert api.put("/api/me/office", json={"office_id": a.id}).status_code == 200
    ids = {x["id"] for x in api.get("/api/orders").json()["items"]}
    assert o1 in ids and o2 not in ids
    assert api.get("/api/meta").json()["office"] == a.id
    assert api.put("/api/me/office", json={"office_id": None}).status_code == 200
    assert {o1, o2} <= {x["id"] for x in api.get("/api/orders").json()["items"]}


def test_office_switch_respects_access(api_manager, db):
    from app.models import User
    a, b = Office(name="Сайт"), Office(name="Prom")
    db.add_all([a, b])
    db.commit()
    m = db.query(User).filter(User.username == "manager1").one()
    m.offices = [a.id]
    db.commit()
    assert api_manager.put("/api/me/office", json={"office_id": b.id}).status_code == 403
    assert api_manager.put("/api/me/office", json={"office_id": a.id}).status_code == 200


def test_saved_filters_and_counters(api, db, products):
    new_order(api, products)
    oid = new_order(api, products, phone="0672223344")["id"]
    st = api.get("/api/meta").json()["statuses"]
    new_id = next(s["id"] for s in st if s["code"] == "new")
    r = api.post("/api/saved-filters", json={"name": "Нові", "color": "#7C3AED", "query": f"?status={new_id}&evil=1"})
    assert r.status_code == 200, r.text
    sf = r.json()
    assert sf["query"] == f"status={new_id}" and sf["mine"] is True    # невідомі параметри відкинуто
    c = api.get("/api/counters").json()
    assert c["saved"][str(sf["id"])] >= 2
    db.get(Order, oid).remind_at = utcnow() - timedelta(minutes=5)
    db.commit()
    assert api.get("/api/counters").json()["reminders_due"] == 1
    n = api.get("/api/notifications").json()
    assert n["reminders"][0]["order_id"] == oid and n["reminders"][0]["due"] is True
    assert api.patch(f"/api/saved-filters/{sf['id']}", json={"name": "Нові ліди"}).json()["name"] == "Нові ліди"
    assert api.post("/api/saved-filters", json={"name": "Спільний", "is_shared": True}).status_code == 200  # адмін може
    assert api.post("/api/saved-filters", json={"name": "", "query": ""}).status_code == 400
    assert api.post("/api/saved-filters", json={"name": "x", "color": "red"}).status_code == 400
    assert api.delete(f"/api/saved-filters/{sf['id']}").status_code == 200
    assert all(x["id"] != sf["id"] for x in api.get("/api/saved-filters").json())


def test_saved_filters_private(api, api_manager):
    sf = api.post("/api/saved-filters", json={"name": "Мій"}).json()
    assert all(x["id"] != sf["id"] for x in api_manager.get("/api/saved-filters").json())
    assert api_manager.delete(f"/api/saved-filters/{sf['id']}").status_code == 404
    assert api_manager.post("/api/saved-filters", json={"name": "Спільний", "is_shared": True}).status_code == 403
