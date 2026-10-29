"""Тести JSON API нового інтерфейсу, черги задач і подій."""
import asyncio
import json
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.models import Order, Payment, Product, SmsMessage, Status
from app.services import settings as st

H = {"X-CRM": "1"}


def sid(db, code):
    return db.query(Status).filter(Status.code == code).one().id


@pytest.fixture()
def api(app):
    with TestClient(app) as c:
        r = c.post("/api/auth/login", json={"username": "admin", "password": "admin12345"}, headers=H)
        assert r.status_code == 200, r.text
        c.headers.update(H)
        yield c


@pytest.fixture()
def api_manager(app):
    with TestClient(app) as c:
        c.post("/api/auth/login", json={"username": "manager1", "password": "password123"}, headers=H)
        c.headers.update(H)
        yield c


def new_order(api, products, **over):
    cream, soap = products
    body = {"customer_name": "Шевченко Тарас", "phone": "0501112233", "delivery_method": "novaposhta",
            "city_name": "Київ", "city_ref": "c", "warehouse_name": "№1", "warehouse_ref": "w",
            "items": [{"product_id": cream.id, "name": cream.name, "qty": 2, "price": 399},
                      {"product_id": soap.id, "name": soap.name, "qty": 1, "price": 99, "upsell": True}]}
    body.update(over)
    r = api.post("/api/orders", json=body)
    assert r.status_code == 200, r.text
    return r.json()


# ------------------------------------------------------------------ доступ
def test_auth_and_csrf(app):
    with TestClient(app) as c:
        assert c.get("/api/meta").status_code == 401
        assert c.post("/api/auth/login", json={"username": "admin", "password": "admin12345"}).status_code == 403
        assert c.post("/api/auth/login", json={"username": "admin", "password": "x"}, headers=H).status_code == 401
        assert c.post("/api/auth/login", json={"username": "admin", "password": "admin12345"}, headers=H).status_code == 200
        assert c.get("/api/me").json()["username"] == "admin"
        # зміна без заголовка X-CRM — відмова (захист від CSRF)
        assert c.post("/api/orders", json={"phone": "0671234567"}).status_code == 403
        c.post("/api/auth/logout", headers=H)
        assert c.get("/api/me").status_code == 401


def test_meta(api, products):
    m = api.get("/api/meta").json()
    assert m["user"]["role"] == "admin" and "settings" in m["nav"]
    assert any(s["code"] == "new" for s in m["statuses"])
    assert {p["sku"] for p in m["products"]} == {"CREAM-1", "SOAP-1"}
    assert m["carriers"]["novaposhta"]["configured"] is False
    assert m["realtime"] is False


def test_role_restrictions(api_manager):
    assert api_manager.get("/api/settings").status_code == 403
    assert api_manager.get("/api/payments").status_code == 403
    assert api_manager.get("/api/warehouse").status_code == 403
    assert api_manager.get("/api/reports").status_code == 200
    assert "settings" not in api_manager.get("/api/meta").json()["nav"]


# ------------------------------------------------------------------ замовлення
def test_order_crud_and_lifecycle(api, db, products):
    cream, _ = products
    o = new_order(api, products, discount="47")
    assert o["total"] == 850 and o["cod_amount"] == 850 and len(o["items"]) == 2
    assert o["items"][1]["upsell"] is True and o["history"]

    # статус «Підтверджено» — резерв
    o = api.patch(f"/api/orders/{o['id']}", json={"status_id": sid(db, "confirmed"), "version": o["version"]}).json()
    db.expire_all()
    assert db.get(Product, cream.id).reserved == 2 and o["stock_reserved"]

    # стара версія — конфлікт
    r = api.patch(f"/api/orders/{o['id']}", json={"customer_name": "X", "version": "2000-01-01T00:00:00"})
    assert r.status_code == 409

    # зміна товарів і відправка
    items = [{"product_id": cream.id, "name": cream.name, "qty": 3, "price": 399}]
    o = api.patch(f"/api/orders/{o['id']}", json={"items": items, "status_id": sid(db, "shipped"),
                                                   "version": o["version"]}).json()
    db.expire_all()
    assert db.get(Product, cream.id).stock == 7 and o["stock_shipped"]
    assert o["payments"][0]["status"] == "expected" and o["payments"][0]["amount"] == 1150

    # коментар, передоплата
    o = api.post(f"/api/orders/{o['id']}/comments", json={"text": "Подзвонити після 18:00"}).json()
    assert o["comments"][0]["text"] == "Подзвонити після 18:00"
    assert api.post(f"/api/orders/{o['id']}/comments", json={"text": " "}).status_code == 400


def test_order_list_cursor_counts_filters(api, db, products, webhook_key):
    for i in range(7):
        api.post(f"/api/v1/orders?key={webhook_key}", data={"phone": f"06712345{i:02d}", "sku": "CREAM-1",
                                                             "utm_source": "fb" if i % 2 else "google"})
    page1 = api.get("/api/orders?limit=3").json()
    assert len(page1["items"]) == 3 and page1["total"] == 7 and page1["next"]
    page2 = api.get(f"/api/orders?limit=3&before={page1['next']}&counts=0").json()
    assert len(page2["items"]) == 3 and page2.get("total") is None
    assert {x["id"] for x in page1["items"]}.isdisjoint({x["id"] for x in page2["items"]})
    assert api.get("/api/orders?source=fb").json()["total"] == 3
    assert api.get("/api/orders?q=0671234503").json()["total"] == 1
    assert sum(page1["counts"].values()) == 7
    assert "fb" in api.get("/api/orders/sources").json()


def test_bulk_without_queue(api, db, products, webhook_key):
    ids = [api.post(f"/api/v1/orders?key={webhook_key}", data={"phone": f"067000{i:04d}", "sku": "CREAM-1"})
           .json()["order_id"] for i in range(3)]
    r = api.post("/api/orders/bulk", json={"ids": ids[:2], "action": "status", "value": sid(db, "confirmed")}).json()
    assert r["done"] == 2
    # ТТН без налаштованої НП — помилки повертаються, черги немає
    r = api.post("/api/orders/bulk", json={"ids": ids, "action": "ttn"}).json()
    assert r["queued"] == 0 and len(r["errors"]) == 3


def test_take_and_manager_visibility(api_manager, db, products):
    st.set_value(db, "managers_see_own_only", "1")
    db.commit()
    o = new_order(api_manager, products)
    assert o["manager"]["username"] == "manager1"
    other = Order(status_id=sid(db, "new"), phone="380991112233", manager_id=1, customer_name="Чужий")
    db.add(other)
    db.commit()
    assert api_manager.get(f"/api/orders/{other.id}").status_code == 403
    assert all(x["customer_name"] != "Чужий" for x in api_manager.get("/api/orders").json()["items"])


def test_payment_prepayment(api, products):
    o = new_order(api, products)
    o = api.post(f"/api/orders/{o['id']}/payments", json={"amount": "897", "method": "card"}).json()
    assert o["payment_type"] == "prepaid" and o["cod_amount"] == 0


# ------------------------------------------------------------------ склад
def test_products_warehouse_purchases(api, db, products):
    p = api.post("/api/products", json={"name": "Новий", "sku": "N-1", "price": 250, "cost": 100,
                                        "initial_stock": 5}).json()
    assert p["stock"] == 5
    assert api.post("/api/products", json={"name": "Дубль", "sku": "N-1"}).status_code == 409
    p = api.patch(f"/api/products/{p['id']}", json={"price": 270, "upsell": True}).json()
    assert p["price"] == 270 and p["upsell"]
    assert api.get(f"/api/products/{p['id']}").json()["moves"][0]["kind"] == "adjust"
    api.post("/api/warehouse/adjust", json={"product_id": p["id"], "mode": "delta", "qty": "-2"})
    w = api.get("/api/warehouse").json()
    assert next(x for x in w["products"] if x["id"] == p["id"])["stock"] == 3 and w["moves"]

    sup = api.post("/api/suppliers", json={"name": "Постачальник 1"}).json()
    pur = api.post("/api/purchases", json={"supplier_id": sup["id"], "items": [{"product_id": p["id"], "qty": 10,
                                                                                "cost": 130}]}).json()
    assert pur["status"] == "draft" and pur["total"] == 1300
    pur = api.patch(f"/api/purchases/{pur['id']}", json={"then": "receive"}).json()
    assert pur["status"] == "received"
    assert api.patch(f"/api/purchases/{pur['id']}", json={"then": "receive"}).status_code == 409
    assert db.get(Product, p["id"]).stock == 13


# ------------------------------------------------------------------ оплати, звіти, журнал
def test_payments_reports_audit(api, db, products):
    o = new_order(api, products, ttn="20450000000101", status_id=sid(db, "shipped"))
    pays = api.get("/api/payments?status=expected").json()
    assert pays["items"][0]["ttn"] == "20450000000101" and pays["totals"]["expected"]["count"] == 1
    csv = "ЕН;Сума\n20450000000101;897\n"
    rep = api.post("/api/payments/import", files={"file": ("r.csv", csv.encode(), "text/csv")}).json()
    assert len(rep["matched"]) == 1
    api.patch(f"/api/orders/{o['id']}", json={"status_id": sid(db, "delivered")})
    r = api.get("/api/reports").json()
    assert r["total"]["leads"] == 1 and r["total"]["delivered"] == 1 and r["total"]["revenue"] == 897
    assert len(r["days"]) == 30
    a = api.get("/api/audit?entity=order").json()
    assert a["items"] and any(x["action"] == "status" for x in a["items"])


# ------------------------------------------------------------------ налаштування
def test_settings_api(api, db):
    s = api.get("/api/settings").json()
    assert "/api/v1/orders?key=" in s["webhook_url"] and s["statuses"]
    s = api.put("/api/settings/np", json={"np_api_key": "SECRET", "np_payer": "Sender"}).json()
    assert s["values"]["np_api_key"] == "********" and s["values"]["np_payer"] == "Sender"
    api.put("/api/settings/np", json={"np_api_key": "********"})
    assert st.get(db, "np_api_key") == "SECRET"
    api.put("/api/settings/general", json={"managers_see_own_only": True, "company_name": "Магазин"})
    assert st.get(db, "managers_see_own_only") == "1"
    s = api.post("/api/settings/statuses", json={"name": "Чекає оплату", "color": "#ff0000"}).json()
    new = next(x for x in s["statuses"] if x["name"] == "Чекає оплату")
    assert api.delete(f"/api/settings/statuses/{new['id']}").status_code == 200
    u = api.post("/api/users", json={"username": "olena", "password": "password123", "role": "manager"}).json()
    assert u["role"] == "manager"
    assert api.post("/api/users", json={"username": "olena", "password": "password123"}).status_code == 409
    me = api.get("/api/me").json()
    assert api.patch(f"/api/users/{me['id']}", json={"is_active": False}).status_code == 400


def test_events_endpoint_without_redis(api):
    assert api.get("/api/events").status_code == 204


def test_spa_fallback_and_api_404(api):
    assert api.get("/api/nope").status_code == 404


# ------------------------------------------------------------------ черга і події (потрібен Redis)
def _redis_ok():
    try:
        import redis
        redis.Redis.from_url("redis://localhost:6379/15", socket_connect_timeout=1).ping()
        return True
    except Exception:  # noqa: BLE001
        return False


needs_redis = pytest.mark.skipif(not _redis_ok(), reason="Redis недоступний")


@needs_redis
def test_events_published_after_commit(monkeypatch, api, db, products):
    import redis

    from app.config import config
    from app.services import events
    monkeypatch.setattr(config, "REDIS_URL", "redis://localhost:6379/15")
    monkeypatch.setattr(events, "_client", None)
    r = redis.Redis.from_url("redis://localhost:6379/15")
    ps = r.pubsub()
    ps.subscribe(events.CHANNEL)
    ps.get_message(timeout=1)
    o = new_order(api, products)
    got = []
    for _ in range(20):
        m = ps.get_message(timeout=0.2)
        if m and m["type"] == "message":
            got.append(json.loads(m["data"]))
    assert {"type": "order", "id": o["id"]} in got
    assert any(x["type"] == "product" for x in got) is False  # без резерву товар не змінювався
    ps.close()


@needs_redis
def test_queue_runs_sms_job(monkeypatch, db, products):
    """SMS після зміни статусу ставиться в чергу і відправляється воркером arq."""
    import httpx
    from arq.worker import Worker

    from app import tasks
    from app.config import config
    from app.services import events, sms
    from app.services import orders as svc
    url = "redis://localhost:6379/15"
    monkeypatch.setattr(config, "REDIS_URL", url)
    monkeypatch.setattr(events, "_client", None)
    import redis
    redis.Redis.from_url(url).flushdb()
    st.set_value(db, "sms_enabled", "1")
    st.set_value(db, "sms_token", "T")
    db.commit()
    order = svc.create_order(db, {"phone": "0501112233", "customer_name": "Тест"}, [], None)
    db.commit()
    svc.change_status(db, order, db.query(Status).filter(Status.code == "confirmed").one(), None)
    db.commit()  # після коміту — задача send_sms у черзі
    assert db.query(SmsMessage).filter(SmsMessage.status == "queued").count() == 1

    def fake_send(*a, **k):
        return True, "id-1"
    monkeypatch.setattr(sms, "send_turbosms", fake_send)

    from arq.connections import RedisSettings

    async def run():
        await asyncio.sleep(1.2)  # задача поставлена з затримкою 1 с
        worker = Worker(functions=tasks.WorkerSettings.functions, redis_settings=RedisSettings.from_dsn(url),
                        burst=True, poll_delay=0.1)
        await worker.async_run()
        await worker.close()
    asyncio.run(run())
    db.expire_all()
    assert db.query(SmsMessage).filter(SmsMessage.status == "sent").count() == 1


# ------------------------------------------------------------------ схема API
def test_openapi_docs_require_login(app):
    with TestClient(app) as c:
        assert c.get("/api/openapi.json").status_code == 401
        c.post("/api/auth/login", json={"username": "admin", "password": "admin12345"}, headers=H)
        spec = c.get("/api/openapi.json").json()
        assert "/api/orders" in spec["paths"] and "OrderOut" in spec["components"]["schemas"]
        assert not any(p.startswith("/classic") for p in spec["paths"])
        assert c.get("/api/docs").status_code == 200


def test_openapi_snapshot_is_current():
    """frontend/openapi.json (з нього генеруються типи фронтенду) має відповідати коду.
    Якщо тест упав: python scripts/export_openapi.py && (cd frontend && npm run gen:api)"""
    import pathlib
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
    from export_openapi import OUT, schema
    assert OUT.read_text(encoding="utf-8") == schema()


def test_request_validation(api):
    r = api.post("/api/orders", json={"phone": "0671234567", "delivery_method": "dhl"})
    assert r.status_code == 422 and r.json()["error"]
    r = api.post("/api/orders/bulk", json={"ids": [1], "action": "explode"})
    assert r.status_code == 422
    r = api.post("/api/orders", json={"phone": "0671234567", "unknown_field": 1})
    assert r.status_code == 422


# ------------------------------------------------------------------ ПІБ і допродаж
def test_name_parts(api, products):
    from app.services.names import split_full_name
    assert split_full_name("Іван Петренко") == ("Петренко", "Іван", "")
    assert split_full_name("петренко іван іванович") == ("Петренко", "Іван", "Іванович")
    assert split_full_name("Олена Петрівна Коваль") == ("Коваль", "Олена", "Петрівна")
    assert split_full_name("Марина") == ("", "Марина", "")

    o = new_order(api, products, customer_name="Тарас Шевченко")
    assert (o["last_name"], o["first_name"], o["customer_name"]) == ("Шевченко", "Тарас", "Шевченко Тарас")
    # окремі поля мають перевагу, PATCH міняє лише передане
    o = api.patch(f"/api/orders/{o['id']}", json={"middle_name": "Григорович", "version": o["version"]}).json()
    assert o["customer_name"] == "Шевченко Тарас Григорович" and o["first_name"] == "Тарас"


def test_upsell_links_and_item_price(api, db, products):
    cream, soap = products
    p = api.patch(f"/api/products/{soap.id}", json={"upsell": True, "upsell_for": [cream.id, soap.id]}).json()
    assert p["upsell"] is True and p["upsell_for"] == [cream.id]  # сам до себе не привʼязується
    body = {"phone": "0501112233", "first_name": "Тарас", "last_name": "Шевченко",
            "items": [{"product_id": cream.id, "name": cream.name, "qty": 1, "price": 350},
                      {"product_id": soap.id, "name": soap.name, "qty": 1, "upsell": True, "upsell_for": cream.id}]}
    o = api.post("/api/orders", json=body).json()
    main, extra = o["items"]
    assert main["price"] == 350 and main["base_price"] == float(cream.price)  # ціну змінено лише в замовленні
    assert extra["upsell"] and extra["upsell_for"] == cream.id and extra["upsell_for_name"] == cream.name
    assert o["total"] == 350 + float(soap.price)


def test_statuses_save_route(api, db):
    rows = api.get("/api/settings").json()["statuses"]
    rows[0]["name"] = "Нова заявка"
    r = api.put("/api/settings/statuses", json=rows)
    assert r.status_code == 200, r.text
    assert r.json()["statuses"][0]["name"] == "Нова заявка"


# ------------------------------------------------------------------ довідники (етап 1)
def test_directories_payment_methods_and_offices(api, api_manager, db, products):
    meta = api.get("/api/meta").json()
    ids = {m["id"]: m for m in meta["payment_methods"]}
    assert 16 in ids and ids[16]["name"] == "Післяплата NovaPay" and ids[16]["checkbox_type"] == "novapay"
    assert 19 not in ids  # Apple Pay вимкнений за замовчуванням
    assert len(api.get("/api/settings").json()["payment_methods"]) == 47
    assert len(meta["marks"]) == 36 and len(meta["reasons"]) == 14 and meta["countries"]["UA"] == "Україна"

    # вид оплати «Оплачено» → без післяплати; «Передоплата» → передоплата + решта післяплатою
    o = new_order(api, products, payment_method_id=1)
    assert o["payment_type"] == "prepaid" and o["cod_amount"] == 0 and o["payment_method_id"] == 1
    o = api.patch(f"/api/orders/{o['id']}", json={"payment_method_id": 2, "prepayment": 100, "version": o["version"]}).json()
    assert o["payment_type"] == "partial" and o["cod_amount"] == o["total"] - 100

    # відділи: менеджер із доступом лише до «PROM» не бачить замовлення відділу «Сайт»
    s = api.put("/api/settings/dir/offices", json=[{"name": "PROM"}, {"name": "Сайт"}]).json()
    prom, site = [x["id"] for x in s["offices"]]
    mgr = next(u for u in s["users"] if u["username"] == "manager1")
    assert api.patch(f"/api/users/{mgr['id']}", json={"offices": [prom]}).json()["offices"] == [prom]
    o_site = new_order(api, products, office_id=site, country="PL", mark_id=1, remind_at="2026-11-01T10:00:00+02:00")
    assert o_site["country"] == "PL" and o_site["mark_id"] == 1 and o_site["remind_at"].startswith("2026-11-01T08:00")
    o_prom = new_order(api, products, office_id=prom)
    assert api_manager.get(f"/api/orders/{o_site['id']}").status_code in (403, 404)
    assert api_manager.get(f"/api/orders/{o_prom['id']}").status_code == 200

    # видалення відділу, у якого є замовлення, лише вимикає його
    s = api.put("/api/settings/dir/offices", json=[{"id": site, "name": "Сайт", "delete": True}]).json()
    assert [x for x in s["offices"] if x["id"] == site][0]["active"] is False
