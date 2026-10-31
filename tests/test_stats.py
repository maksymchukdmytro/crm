"""Статистика: графік, основне / допродаж, фільтри, розрізи, сегменти, замовлення, експорт, дати замовлення."""
from datetime import datetime, timedelta

from app.models import Order, OrderSource, Status, User, utcnow
from app.services import settings as st
from app.services import stats as svc
from app.formatting import today_local

from .test_api import api, api_manager, new_order, sid  # noqa: F401 — фікстури


def day(n: int = 0) -> str:
    return (today_local() + timedelta(days=n)).isoformat()


def move(db, order_id: int, **fields):
    o = db.get(Order, order_id)
    for k, v in fields.items():
        setattr(o, k, v)
    db.commit()


def test_summary_main_vs_upsell(api, db, products):
    cream, soap = products
    new_order(api, products)  # крем ×2 (основний) + мило ×1 (допродаж)
    new_order(api, products, items=[{"product_id": cream.id, "name": cream.name, "qty": 1, "price": 399}], discount=50)
    r = api.get("/api/stats?date_field=created").json()
    s = r["summary"]
    assert s["orders"] == 2 and s["orders_upsell"] == 1 and s["orders_plain"] == 1 and s["upsell_rate"] == 50
    assert s["qty_main"] == 3 and s["qty_upsell"] == 1 and s["qty"] == 4 and s["qty_upsell_rate"] == 25
    assert s["sum_upsell"] == 99 and s["sum_main"] == 399 * 3 - 50 and s["sum"] == 399 * 3 - 50 + 99
    assert s["margin_upsell"] == 99 - 30 and s["margin_main"] == (399 - 120) * 3 - 50
    assert s["avg_check"] == round((399 * 3 - 50 + 99) / 2, 2)
    assert r["series"][-1]["total"] == 2 and r["group"] == "day" and len(r["series"]) == 30
    assert r["prev"]["orders"] == 0 and r["prev"]["date_to"] == day(-30)
    rows = api.get("/api/stats/products").json()["rows"]
    top = rows[0]
    assert top["product_id"] == cream.id and top["qty_main"] == 3 and top["orders"] == 2 and top["sku"] == "CREAM-1"
    assert rows[1]["qty_upsell"] == 1 and rows[1]["margin_upsell"] == 69


def test_filters(api, db, products):
    cream, soap = products
    src = OrderSource(name="Instagram")
    db.add(src)
    db.commit()
    a = new_order(api, products, utm_source="fb", extra1="акція-1", source_id=src.id)
    b = new_order(api, products, items=[{"product_id": cream.id, "name": cream.name, "qty": 1, "price": 399}], utm_source="google")
    c = new_order(api, products, items=[{"product_id": soap.id, "name": soap.name, "qty": 1, "price": 99}])
    get = lambda q: {o["id"] for o in api.get(f"/api/stats/orders?{q}").json()["rows"]}  # noqa: E731
    assert get("") == {a["id"], b["id"], c["id"]}
    assert get(f"product={soap.id}") == {a["id"], c["id"]}
    assert get("utm_source=fb,google") == {a["id"], b["id"]}
    assert get(f"utm_source={svc.EMPTY}") == {c["id"]}
    assert get(f"utm_source=fb,{svc.EMPTY}") == {a["id"], c["id"]}
    assert get(f"source={src.id}") == {a["id"]}
    assert get(f"source={svc.EMPTY}") == {b["id"], c["id"]}
    assert get("extra1=акція-1") == {a["id"]}
    assert get("upsell=with") == {a["id"]} and get("upsell=without") == {b["id"], c["id"]}
    assert get("search=акція") == {a["id"]}
    api.patch(f"/api/orders/{b['id']}", json={"status_id": sid(db, "confirmed")})
    assert get(f"status={sid(db, 'confirmed')}") == {b["id"]}
    assert get(f"status={sid(db, 'confirmed')},{sid(db, 'unsorted')}") == {a["id"], b["id"], c["id"]}
    opts = api.get("/api/stats/options").json()
    assert {x["value"] for x in opts["values"]["utm_source"]} == {"fb", "google"}
    assert opts["date_fields"]["assigned"] == "Закріплене" and "weekday" in opts["dimensions"]


def test_order_dates_assigned_and_confirmed(api, db, products):
    o = new_order(api, products)
    order = db.get(Order, o["id"])
    assert order.assigned_at is None and order.confirmed_at is None  # адмін створив — без менеджера
    m1 = db.query(User).filter(User.username == "manager1").one()
    api.patch(f"/api/orders/{o['id']}", json={"manager_id": m1.id})
    db.expire_all()
    first = db.get(Order, o["id"]).assigned_at
    assert first is not None
    api.patch(f"/api/orders/{o['id']}", json={"status_id": sid(db, "no_answer")})
    db.expire_all()
    assert db.get(Order, o["id"]).confirmed_at is None  # «Недозвон» — не апрув
    api.patch(f"/api/orders/{o['id']}", json={"status_id": sid(db, "confirmed")})
    db.expire_all()
    confirmed = db.get(Order, o["id"]).confirmed_at
    assert confirmed is not None
    api.patch(f"/api/orders/{o['id']}", json={"status_id": sid(db, "packing")})
    db.expire_all()
    assert db.get(Order, o["id"]).confirmed_at == confirmed  # лише перший апрув
    api.post("/api/orders/bulk", json={"ids": [o["id"]], "action": "assign", "value": 0})
    db.expire_all()
    assert db.get(Order, o["id"]).assigned_at is None
    # менеджер створює сам — закріплене одразу
    with_mgr = new_order(api, products, manager_id=m1.id)
    db.expire_all()
    assert db.get(Order, with_mgr["id"]).assigned_at is not None
    # тип дати «Закріплене» у статистиці бачить лише замовлення з менеджером
    r = api.get("/api/stats?date_field=assigned").json()
    assert r["summary"]["orders"] == 1
    # час підтвердження
    move(db, o["id"], created_at=confirmed - timedelta(minutes=30))
    r = api.get("/api/stats?date_field=confirmed").json()
    assert r["summary"]["confirm_avg_min"] == 30.0


def test_groups_and_date_fields(api, db, products):
    a = new_order(api, products)
    b = new_order(api, products)
    move(db, b["id"], created_at=utcnow() - timedelta(days=3))
    r = api.get(f"/api/stats?date_from={day()}&date_to={day()}").json()
    assert r["group"] == "hour" and len(r["series"]) == 24 and r["summary"]["orders"] == 1
    r = api.get(f"/api/stats?date_from={day(-6)}&date_to={day()}").json()
    assert r["group"] == "day" and len(r["series"]) == 7 and sum(p["total"] for p in r["series"]) == 2
    r = api.get(f"/api/stats?date_from={day(-6)}&date_to={day()}&group=week").json()
    assert r["group"] == "week" and sum(p["total"] for p in r["series"]) == 2
    r = api.get(f"/api/stats?date_from={day(-60)}&date_to={day()}&group=month").json()
    assert r["group"] == "month" and r["series"][0]["t"].endswith("-01T00:00")
    # «Відправлене»: лише відправлені замовлення
    assert api.get("/api/stats?date_field=shipped").json()["summary"]["orders"] == 0
    move(db, a["id"], shipped_at=utcnow())
    assert api.get("/api/stats?date_field=shipped").json()["summary"]["orders"] == 1
    # «Весь час» — від найранішого замовлення
    move(db, b["id"], created_at=utcnow() - timedelta(days=400))
    r = api.get("/api/stats?all_time=true").json()
    assert r["summary"]["orders"] == 2 and r["prev"] is None and r["group"] == "week"
    # статуси й частки
    assert r["statuses"][0]["count"] == 2 and r["statuses"][0]["share"] == 100


def test_rates_breakdown_and_segments(api, db, products):
    cream, _ = products
    src = OrderSource(name="TikTok")
    db.add(src)
    db.commit()
    ids = [new_order(api, products, source_id=src.id, phone=f"05011100{i:02d}")["id"] for i in range(3)]
    other = new_order(api, products, phone="0501110099",
                      items=[{"product_id": cream.id, "name": cream.name, "qty": 5, "price": 399}])["id"]
    delivered, refused = db.query(Status).filter(Status.code == "delivered").one(), db.query(Status).filter(Status.code == "refused").one()
    move(db, ids[0], status_id=delivered.id, shipped_at=utcnow())
    move(db, ids[1], status_id=refused.id, shipped_at=utcnow())
    s = api.get("/api/stats").json()["summary"]
    assert s["approved"] == 2 and s["approve_rate"] == 50 and s["delivered"] == 1 and s["refused"] == 1 and s["buyout_rate"] == 50
    rows = api.get("/api/stats/breakdown?dim=source").json()["rows"]
    tiktok = next(r for r in rows if r["label"] == "TikTok")
    assert tiktok["orders"] == 3 and tiktok["approve_rate"] == round(2 * 100 / 3, 1) and tiktok["buyout_rate"] == 50
    # підтверджений дубль не дає апруву понад 100%: дублі без апруву зі знаменника виключаються
    move(db, other, duplicate_of_id=ids[0])
    s = api.get("/api/stats").json()["summary"]
    assert s["duplicates"] == 1 and s["approve_rate"] == round(2 * 100 / 3, 1)
    empty = next(r for r in rows if r["key"] == svc.EMPTY)
    assert empty["orders"] == 1 and empty["label"] == "Пусте поле"
    hours = api.get("/api/stats/breakdown?dim=hour").json()["rows"]
    assert sum(r["orders"] for r in hours) == 4 and hours[0]["label"].endswith(":59")
    week = api.get("/api/stats/breakdown?dim=weekday").json()["rows"]
    assert week[0]["label"] in svc.WEEKDAYS
    seg = api.get("/api/stats/segments?metric=orders_total").json()
    assert seg["step"] > 0 and sum(b["orders"] for b in seg["buckets"]) == 4
    up = api.get("/api/stats/segments?metric=upsell_total").json()
    assert sum(b["orders"] for b in up["buckets"]) == 3  # замовлення без допродажу не рахуються
    rr = api.get("/api/stats/segments?metric=return_rate").json()
    assert any(b["return_rate"] == 50 for b in rr["buckets"])
    assert other


def test_orders_page_visibility_and_export(api, api_manager, db, products):
    m1 = db.query(User).filter(User.username == "manager1").one()
    m2 = db.query(User).filter(User.username == "manager2").one()
    a = new_order(api, products, manager_id=m1.id)
    new_order(api, products, manager_id=m2.id)
    page = api.get("/api/stats/orders?limit=1").json()
    assert page["total"] == 2 and len(page["rows"]) == 1 and page["rows"][0]["items"][0]["qty"] == 2
    st.set_value(db, "managers_see_own_only", "1")
    db.commit()
    mine = api_manager.get("/api/stats/orders").json()
    assert {r["id"] for r in mine["rows"]} == {a["id"]}
    assert api_manager.get("/api/stats").json()["summary"]["orders"] == 1
    for kind, head in (("products", "ID;Артикул;Товар"), ("orders", "№;№ маркетплейсу"), ("breakdown", "Менеджер;Замовлення")):
        r = api.get(f"/api/stats/export.csv?kind={kind}&dim=manager")
        assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
        assert r.text.startswith("﻿" + head), r.text[:80]
    assert "Крем для рук ×2" in api.get("/api/stats/export.csv?kind=orders").text


def test_stats_requires_sales_role(app, db):
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        c.post("/api/auth/login", json={"username": "store", "password": "password123"}, headers={"X-CRM": "1"})
        assert c.get("/api/stats", headers={"X-CRM": "1"}).status_code == 403


def test_bucket_keys_cover_period():
    d0, d1 = datetime(2026, 1, 30).date(), datetime(2026, 3, 2).date()
    assert len(svc.bucket_keys("day", d0, d1)) == 32
    assert [k.month for k in svc.bucket_keys("month", d0, d1)] == [1, 2, 3]
    assert svc.bucket_keys("week", d0, d1)[0].weekday() == 0
    assert len(svc.bucket_keys("hour", d0, d0)) == 24


def test_test_data_create_and_delete(api, db, products):
    real = new_order(api, products)
    r = api.post("/api/system/test-data", json={"action": "create"}).json()
    assert r["products"] == 10 and r["orders"] == 10 and "Створено 10" in r["message"]
    orders = db.query(Order).filter(Order.site == "test-data").all()
    assert len(orders) == 10
    oldest = min(o.created_at for o in orders)
    assert utcnow() - oldest > timedelta(days=4)  # замовлення розкидані по місяцю заднім числом
    assert all(o.created_at > utcnow() - timedelta(days=31) for o in orders)
    assert all(o.confirmed_at is None or o.confirmed_at > o.created_at for o in orders)
    from app.models import SmsMessage, StockMovement
    assert db.query(StockMovement).count() == 0 and db.query(SmsMessage).count() == 0  # без складу й SMS
    s = api.get("/api/stats?site=test-data").json()["summary"]
    assert s["orders"] == 10 and s["delivered"] >= 4
    assert api.get("/api/system/test-data").json()["orders"] == 10
    # повторне створення не дублює товари
    api.post("/api/system/test-data", json={"action": "create"})
    assert api.get("/api/system/test-data").json() == {"products": 10, "orders": 20, "message": ""}
    r = api.post("/api/system/test-data", json={"action": "delete"}).json()
    assert r["orders"] == 0 and r["products"] == 0
    db.expire_all()
    assert db.get(Order, real["id"]) is not None  # справжнє замовлення на місці


def test_test_data_admin_only(api_manager):
    assert api_manager.post("/api/system/test-data", json={"action": "create"}).status_code == 403
