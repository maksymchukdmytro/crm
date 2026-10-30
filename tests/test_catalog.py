"""Етап 6: категорії, виробники, атрибути й варіанти зі складом, фото, акційна ціна; покупці, групи, чорний список, IP."""
import base64

from app.config import config
from app.models import Customer, Order, Product, ProductVariant, StockMovement, Status

from .test_api import api, api_manager, new_order, sid  # noqa: F401 — фікстури

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")


def test_categories_two_levels_and_filters(api, db, products):
    cream, soap = products
    cats = api.post("/api/catalog/categories", json={"name": "Догляд"}).json()
    root = cats[0]["id"]
    cats = api.post("/api/catalog/categories", json={"name": "Руки", "parent_id": root}).json()
    sub = next(c for c in cats if c["name"] == "Руки")["id"]
    r = api.post("/api/catalog/categories", json={"name": "Глибше", "parent_id": sub})
    assert r.status_code == 400  # лише два рівні
    api.patch(f"/api/products/{cream.id}", json={"category_id": sub})
    assert [p["id"] for p in api.get(f"/api/products?category={root}").json()] == [cream.id]  # разом із підкатегоріями
    assert {p["id"] for p in api.get("/api/products?category=-1").json()} == {soap.id}
    assert next(c for c in api.get("/api/catalog/categories").json() if c["id"] == sub)["products"] == 1
    # статистика за категорією
    new_order(api, products)
    new_order(api, products, items=[{"product_id": soap.id, "name": soap.name, "qty": 1, "price": 99}], phone="0509990000")
    assert api.get(f"/api/stats?category={root}").json()["summary"]["orders"] == 1
    assert api.get("/api/meta").json()["categories"][0]["name"] in ("Догляд", "Руки")
    # видалення розділу: підкатегорія піднімається нагору, товари лишаються
    cats = api.delete(f"/api/catalog/categories/{root}").json()
    assert next(c for c in cats if c["id"] == sub)["parent_id"] is None


def test_manufacturers(api, db, products):
    cream, _ = products
    m = api.post("/api/catalog/manufacturers", json={"name": "Ulanzi"}).json()[0]
    assert api.post("/api/catalog/manufacturers", json={"name": "ulanzi"}).status_code == 409
    p = api.patch(f"/api/products/{cream.id}", json={"manufacturer_id": m["id"], "model": "VL49",
                                                     "countries": ["ua", "pl", "xx"]}).json()
    assert p["manufacturer_id"] == m["id"] and p["model"] == "VL49" and p["countries"] == ["PL", "UA"]
    assert api.get(f"/api/products?manufacturer={m['id']}").json()[0]["id"] == cream.id
    api.delete(f"/api/catalog/manufacturers/{m['id']}")
    db.expire_all()
    assert db.get(Product, cream.id).manufacturer_id is None


def test_sale_price_and_photos(api, db, products, tmp_path, monkeypatch):
    cream, _ = products
    p = api.patch(f"/api/products/{cream.id}", json={"spec_price": 299, "wholesale_price": 250, "description": "Опис"}).json()
    assert p["sale_price"] == 299 and p["discount_percent"] == 25 and p["wholesale_price"] == 250
    o = api.post("/api/orders", json={"phone": "0501110001", "items": [{"product_id": cream.id, "qty": 1}]}).json()
    assert o["items"][0]["price"] == 299  # акційна ціна за замовчуванням
    monkeypatch.setattr(config, "MEDIA_DIR", str(tmp_path))
    files = [("files", ("a.png", PNG, "image/png")), ("files", ("b.png", PNG, "image/png"))]
    photos = api.post(f"/api/products/{cream.id}/photos", files=files, headers={"X-CRM": "1"}).json()
    assert len(photos) == 2 and photos[0]["url"].startswith("/media/products/")
    assert api.get(photos[0]["url"]).content == PNG
    assert "class Config" not in api.get("/media/%2e%2e/%2e%2e/app/config.py").text
    bad = api.post(f"/api/products/{cream.id}/photos", files=[("files", ("x.txt", b"hi", "text/plain"))])
    assert bad.status_code == 400
    order = api.put(f"/api/products/{cream.id}/photos", json=[photos[1]["id"], photos[0]["id"]]).json()
    assert order[0]["id"] == photos[1]["id"]
    assert api.get(f"/api/products/{cream.id}").json()["photo"] == photos[1]["url"]
    left = api.delete(f"/api/products/{cream.id}/photos/{photos[1]['id']}").json()
    assert len(left) == 1 and len(list(tmp_path.joinpath("products").iterdir())) == 1
    assert api.get(f"/api/products/{cream.id}").json()["description"] == "Опис"


def test_attributes_variants_and_stock(api, db, products):
    groups = api.post("/api/catalog/attribute-groups", json={"name": "Колір"}).json()
    gid = groups[0]["id"]
    api.post("/api/catalog/attributes", json={"group_id": gid, "name": "Чорний"})
    groups = api.post("/api/catalog/attributes", json={"group_id": gid, "name": "Білий"}).json()
    black, white = [a["id"] for a in groups[0]["attributes"]]
    p = api.post("/api/products", json={"name": "Лампа", "price": 1000, "cost": 600, "variants": [
        {"attribute_ids": [black], "initial_stock": 5, "sku": "LAMP-B"},
        {"attribute_ids": [white], "initial_stock": 3, "price": 1100}]}).json()
    assert [v["name"] for v in p["variants"]] == ["Чорний", "Білий"] and p["stock"] == 8
    vb, vw = p["variants"]
    # замовлення з варіантом: ціна варіанта, резерв і списання по варіанту
    o = api.post("/api/orders", json={"phone": "0501110002", "items": [{"product_id": p["id"], "variant_id": vw["id"], "qty": 2}]}).json()
    assert o["items"][0]["price"] == 1100 and o["items"][0]["name"] == "Лампа (Білий)"
    api.patch(f"/api/orders/{o['id']}", json={"status_id": sid(db, "confirmed")})
    db.expire_all()
    w = db.get(ProductVariant, vw["id"])
    assert w.reserved == 2 and db.get(Product, p["id"]).reserved == 2
    api.patch(f"/api/orders/{o['id']}", json={"status_id": sid(db, "shipped")})
    db.expire_all()
    assert db.get(ProductVariant, vw["id"]).stock == 1 and db.get(ProductVariant, vw["id"]).reserved == 0
    assert db.get(Product, p["id"]).stock == 6
    assert db.query(StockMovement).filter(StockMovement.variant_id == vw["id"], StockMovement.kind == "ship").count() == 1
    # артикул варіанта в заявці з лендингу
    key = api.get("/api/settings").json()["values"].get("webhook_key")
    r = api.post(f"/api/v1/orders?key={key}", data={"phone": "0671234500", "sku": "LAMP-B"})
    oid = r.json()["order_id"]
    item = db.get(Order, oid).items[0]
    assert item.variant_id == vb["id"] and item.product_id == p["id"]
    # коригування: товару з варіантами — лише по варіанту
    assert api.post("/api/warehouse/adjust", json={"product_id": p["id"], "qty": 10}).status_code == 400
    api.post("/api/warehouse/adjust", json={"product_id": p["id"], "variant_id": vb["id"], "qty": 9})
    db.expire_all()
    assert db.get(ProductVariant, vb["id"]).stock == 9 and db.get(Product, p["id"]).stock == 10
    # варіант, що вже продавався, при видаленні лише вимикається; новий без історії — видаляється
    p2 = api.patch(f"/api/products/{p['id']}", json={"variants": [{"id": vb["id"], "attribute_ids": [black]},
                                                                  {"name": "Сірий"}]}).json()
    names = {v["name"]: v["active"] for v in p2["variants"]}
    assert names == {"Чорний": True, "Білий": False, "Сірий": True}
    p3 = api.patch(f"/api/products/{p['id']}", json={"variants": [{"id": vb["id"], "attribute_ids": [black]}]}).json()
    assert "Сірий" not in {v["name"] for v in p3["variants"]}
    assert api.patch(f"/api/products/{p['id']}", json={"variants": [{"name": "А"}, {"name": "а"}]}).status_code == 400
    # атрибут у варіантах при видаленні лише вимикається
    groups = api.delete(f"/api/catalog/attributes/{black}").json()
    assert next(a for a in groups[0]["attributes"] if a["id"] == black)["active"] is False


def test_customers_stats_blacklist_and_groups(api, api_manager, db, products):
    a = new_order(api, products, phone="0501230001", customer_name="Іваненко Ольга", email="olga@example.com")
    b = new_order(api, products, phone="0501230001")
    new_order(api, products, phone="0501230002", customer_name="Петренко Іван")
    c = db.query(Customer).filter(Customer.phone == "380501230001").one()
    assert c.name == "Іваненко Ольга" and c.email == "olga@example.com" and c.group is not None
    delivered = db.query(Status).filter(Status.code == "delivered").one()
    refused = db.query(Status).filter(Status.code == "refused").one()
    db.get(Order, a["id"]).status_id = delivered.id
    db.get(Order, b["id"]).status_id = refused.id
    db.commit()
    rows = api.get("/api/customers?sort=sum").json()["rows"]
    top = rows[0]
    assert top["id"] == c.id and top["orders"] == 2 and top["delivered"] == 1 and top["refused"] == 1 and top["buyout_rate"] == 50
    assert top["sum_delivered"] == a["total"]
    assert api.get("/api/customers?q=Петренко").json()["total"] == 1
    assert api.get("/api/customers?q=1230001").json()["rows"][0]["id"] == c.id
    # картка з історією
    d = api.get(f"/api/customers/{c.id}").json()
    assert {o["id"] for o in d["history"]} == {a["id"], b["id"]}
    # чорний список: позначка в замовленнях і фільтр
    groups = api.get("/api/customer-groups").json()
    opt = next(g for g in groups if g["name"] == "Оптовик")
    d = api.patch(f"/api/customers/{c.id}", json={"blacklisted": True, "blacklist_reason": "Не забирає посилки",
                                                  "group_id": opt["id"], "comment": "Дзвонити з 10:00"}).json()
    assert d["blacklisted"] and d["group"] == "Оптовик"
    assert api.get("/api/customers?blacklist=1").json()["total"] == 1
    card = api.get(f"/api/orders/{a['id']}").json()
    assert card["customer"]["blacklisted"] and card["customer"]["blacklist_reason"] == "Не забирає посилки"
    assert card["customer"]["orders"] == 2
    lst = {o["id"]: o for o in api.get("/api/orders").json()["items"]}
    assert lst[a["id"]]["blacklisted"] and not any(o["blacklisted"] for i, o in lst.items() if i not in (a["id"], b["id"]))
    # ручне редагування не перезаписується наступним замовленням
    api.patch(f"/api/customers/{c.id}", json={"name": "Ольга (опт)"})
    new_order(api, products, phone="0501230001", customer_name="Хтось Інший")
    db.expire_all()
    assert db.get(Customer, c.id).name == "Ольга (опт)"
    # зміна телефону в замовленні переносить його до іншого покупця
    api.patch(f"/api/orders/{b['id']}", json={"phone": "0509998877"})
    db.expire_all()
    assert db.get(Order, b["id"]).customer.phone == "380509998877"
    # новий покупець вручну підхоплює наявні замовлення з його телефоном
    db.get(Order, b["id"]).customer_id = None
    db.query(Customer).filter(Customer.phone == "380509998877").delete()
    db.commit()
    nc = api.post("/api/customers", json={"phone": "050 999 88 77", "name": "Новий"}).json()
    assert {o["id"] for o in nc["history"]} == {b["id"]}
    assert api.post("/api/customers", json={"phone": "0509998877"}).status_code == 409
    # групи редагує лише адміністратор
    assert api_manager.post("/api/customer-groups", json={"name": "VIP"}).status_code == 403
    groups = api.post("/api/customer-groups", json={"name": "VIP", "color": "#ff0000"}).json()
    vip = next(g for g in groups if g["name"] == "VIP")
    api.delete(f"/api/customer-groups/{opt['id']}")
    db.expire_all()
    assert db.get(Customer, c.id).group_id is None and vip["customers"] == 0


def test_blocked_ip_rejects_webhook(api, db, products, webhook_key):
    ips = api.post("/api/blocked-ips", json={"ip": "testclient", "comment": "x"})
    assert ips.status_code == 400  # некоректна адреса
    api.post("/api/blocked-ips", json={"ip": "10.1.2.3", "comment": "спам"})
    r = api.post(f"/api/v1/orders?key={webhook_key}", data={"phone": "0671112233"}, headers={"X-Forwarded-For": "10.1.2.3"})
    assert r.status_code == 403
    r = api.post(f"/api/v1/orders?key={webhook_key}", data={"phone": "0671112233"}, headers={"X-Forwarded-For": "10.1.2.4"})
    assert r.status_code == 200
    bid = api.get("/api/blocked-ips").json()[0]["id"]
    assert api.delete(f"/api/blocked-ips/{bid}").json() == []


def test_product_delete_or_archive(api, db, products):
    cream, soap = products
    new_order(api, products, items=[{"product_id": cream.id, "name": cream.name, "qty": 1, "price": 399}])
    r = api.delete(f"/api/products/{cream.id}").json()
    assert r["deleted"] is False and "архів" in r["message"]
    db.expire_all()
    assert db.get(Product, cream.id).is_active is False
    soap_id = soap.id
    r = api.delete(f"/api/products/{soap_id}").json()
    db.expire_all()
    assert r["deleted"] is True and db.query(Product).filter(Product.id == soap_id).first() is None


def test_leads_and_orders_sections(api, db, products, webhook_key):
    a = new_order(api, products, phone="0501110010", status_id=sid(db, "new"))  # лід
    b = new_order(api, products, phone="0501110011")
    api.patch(f"/api/orders/{b['id']}", json={"status_id": sid(db, "confirmed")})
    leads = {o["id"] for o in api.get("/api/orders?stage=lead").json()["items"]}
    orders = {o["id"] for o in api.get("/api/orders?stage=order").json()["items"]}
    assert leads == {a["id"]} and orders == {b["id"]}
    st = {s["code"]: s["stage"] for s in api.get("/api/meta").json()["statuses"]}
    assert st["new"] == st["no_answer"] == st["callback"] == "lead" and st["shipped"] == "order"


def test_legal_entity_picks_cashier_and_np_key(api, db, products, monkeypatch):
    from app.models import CheckboxCashier, LegalEntity, NpAccount
    from app.services import checkbox as cb, np as np_svc
    r = api.put("/api/settings/legal-entities", json=[{"name": "ФОП Іваненко", "code": "1234567890", "is_default": True},
                                                      {"name": "ФОП Петренко"}])
    assert r.status_code == 200, r.text
    ents = {e.name: e for e in db.query(LegalEntity)}
    iv, pe = ents["ФОП Іваненко"], ents["ФОП Петренко"]
    assert iv.is_default and not pe.is_default
    db.add_all([CheckboxCashier(name="Каса Іваненко", legal_entity_id=iv.id, license_key="k", login="l", password="p"),
                CheckboxCashier(name="Каса Петренко", legal_entity_id=pe.id, license_key="k", login="l", password="p"),
                NpAccount(name="НП Петренко", api_key="x", legal_entity_id=pe.id),
                NpAccount(name="НП Основний", api_key="y", is_default=True)])
    db.commit()
    o = new_order(api, products)
    order = db.get(Order, o["id"])
    assert order.legal_entity_id == iv.id  # юрособа за замовчуванням для нових замовлень
    assert cb.pick_cashier(db, order).name == "Каса Іваненко"
    api.patch(f"/api/orders/{o['id']}", json={"legal_entity_id": pe.id})
    db.expire_all()
    order = db.get(Order, o["id"])
    assert cb.pick_cashier(db, order).name == "Каса Петренко" and np_svc.pick_account(db, order).name == "НП Петренко"
    # фіскалізація в один клік
    sent = []
    monkeypatch.setattr(cb.Api, "sell", lambda self, body: sent.append((self.c.name if hasattr(self, "c") else "", body)) or {"id": "r1", "status": "DONE", "fiscal_code": "FX1"})
    card = api.post(f"/api/orders/{o['id']}/fiscalize").json()
    assert card["receipts"][0]["kind"] == "sell" and card["receipts"][0]["fiscal_code"] == "FX1"
    assert api.post(f"/api/orders/{o['id']}/fiscalize").status_code == 422  # чек продажу вже є
    r = api.post("/api/orders/bulk", json={"ids": [o["id"]], "action": "fiscalize"}).json()
    assert r["done"] == 0 and r["errors"]
    # юрособа без каси — зрозуміла помилка
    api.put("/api/settings/legal-entities", json=[{"id": iv.id, "name": iv.name, "is_default": True}, {"id": pe.id, "name": pe.name},
                                                  {"name": "ТОВ Без каси"}])
    third = db.query(LegalEntity).filter(LegalEntity.name == "ТОВ Без каси").one()
    o2 = new_order(api, products, phone="0507770000", legal_entity_id=third.id)
    r = api.post(f"/api/orders/{o2['id']}/fiscalize")
    assert r.status_code == 422 and "ТОВ Без каси" in r.json()["error"]
    assert next(e for e in api.get("/api/meta").json()["legal_entities"] if e["id"] == third.id)["has_cashier"] is False


def test_office_is_derived_from_source(api, db, products):
    s = api.get("/api/settings").json()
    api.put("/api/settings/dir/offices", json=[{"name": "PROM"}])
    office = api.get("/api/settings").json()["offices"][0]["id"]
    src = s["order_sources"][0]
    api.put("/api/settings/dir/sources", json=[{**src, "office_id": office}])
    o = new_order(api, products, source_id=src["id"])
    assert db.get(Order, o["id"]).office_id == office
    api.put("/api/settings/dir/offices", json=[{"id": office, "name": "PROM"}, {"name": "Сайт"}])
    site = next(x for x in api.get("/api/settings").json()["offices"] if x["name"] == "Сайт")["id"]
    api.put("/api/settings/dir/sources", json=[{**src, "office_id": site}])
    db.expire_all()
    assert db.get(Order, o["id"]).office_id == site  # зміна відділу джерела переносить і замовлення
