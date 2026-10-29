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
    cream, soap = products
    data = {
        "customer_name": "Шевченко Тарас", "phone": "0501112233", "delivery_method": "novaposhta",
        "city_name": "Київ", "city_ref": "city-ref", "warehouse_name": "Відділення №1", "warehouse_ref": "wh-ref",
        "payment_type": "cod", "discount": "", "prepayment": "", "items_present": "1",
        "item_product_id": [str(cream.id), str(soap.id)], "item_name": [cream.name, soap.name],
        "item_qty": ["2", "1"], "item_price": ["399", "99"], "item_upsell": ["0", "1"],
    }
    data.update(over)
    return data


def create_via_ui(client, products, **over) -> int:
    r = client.post("/orders/new", data=order_form(products, **over), follow_redirects=False)
    assert r.status_code == 303, r.text
    return int(r.headers["location"].rsplit("/", 1)[1])


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
    admin.post(f"/orders/{oid}", data={**order_form(products, discount="47"), "status_id": status_id(db, "confirmed")})
    cream, soap = fresh(db, cream), fresh(db, soap)
    assert (cream.stock, cream.reserved) == (10, 2) and (soap.stock, soap.reserved) == (50, 1)

    # Зміна кількості після резерву — резерв коригується
    form = order_form(products, discount="47", item_qty=["3", "1"])
    admin.post(f"/orders/{oid}", data=form)
    assert fresh(db, cream).reserved == 3

    # Відправка — списання і очікуваний накладений платіж
    admin.post(f"/orders/{oid}", data={**form, "status_id": status_id(db, "shipped")})
    cream = fresh(db, cream)
    assert (cream.stock, cream.reserved) == (7, 0)
    o = fresh(db, db.get(Order, oid))
    assert o.stock_shipped and not o.stock_reserved
    cod = [p for p in o.payments if p.kind == "cod"]
    assert len(cod) == 1 and cod[0].status == "expected" and cod[0].amount == Decimal("1249")

    # Повторна установка того ж статусу нічого не дублює
    admin.post(f"/orders/{oid}", data={**form, "status_id": status_id(db, "delivered")})
    admin.post(f"/orders/{oid}", data={**form, "status_id": status_id(db, "delivered")})
    assert fresh(db, cream).stock == 7
    o = fresh(db, db.get(Order, oid))
    assert [p.status for p in o.payments] == ["collected"]


def test_refusal_returns_stock_and_cancels_cod(admin, db, products):
    cream, _ = products
    oid = create_via_ui(admin, products, status_id=str(status_id(db, "shipped")))
    assert fresh(db, cream).stock == 8
    form = order_form(products)
    admin.post(f"/orders/{oid}", data={**form, "status_id": status_id(db, "refused")})
    o = fresh(db, db.get(Order, oid))
    assert o.payments[0].status == "cancelled"
    assert fresh(db, cream).stock == 8  # ще в дорозі назад
    admin.post(f"/orders/{oid}", data={**form, "status_id": status_id(db, "returned")})
    assert fresh(db, cream).stock == 10


def test_cancel_releases_reserve(admin, db, products):
    cream, _ = products
    oid = create_via_ui(admin, products, status_id=str(status_id(db, "confirmed")))
    assert fresh(db, cream).reserved == 2
    admin.post(f"/orders/{oid}", data={**order_form(products), "status_id": status_id(db, "cancelled")})
    assert fresh(db, cream).reserved == 0 and fresh(db, cream).stock == 10


def test_prepayment_changes_cod(admin, db, products):
    oid = create_via_ui(admin, products)
    admin.post(f"/orders/{oid}/payment", data={"amount": "200", "method": "card"})
    o = fresh(db, db.get(Order, oid))
    assert o.payment_type == "partial" and o.prepayment == Decimal("200") and o.cod_amount == Decimal("697")
    admin.post(f"/orders/{oid}/payment", data={"amount": "697", "method": "card"})
    o = fresh(db, db.get(Order, oid))
    assert o.payment_type == "prepaid" and o.cod_amount == 0


def test_concurrent_edit_protection(admin, db, products):
    oid = create_via_ui(admin, products)
    r = admin.post(f"/orders/{oid}", data={**order_form(products), "customer_name": "Інше Ім'я",
                                           "version": "2000-01-01T00:00:00"})
    assert r.status_code == 200
    assert fresh(db, db.get(Order, oid)).customer_name == "Шевченко Тарас"


def test_history_is_logged(admin, db, products):
    oid = create_via_ui(admin, products)
    admin.post(f"/orders/{oid}", data={**order_form(products), "customer_name": "Нове Ім'я",
                                       "status_id": status_id(db, "callback")})
    actions = [a.action for a in db.query(AuditLog).filter(AuditLog.entity == "order", AuditLog.entity_id == oid)]
    assert {"create", "update", "status"} <= set(actions)
    page = admin.get(f"/orders/{oid}").text
    assert "Нове Ім&#39;я" in page or "Нове Ім'я" in page


def test_manager_own_only_visibility(manager, db, products):
    st.set_value(db, "managers_see_own_only", "1")
    other = db.query(User).filter(User.username == "manager2").one()
    cream, _ = products
    o = Order(status_id=status_id(db, "new"), phone="380991112233", manager_id=other.id, customer_name="Чужий")
    db.add(o)
    db.commit()
    assert manager.get(f"/orders/{o.id}").status_code == 403
    assert "Чужий" not in manager.get("/orders").text


def test_bulk_status_and_search(admin, db, products, webhook_key):
    ids = [admin.post(f"/api/v1/orders?key={webhook_key}", data={"phone": f"06712345{i:02d}", "sku": "CREAM-1"})
           .json()["order_id"] for i in range(3)]
    admin.post("/orders/bulk", data={"ids": [str(i) for i in ids[:2]], "action": f"status:{status_id(db, 'confirmed')}"})
    db.expire_all()
    assert [db.get(Order, i).status.code for i in ids] == ["confirmed", "confirmed", "new"]
    assert db.get(Product, products[0].id).reserved == 2
    page = admin.get("/orders?q=0671234502").text
    assert f"/orders/{ids[2]}" in page and f"/orders/{ids[0]}\"" not in page


def test_csv_export(admin, products, webhook_key):
    admin.post(f"/api/v1/orders?key={webhook_key}", data={"name": "Експорт Тест", "phone": "0671112233", "sku": "CREAM-1"})
    r = admin.get("/orders/export.csv")
    assert r.status_code == 200 and "Експорт Тест" in r.text
