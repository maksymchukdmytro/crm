from decimal import Decimal

from app.models import AuditLog, Order, Product, Status, User
from app.services import settings as st
from app.services.orders import normalize_phone


def status_id(db, code):
    return db.query(Status).filter(Status.code == code).one().id


def fresh(db, obj):
    db.expire_all()
    return db.get(type(obj), obj.id)


def test_normalize_phone():
    assert normalize_phone("067 123-45-67") == "380671234567"
    assert normalize_phone("+38 (067) 123 45 67") == "380671234567"
    assert normalize_phone("671234567") == "380671234567"
    assert normalize_phone("80671234567") == "380671234567"


def test_webhook_creates_order(anon, db, products, webhook_key):
    r = anon.post(f"/api/v1/orders?key={webhook_key}", data={
        "name": "Петренко Іван", "phone": "(067) 123-45-67", "sku": "CREAM-1", "qty": "2",
        "utm_source": "facebook", "utm_campaign": "spring", "site": "cream-landing",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] and not body["duplicate"]
    o = db.get(Order, body["order_id"])
    assert o.phone == "380671234567"
    assert o.status.code == "new"
    assert o.utm_source == "facebook" and o.site == "cream-landing"
    assert len(o.items) == 1 and o.items[0].qty == 2
    assert o.total == Decimal("798.00") and o.cod_amount == Decimal("798.00")
    assert r.headers["access-control-allow-origin"] == "*"


def test_webhook_multiple_products_and_duplicate(anon, db, products, webhook_key):
    payload = {"name": "Іван", "phone": "0671234567",
               "products": [{"sku": "CREAM-1", "qty": 1}, {"sku": "SOAP-1", "qty": 3, "price": 79}]}
    r1 = anon.post(f"/api/v1/orders?key={webhook_key}", json=payload).json()
    r2 = anon.post(f"/api/v1/orders?key={webhook_key}", json=payload).json()
    assert not r1["duplicate"] and r2["duplicate"]
    o = db.get(Order, r1["order_id"])
    assert o.total == Decimal("399") + Decimal("79") * 3
    assert db.get(Order, r2["order_id"]).duplicate_of_id == r1["order_id"]


def test_webhook_rejects_bad_key_and_phone(anon, webhook_key):
    assert anon.post("/api/v1/orders?key=wrong", data={"phone": "0671234567"}).status_code == 403
    assert anon.post(f"/api/v1/orders?key={webhook_key}", data={"phone": "12"}).status_code == 422


def test_webhook_redirect_for_html_forms(anon, webhook_key):
    r = anon.post(f"/api/v1/orders?key={webhook_key}",
                  data={"phone": "0671234567", "redirect": "https://shop.example/thanks"}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "https://shop.example/thanks"


def test_round_robin_assignment(anon, db, webhook_key):
    st.set_value(db, "auto_assign", "round_robin")
    db.commit()
    ids = [anon.post(f"/api/v1/orders?key={webhook_key}", data={"phone": f"067123450{i}"}).json()["order_id"]
           for i in range(4)]
    db.expire_all()
    managers = [db.get(Order, i).manager.username for i in ids]
    assert managers == ["manager1", "manager2", "manager1", "manager2"]


def order_form(products, **over):
    """Тіло POST/PATCH /api/orders: 2 креми + мило допродажем."""
    cream, soap = products
    data = {
        "customer_name": "Шевченко Тарас", "phone": "0501112233", "delivery_method": "novaposhta",
        "city_name": "Київ", "city_ref": "city-ref", "warehouse_name": "Відділення №1", "warehouse_ref": "wh-ref",
        "payment_type": "cod", "discount": "", "prepayment": "",
        "items": [{"product_id": cream.id, "name": cream.name, "qty": 2, "price": "399", "upsell": False},
                  {"product_id": soap.id, "name": soap.name, "qty": 1, "price": "99", "upsell": True}],
    }
    if "item_qty" in over:
        for it, q in zip(data["items"], over.pop("item_qty")):
            it["qty"] = int(q)
    data.update(over)
    return data


def create_via_ui(client, products, **over) -> int:
    r = client.post("/api/orders", json=order_form(products, **over))
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_manual_order_assigned_to_manager(manager, db, products):
    oid = create_via_ui(manager, products)
    o = db.get(Order, oid)
    assert o.manager.username == "manager1"
    assert o.total == Decimal("897") and [i.is_upsell for i in o.items] == [False, True]


def test_full_lifecycle_stock_and_payments(admin, db, products):
    cream, soap = products
    oid = create_via_ui(admin, products, discount="47")
    o = db.get(Order, oid)
    assert o.total == Decimal("850") and o.cod_amount == Decimal("850")

    # Підтвердження — резерв
    admin.patch(f"/api/orders/{oid}", json={**order_form(products, discount="47"), "status_id": status_id(db, "confirmed")})
    cream, soap = fresh(db, cream), fresh(db, soap)
    assert (cream.stock, cream.reserved) == (10, 2) and (soap.stock, soap.reserved) == (50, 1)

    # Зміна кількості після резерву — резерв коригується
    form = order_form(products, discount="47", item_qty=["3", "1"])
    admin.patch(f"/api/orders/{oid}", json=form)
    assert fresh(db, cream).reserved == 3

    # Відправка — списання і очікуваний накладений платіж
    admin.patch(f"/api/orders/{oid}", json={**form, "status_id": status_id(db, "shipped")})
    cream = fresh(db, cream)
    assert (cream.stock, cream.reserved) == (7, 0)
    o = fresh(db, db.get(Order, oid))
    assert o.stock_shipped and not o.stock_reserved
    cod = [p for p in o.payments if p.kind == "cod"]
    assert len(cod) == 1 and cod[0].status == "expected" and cod[0].amount == Decimal("1249")

    # Повторна установка того ж статусу нічого не дублює
    admin.patch(f"/api/orders/{oid}", json={**form, "status_id": status_id(db, "delivered")})
    admin.patch(f"/api/orders/{oid}", json={**form, "status_id": status_id(db, "delivered")})
    assert fresh(db, cream).stock == 7
    o = fresh(db, db.get(Order, oid))
    assert [p.status for p in o.payments] == ["collected"]


def test_refusal_returns_stock_and_cancels_cod(admin, db, products):
    cream, _ = products
    oid = create_via_ui(admin, products, status_id=status_id(db, "shipped"))
    assert fresh(db, cream).stock == 8
    form = order_form(products)
    admin.patch(f"/api/orders/{oid}", json={**form, "status_id": status_id(db, "refused")})
    o = fresh(db, db.get(Order, oid))
    assert o.payments[0].status == "cancelled"
    assert fresh(db, cream).stock == 8  # ще в дорозі назад
    admin.patch(f"/api/orders/{oid}", json={**form, "status_id": status_id(db, "returned")})
    assert fresh(db, cream).stock == 10


def test_cancel_releases_reserve(admin, db, products):
    cream, _ = products
    oid = create_via_ui(admin, products, status_id=status_id(db, "confirmed"))
    assert fresh(db, cream).reserved == 2
    from app.models import StatusReason
    reason = db.query(StatusReason).first()
    body = {**order_form(products), "status_id": status_id(db, "cancelled"), **({"reason_id": reason.id} if reason else {})}
    r = admin.patch(f"/api/orders/{oid}", json=body)
    assert r.status_code == 200, r.text
    assert fresh(db, cream).reserved == 0 and fresh(db, cream).stock == 10


def test_prepayment_changes_cod(admin, db, products):
    oid = create_via_ui(admin, products)
    admin.post(f"/api/orders/{oid}/payments", json={"amount": "200", "method": "card"})
    o = fresh(db, db.get(Order, oid))
    assert o.payment_type == "partial" and o.prepayment == Decimal("200") and o.cod_amount == Decimal("697")
    admin.post(f"/api/orders/{oid}/payments", json={"amount": "697", "method": "card"})
    o = fresh(db, db.get(Order, oid))
    assert o.payment_type == "prepaid" and o.cod_amount == 0


def test_concurrent_edit_protection(admin, db, products):
    oid = create_via_ui(admin, products)
    r = admin.patch(f"/api/orders/{oid}", json={**order_form(products), "customer_name": "Інше Ім'я", "version": "2000-01-01T00:00:00"})
    assert r.status_code == 409
    assert fresh(db, db.get(Order, oid)).customer_name == "Шевченко Тарас"


def test_history_is_logged(admin, db, products):
    oid = create_via_ui(admin, products)
    admin.patch(f"/api/orders/{oid}", json={**order_form(products), "customer_name": "Нове Ім'я", "status_id": status_id(db, "callback")})
    actions = [a.action for a in db.query(AuditLog).filter(AuditLog.entity == "order", AuditLog.entity_id == oid)]
    assert {"create", "update", "status"} <= set(actions)
    assert admin.get(f"/api/orders/{oid}").json()["customer_name"] == "Нове Ім'я"
    assert admin.get(f"/api/orders/{oid}/history").json()["events"]


def test_manager_own_only_visibility(manager, db, products):
    st.set_value(db, "managers_see_own_only", "1")
    other = db.query(User).filter(User.username == "manager2").one()
    o = Order(status_id=status_id(db, "new"), phone="380991112233", manager_id=other.id, customer_name="Чужий")
    db.add(o)
    db.commit()
    assert manager.get(f"/api/orders/{o.id}").status_code == 403
    assert all(r["customer_name"] != "Чужий" for r in manager.get("/api/orders?stage=lead").json()["items"])


def test_bulk_status_and_search(admin, db, products, webhook_key):
    ids = [admin.post(f"/api/v1/orders?key={webhook_key}", data={"phone": f"06712345{i:02d}", "sku": "CREAM-1"})
           .json()["order_id"] for i in range(3)]
    admin.post("/api/orders/bulk", json={"ids": ids[:2], "action": "status", "value": status_id(db, "confirmed")})
    db.expire_all()
    assert [db.get(Order, i).status.code for i in ids] == ["confirmed", "confirmed", "new"]
    assert db.get(Product, products[0].id).reserved == 2
    found = [r["id"] for r in admin.get("/api/orders?q=0671234502").json()["items"]]
    assert found == [ids[2]]


def test_csv_export(admin, products, webhook_key):
    admin.post(f"/api/v1/orders?key={webhook_key}", data={"name": "Експорт Тест", "phone": "0671112233", "sku": "CREAM-1"})
    r = admin.get("/api/orders/export.csv")
    assert r.status_code == 200 and "Експорт Тест" in r.text


def test_duplicate_only_when_items_and_total_match(anon, db, products, webhook_key):
    """Той самий телефон з іншим товаром — повторний покупець, а не дубль."""
    url = f"/api/v1/orders?key={webhook_key}"
    r1 = anon.post(url, json={"name": "Олег", "phone": "0679998877", "products": [{"sku": "CREAM-1", "qty": 1}]}).json()
    r2 = anon.post(url, json={"name": "Олег", "phone": "0679998877", "products": [{"sku": "SOAP-1", "qty": 1}]}).json()
    r3 = anon.post(url, json={"name": "Олег", "phone": "0679998877", "products": [{"sku": "CREAM-1", "qty": 2}]}).json()
    r4 = anon.post(url, json={"name": "Олег", "phone": "0679998877", "products": [{"sku": "CREAM-1", "qty": 1}]}).json()
    assert not r2["duplicate"] and not r3["duplicate"]
    assert r4["duplicate"] and db.get(Order, r4["order_id"]).duplicate_of_id == r1["order_id"]
