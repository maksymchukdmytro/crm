"""Крок 7: склад з прогнозом, підсумок продажів товару, розширене вікно покупця, додатковий телефон."""
from datetime import timedelta

from app.models import Customer, Order, Product, Status, utcnow
from app.services.stock import forecast

from .test_api import api, new_order  # noqa: F401 — фікстури


def _sid(db, code):
    return db.query(Status).filter(Status.code == code).one().id


def test_forecast_formula():
    assert forecast(30, 30) == (1.0, 30)
    assert forecast(10, 0) == (0.0, None)
    assert forecast(5, 60) == (2.0, 2)


def test_stock_view_filters(api, db, products):
    cream, soap = products
    cream.stock, soap.stock = 3, 50
    db.commit()
    for i in range(3):
        new_order(api, products, phone=f"05011144{i:02d}", items=[{"product_id": cream.id, "name": cream.name, "qty": 3, "price": 399}])
    d = api.get("/api/stock").json()
    row = next(r for r in d["rows"] if r["product_id"] == cream.id)
    assert row["sold_30"] == 9 and row["daily"] == 0.3 and row["days_left"] == 10
    assert d["all"] >= 2 and isinstance(d["moves_today"], list)
    assert all(r["available"] <= 0 for r in api.get("/api/stock?filter=out").json()["rows"])
    dead = api.get("/api/stock?filter=dead").json()["rows"]
    assert any(r["product_id"] == soap.id for r in dead) and not any(r["product_id"] == cream.id for r in dead)
    assert [r["product_id"] for r in api.get(f"/api/stock?q={cream.name[:5]}").json()["rows"]] == [cream.id]


def test_product_summary(api, db, products):
    cream, soap = products
    a = new_order(api, products, phone="0501115501")["id"]          # крем + мило-допродаж
    b = new_order(api, products, phone="0501115502", items=[{"product_id": cream.id, "name": cream.name, "qty": 1, "price": 399}])["id"]
    api.patch(f"/api/orders/{a}", json={"status_id": _sid(db, "delivered")})
    api.patch(f"/api/orders/{b}", json={"status_id": _sid(db, "refused")})
    s = api.get(f"/api/products/{cream.id}/summary").json()
    assert s["qty"] == 3 and s["sum"] == 3 * 399 and s["orders"] == 2
    assert s["buyout_rate"] == 50.0 and s["upsell_share"] == 50.0 and s["sold_total"] == 3
    old = db.get(Order, b)
    old.created_at = utcnow() - timedelta(days=40)
    db.commit()
    assert api.get(f"/api/products/{cream.id}/summary?days=30").json()["qty"] == 2


def test_customer_window_and_phone2(api, db, products):
    o = new_order(api, products, phone="0501116601")
    c = db.query(Customer).filter(Customer.phone == "380501116601").one()
    r = api.patch(f"/api/customers/{c.id}", json={"phone2": "067 222 33 44"})
    assert r.status_code == 200, r.text
    assert r.json()["phone2"] == "380672223344"
    # нове замовлення з додаткового номера — той самий покупець
    o2 = new_order(api, products, phone="0672223344")
    assert db.get(Order, o2["id"]).customer_id == c.id
    d = api.get(f"/api/customers/{c.id}").json()
    assert {x["id"] for x in d["history"]} == {o["id"], o2["id"]}
    assert d["addresses"][0]["count"] == 2 and d["addresses"][0]["text"].startswith("НП · Київ")
    assert api.get("/api/customers?q=2223344").json()["rows"][0]["id"] == c.id
    assert api.patch(f"/api/customers/{c.id}", json={"phone2": "12"}).status_code == 400
    assert db.query(Product).count() >= 2
