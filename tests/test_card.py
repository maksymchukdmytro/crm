"""Картка замовлення (крок 5): «Що лишилось», рахунки юрособ і підтвердження передоплати, реєстр НП, вікно ТТН, історія."""
from decimal import Decimal

from app.models import LegalEntity, NpAccount, Order, Status

from .test_api import api, api_manager, new_order  # noqa: F401 — фікстури
from .test_delivery_payments import np_mock


def _sid(db, code):
    return db.query(Status).filter(Status.code == code).one().id


def _np_account(db):
    acc = NpAccount(name="ФОП", api_key="KEY", sender_ref="S", contact_ref="C", sender_phone="380501112233",
                    city_ref="CS", warehouse_ref="WS", is_default=True)
    db.add(acc)
    db.commit()
    return acc


def test_checklist_flow(api, db, products):
    o = new_order(api, products)
    assert o["todo"] == []                                        # несортоване — ще нічого
    o = api.patch(f"/api/orders/{o['id']}", json={"status_id": _sid(db, "confirmed")}).json()
    keys = {t["key"]: t["state"] for t in o["todo"]}
    assert keys["reserve"] == "done" and keys["ttn"] == "pending"
    assert "label" not in keys and "registry" not in keys        # без ТТН — ці кроки не показуємо
    o = api.patch(f"/api/orders/{o['id']}", json={"ttn": "20450000000099"}).json()
    keys = {t["key"]: t for t in o["todo"]}
    assert keys["ttn"]["state"] == "done" and keys["label"]["action"] == "label" and keys["registry"]["state"] == "pending"
    o = api.patch(f"/api/orders/{o['id']}", json={"status_id": _sid(db, "shipped")}).json()
    assert [t["key"] for t in o["todo"]][:2] == ["received", "money"]


def test_entity_accounts_and_prepayment_confirm(api, api_manager, db, products):
    le = LegalEntity(name="ФОП Максимчук", is_default=True)
    db.add(le)
    db.commit()
    r = api.post(f"/api/legal-entities/{le.id}/accounts", json={"name": "Monobank", "kind": "card", "card_mask": "5375 •• 1234"})
    assert r.status_code == 200, r.text
    acc = r.json()
    assert api.post(f"/api/legal-entities/{le.id}/accounts", json={"name": "Банк", "kind": "iban", "iban": "UA12"}).status_code == 400
    assert api_manager.post(f"/api/legal-entities/{le.id}/accounts", json={"name": "x"}).status_code == 403
    assert [a["name"] for a in api_manager.get(f"/api/legal-entities/{le.id}/accounts").json()] == ["Monobank"]
    assert api.get("/api/meta").json()["legal_entities"][0]["accounts"][0]["name"] == "Monobank"

    o = new_order(api, products, payment_method_id=2, prepayment="200")  # «Передоплата»
    o = api.patch(f"/api/orders/{o['id']}", json={"status_id": _sid(db, "confirmed")}).json()
    assert {t["key"]: t["state"] for t in o["todo"]}["prepay"] == "pending"
    o = api.post(f"/api/orders/{o['id']}/prepayment/confirm", json={"account_id": acc["id"]}).json()
    p = [x for x in o["payments"] if x["kind"] == "prepayment"][0]
    assert p["status"] == "received" and p["amount"] == 200 and p["account"] == "Monobank" and p["confirmed_by"] and p["confirmed_at"]
    assert {t["key"]: t["state"] for t in o["todo"]}["prepay"] == "done"
    # повторне підтвердження не додає оплату вдруге
    o = api.post(f"/api/orders/{o['id']}/prepayment/confirm", json={"account_id": acc["id"]}).json()
    assert len([x for x in o["payments"] if x["kind"] == "prepayment"]) == 1
    assert api.delete(f"/api/legal-entities/{le.id}/accounts/{acc['id']}").status_code == 200


def test_ttn_window_after_actions_and_registry(api, db, products, mock_api):
    _np_account(db)
    np_mock(mock_api)
    mock_api.on(lambda c: c["json"].get("calledMethod") == "getDocumentPrice", {"success": True, "data": [{"Cost": 85, "CostAfterpaymentOnGoodsCost": 32}]})
    mock_api.on(lambda c: c["json"].get("calledMethod") == "getDocumentDeliveryDate",
                {"success": True, "data": [{"DeliveryDate": {"date": "2026-10-31 00:00:00"}}]})
    mock_api.on(lambda c: c["json"].get("calledMethod") == "insertDocuments",
                lambda c: {"success": True, "data": [{"Ref": "REG1", "Number": "105-00001", "Errors": []}]})
    a = new_order(api, products, phone="0501112201")
    b = new_order(api, products, phone="0501112202")
    p = api.get(f"/api/orders/{a['id']}/ttn/preview").json()
    assert p["price"] == 85 and p["cod_commission"] == 32 and p["eta"] == "2026-10-31" and p["recipient"].startswith("Шевченко")
    r = api.post(f"/api/orders/{a['id']}/ttn", json={"city_name": "Київ", "city_ref": "CK", "warehouse_name": "Відділення №12", "warehouse_ref": "W12",
                                                      "after": {"print_label": True, "add_registry": True, "set_shipped": True}})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["ttn"] == "20450000000001" and d["label_url"] == f"/api/orders/{a['id']}/label"
    assert d["np_registry_ref"] == "105-00001", d["after_errors"]
    assert d["warehouse_name"] == "Відділення №12"
    assert db.get(Order, a["id"]).status.code == "shipped"
    # друге замовлення того ж ключа за день — у той самий реєстр
    api.post(f"/api/orders/{b['id']}/ttn")
    r = api.post("/api/orders/bulk", json={"ids": [b["id"]], "action": "registry"}).json()
    assert r["done"] == 1
    reg = [c["json"]["methodProperties"] for c in mock_api.calls if c["json"].get("calledMethod") == "insertDocuments"]
    assert reg[0].get("Ref") is None and reg[1]["Ref"] == "REG1"


def test_label_marks_printed_and_history(api, db, products, mock_api):
    import httpx
    _np_account(db)
    mock_api.on("printMarking100x100", httpx.Response(200, content=b"%PDF-1.4 test"))
    o = new_order(api, products)
    api.patch(f"/api/orders/{o['id']}", json={"ttn": "20450000000077", "status_id": _sid(db, "confirmed")})
    assert api.get(f"/api/orders/{o['id']}/label").status_code == 200
    db.expire_all()
    assert db.get(Order, o["id"]).label_printed_at is not None
    api.post(f"/api/orders/{o['id']}/comments", json={"text": "Подзвонити після 18:00"})
    h = api.get(f"/api/orders/{o['id']}/history").json()["events"]
    assert {e["kind"] for e in h} >= {"status", "comment"}
    only = api.get(f"/api/orders/{o['id']}/history?kind=comments").json()["events"]
    assert [e["details"] for e in only] == ["Подзвонити після 18:00"]


def test_items_cost_only_for_admin(api, api_manager, db, products):
    cream, _ = products
    cream.cost = Decimal("150")
    db.commit()
    o = new_order(api, products)
    assert api.get(f"/api/orders/{o['id']}").json()["items_cost"] is not None
    db.get(Order, o["id"]).manager_id = None
    db.commit()
    r = api_manager.get(f"/api/orders/{o['id']}")
    if r.status_code == 200:
        assert r.json()["items_cost"] is None
