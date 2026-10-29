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


# ------------------------------------------------------------------ Нова Пошта: кілька ключів, вікно ТТН, правила (етап 2)
def test_np_accounts_ttn_dialog_and_rules(api, db, products, mock_api):
    from .test_delivery_payments import np_mock
    np_mock(mock_api, status_code="7")
    mock_api.on(lambda c: c["json"].get("calledMethod") == "getCounterparties",
                {"success": True, "data": [{"Ref": "S1", "Description": "ФОП Перший"}]})
    mock_api.on(lambda c: c["json"].get("calledMethod") == "getCounterpartyContactPersons",
                {"success": True, "data": [{"Ref": "C1", "Description": "Іван", "Phones": "380501112233"}]})
    cream, soap = products
    api.patch(f"/api/products/{cream.id}", json={"length": 20, "width": 10, "height": 5, "ship_description": "Косметика"})
    s = api.put("/api/settings/np-accounts", json=[
        {"name": "ФОП Перший", "api_key": "KEY1", "city_ref": "CS", "warehouse_ref": "WS", "cod_mode": "afterpayment"},
        {"name": "ФОП Другий", "api_key": "KEY2", "city_ref": "CS2", "warehouse_ref": "WS2", "is_default": True},
    ]).json()
    by = {a["name"]: a for a in s["np_accounts"]}
    a1, a2 = by["ФОП Перший"], by["ФОП Другий"]
    assert a1["api_key"] == "********" and (a1["is_default"], a2["is_default"]) == (False, True)
    s = api.post(f"/api/settings/np-accounts/{a1['id']}/sync").json()
    a1 = next(a for a in s["np_accounts"] if a["id"] == a1["id"])
    assert a1["sender_ref"] == "S1" and a1["contact_ref"] == "C1" and a1["sender_phone"] == "380501112233"
    api.post(f"/api/settings/np-accounts/{a2['id']}/sync")

    o = new_order(api, products, items=[{"product_id": cream.id, "name": cream.name, "qty": 2, "price": 399}])
    p = api.get(f"/api/orders/{o['id']}/ttn/preview").json()
    assert p["supported"] and p["np_account_id"] == a2["id"]  # основний ключ
    assert p["params"]["seats"][0] == {"length": 20, "width": 10, "height": 10, "weight": 0.6}  # висоти складаються
    assert p["params"]["description"] == "Косметика" and "Крем для рук ×2" in p["params"]["additional_info"]
    # вибраний у вікні ключ і змінені параметри йдуть у ТТН
    r = api.post(f"/api/orders/{o['id']}/ttn", json={"np_account_id": a1["id"], "description": "Подарунок",
                                                     "seats": [{"length": 30, "width": 20, "height": 10, "weight": 1.2}]})
    assert r.status_code == 200, r.text
    assert r.json()["ttn"] == "20450000000001"
    doc = [c["json"] for c in mock_api.calls if c["json"].get("modelName") == "InternetDocument"][-1]
    props = doc["methodProperties"]
    assert doc["apiKey"] == "KEY1" and props["Description"] == "Подарунок" and props["Weight"] == "1.2"
    assert props["OptionsSeat"][0]["volumetricLength"] == "30" and "AfterpaymentOnGoodsCost" in props
    assert props["AdditionalInformation"].startswith("Крем для рук ×2")

    # правило: «Прибув на відділення» (7) → «Отримано», крім статусу «Скасовано»
    rule = {"np_code": "7", "status_id": sid(db, "delivered"), "except_ids": [sid(db, "cancelled")]}
    assert api.put("/api/settings/np-rules", json=[rule]).json()["np_status_rules"][0]["np_code"] == "7"
    from app.services import delivery
    delivery.sync_tracking(db, order_ids=[o["id"]], force=True)
    db.expire_all()
    assert db.get(Order, o["id"]).status.code == "delivered"

    # вид оплати «Оплачено» прибирає післяплату з ТТН
    o2 = new_order(api, products, payment_method_id=1)
    assert api.get(f"/api/orders/{o2['id']}/ttn/preview").json()["params"]["cod_mode"] == "none"


# ------------------------------------------------------------------ маркетплейси (етап 3)
def test_rozetka_and_prom_import_and_status_push(api, db, products, monkeypatch):
    import httpx
    from app.services import marketplaces as mp
    cream, soap = products
    calls = []

    def handler(req: httpx.Request):
        calls.append((req.method, str(req.url), req.content.decode() if req.content else ""))
        u = str(req.url)
        if u.endswith("/sites"):
            return httpx.Response(200, json={"success": True, "content": {"access_token": "TOK"}})
        if "/orders/statuses" in u:
            return httpx.Response(200, json={"success": True, "content": {"data": [{"id": 1, "name_uk": "Нове замовлення"}, {"id": 3, "name_uk": "Переданий в службу доставки"}]}})
        if "/orders/search" in u:
            return httpx.Response(200, json={"success": True, "content": {"orders": [{
                "id": 905850113, "status": 1, "amount_with_discount": "3899.00", "ttn": "20451534560757",
                "recipient_title": {"last_name": "Колодруб", "first_name": "Михайло", "second_name": "Юрійович"},
                "recipient_phone": "380500345025", "comment": "",
                "delivery": {"delivery_service_name": "Нова Пошта", "city": {"name_ua": "Кременчук"}, "place_number": "19", "place_street": "просп. Лесі Українки, 54А"},
                "purchases": [{"item_name": cream.name, "quantity": 1, "price": "3899.00", "item": {"article": "CREAM-1"}}],
                "payment": {"payment_method_name": "Google Pay", "payment_status": "paid"}}], "_meta": {"pageCount": 1}}})
        if u.startswith("https://api-seller.rozetka.com.ua/orders/905850113") and req.method == "PUT":
            return httpx.Response(200, json={"success": True, "content": {}})
        if "/orders/list" in u:
            return httpx.Response(200, json={"orders": [{"id": 777, "status": "pending", "client_first_name": "Оля", "client_last_name": "Коваль",
                "phone": "+380671112233", "full_price": "499 грн", "delivery_option": {"name": "Нова Пошта"},
                "delivery_provider_data": {"declaration_number": ""}, "payment_option": {"name": "Пром-оплата"},
                "products": [{"name": "Невідомий товар", "sku": "", "price": "499", "quantity": 1}]}]})
        if "/orders/set_status" in u:
            return httpx.Response(200, json={"processed_ids": [777]})
        return httpx.Response(404, json={"success": False, "errors": {"message": "not found"}})

    monkeypatch.setattr(mp, "_client", httpx.Client(transport=httpx.MockTransport(handler)))
    s = api.put("/api/settings/dir/offices", json=[{"name": "PROM"}]).json()
    prom_office = s["offices"][0]["id"]
    s = api.put("/api/settings/shops", json=[
        {"kind": "rozetka", "name": "Antony_store", "login": "seller", "secret": "pass", "status_map": {str(sid(db, "shipped")): "3"}},
        {"kind": "prom", "name": "PROM", "secret": "PROMTOKEN", "office_id": prom_office, "status_map": {str(sid(db, "cancelled")): "canceled"}},
    ]).json()
    roz, prom = s["shops"]
    assert roz["secret"] == "********"
    chk = api.post(f"/api/settings/shops/{roz['id']}/check").json()
    assert chk["statuses"]["3"] == "Переданий в службу доставки" and chk["sample_parsed"]["last_name"] == "Колодруб"

    r = api.post(f"/api/settings/shops/{roz['id']}/sync").json()
    assert r == {"new": 1, "updated": 0, "seen": 1, "error": ""}
    assert api.post(f"/api/settings/shops/{roz['id']}/sync").json()["new"] == 0  # повторно не дублює
    o = db.query(Order).filter(Order.external_id == "905850113").one()
    assert (o.last_name, o.first_name, o.middle_name) == ("Колодруб", "Михайло", "Юрійович")
    assert o.ttn == "20451534560757" and o.payment_method_id == 14 and o.items[0].product_id == cream.id
    assert o.extra1 == "Rozetka(Antony_store)" and o.source.name == "Маркетплейси"
    # статус «Відправлено» в CRM → «3» на Rozetka
    o2 = api.patch(f"/api/orders/{o.id}", json={"status_id": sid(db, "shipped"), "version": api.get(f"/api/orders/{o.id}").json()["version"]}).json()
    assert o2["external_status"] == "3"
    put = [c for c in calls if c[0] == "PUT"][-1]
    assert '"status": 3' in put[2] or '"status":3' in put[2]

    r = api.post(f"/api/settings/shops/{prom['id']}/sync").json()
    assert r["new"] == 1
    po = db.query(Order).filter(Order.external_id == "777").one()
    assert po.office_id == prom_office and po.payment_method_id == 10 and po.items[0].product_id is None
    assert po.total == 499


# ------------------------------------------------------------------ Checkbox (етап 4)
def test_checkbox_cashiers_and_receipts(api, db, products, monkeypatch):
    import json as _json
    import httpx
    from app.services import checkbox as cb
    sent = []

    def handler(req: httpx.Request):
        u = str(req.url)
        if u.endswith("/cashier/signin"):
            return httpx.Response(200, json={"access_token": "CBTOKEN"})
        if u.endswith("/cashier/shift"):
            return httpx.Response(200, json={"id": "sh1", "status": "CLOSED"})
        if u.endswith("/shifts") and req.method == "POST":
            return httpx.Response(202, json={"id": "sh1", "status": "OPENED"})
        if u.endswith("/receipts/sell"):
            body = _json.loads(req.content)
            sent.append((req.headers.get("X-License-Key"), body))
            return httpx.Response(201, json={"id": body["id"], "status": "DONE", "fiscal_code": f"FC-{len(sent)}"})
        return httpx.Response(404, json={"message": "not found"})

    monkeypatch.setattr(cb, "_client", httpx.Client(transport=httpx.MockTransport(handler)))
    offices = api.put("/api/settings/dir/offices", json=[{"name": "ФОП А"}, {"name": "ФОП Б"}]).json()["offices"]
    fa, fb = offices[0]["id"], offices[1]["id"]
    s = api.put("/api/settings/checkbox-cashiers", json=[
        {"name": "Касир А", "license_key": "LIC-A", "login": "a", "password": "pa", "condition": "office", "condition_value": fa},
        {"name": "Касир Б", "license_key": "LIC-B", "login": "b", "password": "pb", "condition": "office", "condition_value": fb},
    ]).json()
    assert [c["license_key"] for c in s["cashiers"]] == ["********", "********"]
    assert api.post(f"/api/settings/checkbox-cashiers/{s['cashiers'][0]['id']}/check").json()["shift"] == "CLOSED"

    # ручний чек: каса за відділом, тип оплати з виду оплати (Післяплата Rozetka → RozetkaPay)
    o = new_order(api, products, office_id=fb, payment_method_id=15, discount="47")
    o = api.post(f"/api/orders/{o['id']}/receipts", json={"kind": "sell"}).json()
    assert o["receipts"][0]["status"] == "done" and o["receipts"][0]["cashier"] == "Касир Б" and o["receipts"][0]["total"] == 850
    lic, body = sent[-1]
    assert lic == "LIC-B" and body["payments"][0]["type"] == "CASHLESS" and "RozetkaPay" in body["payments"][0]["label"]
    assert body["goods"][0]["quantity"] == 2000 and body["goods"][0]["good"]["price"] == 39900
    assert body["discounts"][0]["value"] == 4700 and o["receipts"][0]["url"].endswith(body["id"])
    assert api.post(f"/api/orders/{o['id']}/receipts", json={"kind": "sell"}).status_code == 422  # другий чек продажу — ні

    # автоматичний чек при статусі «Відправлено», повернення — з is_return
    api.put("/api/settings/checkbox", json={"cb_sell_status": str(sid(db, "shipped"))})
    o2 = new_order(api, products, office_id=fa, payment_method_id=9)
    o2 = api.patch(f"/api/orders/{o2['id']}", json={"status_id": sid(db, "shipped"), "version": o2["version"]}).json()
    assert sent[-1][0] == "LIC-A" and sent[-1][1]["payments"][0]["type"] == "CASH"
    assert api.get(f"/api/orders/{o2['id']}").json()["receipts"][0]["kind"] == "sell"
    api.post(f"/api/orders/{o2['id']}/receipts", json={"kind": "return"})
    assert all(g["is_return"] for g in sent[-1][1]["goods"])


def test_stats_main_vs_upsell(api, db, products):
    cream, soap = products
    new_order(api, products)  # крем ×2 (основний) + мило ×1 (допродаж)
    new_order(api, products, items=[{"product_id": cream.id, "name": cream.name, "qty": 1, "price": 399}])
    r = api.get("/api/stats?date_field=created").json()
    s = r["summary"]
    assert s["orders"] == 2 and s["orders_upsell"] == 1 and s["upsell_rate"] == 50
    assert s["qty_main"] == 3 and s["qty_upsell"] == 1 and s["sum_upsell"] == 99 and s["sum_main"] == 1197
    assert s["margin_upsell"] == 99 - 30 and r["days"][-1]["total"] == 2
    top = r["products"][0]
    assert top["product_id"] == cream.id and top["qty_main"] == 3
    assert api.get(f"/api/stats?product={soap.id}").json()["summary"]["orders"] == 1
