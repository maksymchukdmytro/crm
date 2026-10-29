from decimal import Decimal

import httpx

from app.carriers.novaposhta import np_state
from app.carriers.ukrposhta import up_state
from app.models import Order, Payment, Product, Purchase, SmsMessage, Status
from app.services import delivery, sms
from app.services import settings as st

from .test_orders import create_via_ui, fresh, order_form, status_id


def configure_np(db):
    for k, v in {"np_api_key": "KEY", "np_sender_ref": "S", "np_contact_ref": "C", "np_sender_phone": "380500000000",
                 "np_city_ref": "CS", "np_warehouse_ref": "WS"}.items():
        st.set_value(db, k, v)
    db.commit()


def np_mock(mock_api, status_code="5"):
    mock_api.on(lambda c: c["json"].get("calledMethod") == "save" and c["json"].get("modelName") == "Counterparty",
                {"success": True, "data": [{"Ref": "REC", "ContactPerson": {"data": [{"Ref": "RCONT"}]}}]})
    mock_api.on(lambda c: c["json"].get("modelName") == "InternetDocument" and c["json"].get("calledMethod") == "save",
                {"success": True, "data": [{"IntDocNumber": "20450000000001", "Ref": "DOCREF", "CostOnSite": 85}]})
    mock_api.on(lambda c: c["json"].get("calledMethod") == "getStatusDocuments",
                lambda c: {"success": True, "data": [{"Number": d["DocumentNumber"], "StatusCode": status_code[0],
                                                      "Status": "Посилка в дорозі"} for d in
                                                     c["json"]["methodProperties"]["Documents"]]})


def test_status_mapping():
    assert np_state("9") == "delivered" and np_state("103") == "refused" and np_state("7") == "arrived"
    assert up_state("Відправлення вручено") == "delivered"
    assert up_state("Вручено відправнику") == "returned"
    assert up_state("Повернення відправлення") == "refused"


def test_np_create_ttn(admin, db, products, mock_api):
    configure_np(db)
    np_mock(mock_api)
    oid = create_via_ui(admin, products)
    r = admin.post(f"/orders/{oid}/ttn", follow_redirects=False)
    assert r.status_code == 303
    o = fresh(db, db.get(Order, oid))
    assert o.ttn == "20450000000001" and o.carrier_ref == "DOCREF" and o.delivery_cost == Decimal("85")
    doc = next(c["json"] for c in mock_api.calls if c["json"].get("modelName") == "InternetDocument")
    props = doc["methodProperties"]
    assert props["BackwardDeliveryData"][0]["RedeliveryString"] == "897.00"
    assert props["RecipientAddress"] == "wh-ref" and props["Recipient"] == "REC"
    assert Decimal(props["Weight"]) == Decimal("0.7")  # 2 × 0.3 + 1 × 0.1
    rec = next(c["json"] for c in mock_api.calls if c["json"].get("modelName") == "Counterparty")
    assert rec["methodProperties"]["LastName"] == "Шевченко" and rec["methodProperties"]["FirstName"] == "Тарас"


def test_np_afterpayment_mode(admin, db, products, mock_api):
    configure_np(db)
    st.set_value(db, "np_cod_mode", "afterpayment")
    db.commit()
    np_mock(mock_api)
    oid = create_via_ui(admin, products)
    admin.post(f"/orders/{oid}/ttn")
    props = next(c["json"] for c in mock_api.calls if c["json"].get("modelName") == "InternetDocument")["methodProperties"]
    assert props["AfterpaymentOnGoodsCost"] == "897.00" and "BackwardDeliveryData" not in props


def test_np_error_is_shown(admin, db, products, mock_api):
    configure_np(db)
    mock_api.on(lambda c: True, {"success": False, "errors": ["RecipientsPhone is invalid"]})
    oid = create_via_ui(admin, products)
    r = admin.post(f"/orders/{oid}/ttn")
    assert "RecipientsPhone is invalid" in r.text
    assert fresh(db, db.get(Order, oid)).ttn == ""


def test_missing_sender_settings(admin, db, products, mock_api):
    st.set_value(db, "np_api_key", "KEY")
    db.commit()
    oid = create_via_ui(admin, products)
    r = admin.post(f"/orders/{oid}/ttn")
    assert "Не заповнені дані відправника" in r.text


def test_tracking_auto_status_flow(admin, db, products, mock_api):
    configure_np(db)
    cream, _ = products
    oid = create_via_ui(admin, products, ttn="20450000000099", status_id=str(status_id(db, "confirmed")))
    state = {"code": "5"}
    mock_api.on(lambda c: c["json"].get("calledMethod") == "getStatusDocuments",
                lambda c: {"success": True, "data": [{"Number": "20450000000099", "StatusCode": state["code"],
                                                      "Status": "статус " + state["code"]}]})
    delivery.sync_tracking(db, force=True)
    o = fresh(db, db.get(Order, oid))
    assert o.status.code == "shipped" and o.delivery_state == "in_transit"
    assert fresh(db, cream).stock == 8 and fresh(db, cream).reserved == 0
    assert o.payments[0].status == "expected"

    state["code"] = "9"
    delivery.sync_tracking(db, force=True)
    o = fresh(db, db.get(Order, oid))
    assert o.status.code == "delivered" and o.delivered_at is not None
    assert o.payments[0].status == "collected"

    # фінальні стани більше не перевіряються
    n = len(mock_api.calls)
    delivery.sync_tracking(db, force=True)
    assert len(mock_api.calls) == n


def test_tracking_refusal(admin, db, products, mock_api):
    configure_np(db)
    oid = create_via_ui(admin, products, ttn="20450000000077", status_id=str(status_id(db, "shipped")))
    mock_api.on(lambda c: True, {"success": True, "data": [{"Number": "20450000000077", "StatusCode": "103",
                                                            "Status": "Відмова одержувача"}]})
    delivery.sync_tracking(db, force=True)
    o = fresh(db, db.get(Order, oid))
    assert o.status.code == "refused" and o.payments[0].status == "cancelled"


def test_tracking_respects_interval(admin, db, products, mock_api):
    configure_np(db)
    create_via_ui(admin, products, ttn="20450000000055")
    mock_api.on(lambda c: True, {"success": True, "data": [{"Number": "20450000000055", "StatusCode": "5", "Status": "x"}]})
    assert delivery.sync_tracking(db)["checked"] == 1
    assert delivery.sync_tracking(db)["checked"] == 0  # нещодавно перевірено


def test_delete_ttn(admin, db, products, mock_api):
    configure_np(db)
    np_mock(mock_api)
    mock_api.on(lambda c: c["json"].get("calledMethod") == "delete", {"success": True, "data": [{"Ref": "DOCREF"}]})
    oid = create_via_ui(admin, products)
    admin.post(f"/orders/{oid}/ttn")
    admin.post(f"/orders/{oid}/ttn/delete")
    o = fresh(db, db.get(Order, oid))
    assert o.ttn == "" and o.carrier_ref == ""


def test_label_proxy(admin, db, products, mock_api):
    configure_np(db)
    np_mock(mock_api)
    mock_api.on("printMarking", httpx.Response(200, content=b"%PDF-1.4 label"))
    oid = create_via_ui(admin, products)
    admin.post(f"/orders/{oid}/ttn")
    r = admin.get(f"/orders/{oid}/label")
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"


def test_np_city_autocomplete(admin, db, mock_api):
    configure_np(db)
    mock_api.on(lambda c: c["json"].get("calledMethod") == "getCities",
                {"success": True, "data": [{"Ref": "R1", "Description": "Київ", "AreaDescription": "Київська",
                                            "SettlementTypeDescription": "місто"}]})
    data = admin.get("/api/np/cities?q=Ки").json()
    assert data["ok"] and data["items"][0]["ref"] == "R1" and "Київська" in data["items"][0]["label"]


# ------------------------------------------------------------------ звірка
def shipped_order(admin, db, products, ttn):
    return create_via_ui(admin, products, ttn=ttn, status_id=str(status_id(db, "shipped")))


def test_registry_import(admin, db, products):
    o1 = shipped_order(admin, db, products, "20450000000101")
    o2 = shipped_order(admin, db, products, "20450000000102")
    csv_text = "Номер ЕН;Сума переказу\n20450000000101;897,00\n20450000000102;800\n20450000009999;100\n"
    r = admin.post("/payments/import", files={"file": ("reg.csv", csv_text.encode("cp1251"), "text/csv")})
    assert r.status_code == 200
    assert "Розбіжність суми" in r.text and "20450000009999" in r.text
    db.expire_all()
    p1 = db.query(Payment).filter(Payment.order_id == o1).one()
    p2 = db.query(Payment).filter(Payment.order_id == o2).one()
    assert p1.status == "received" and p1.received_amount == Decimal("897")
    assert p2.status == "received" and p2.received_amount == Decimal("800")
    # повторний імпорт не дублює
    r = admin.post("/payments/import", files={"file": ("reg.csv", csv_text.encode(), "text/csv")})
    assert "вже були зараховані: 2" in r.text


def test_manual_mark_received(admin, db, products):
    oid = shipped_order(admin, db, products, "20450000000201")
    pid = db.query(Payment).filter(Payment.order_id == oid).one().id
    admin.post("/payments/receive", data={"ids": [str(pid)], "reference": "виписка 12"})
    db.expire_all()
    p = db.get(Payment, pid)
    assert p.status == "received" and p.reference == "виписка 12"


# --------------------------------------------------------------------- SMS
def test_sms_queue_and_send(admin, db, products):
    st.set_value(db, "sms_enabled", "1")
    st.set_value(db, "sms_token", "T")
    st.set_value(db, "sms_sender", "Shop")
    db.commit()
    oid = create_via_ui(admin, products, ttn="20450000000301", status_id=str(status_id(db, "shipped")))
    msgs = db.query(SmsMessage).filter(SmsMessage.order_id == oid).all()
    assert len(msgs) == 1 and "20450000000301" in msgs[0].text and "897" in msgs[0].text

    sent_bodies = []

    def handler(request):
        import json
        sent_bodies.append(json.loads(request.content))
        return httpx.Response(200, json={"response_code": 800, "response_result": [
            {"phone": "380501112233", "response_code": 0, "message_id": "abc-1", "response_status": "OK"}]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    assert sms.send_pending(db, client=client) == 1
    assert sent_bodies[0]["sms"]["sender"] == "Shop" and sent_bodies[0]["recipients"] == ["380501112233"]
    db.expire_all()
    m = db.get(SmsMessage, msgs[0].id)
    assert m.status == "sent" and m.provider_id == "abc-1"


def test_sms_failure_retries(db):
    st.set_value(db, "sms_token", "T")
    db.add(SmsMessage(phone="380501112233", text="x", channel="sms"))
    db.commit()
    client = httpx.Client(transport=httpx.MockTransport(
        lambda r: httpx.Response(200, json={"response_code": 103, "response_status": "REQUIRED_TOKEN"})))
    for _ in range(3):
        sms.send_pending(db, client=client)
    m = db.query(SmsMessage).one()
    assert m.status == "failed" and m.attempts == 3 and "REQUIRED_TOKEN" in m.error


def test_sms_disabled_by_default(admin, db, products):
    create_via_ui(admin, products, status_id=str(status_id(db, "shipped")))
    assert db.query(SmsMessage).count() == 0


# ---------------------------------------------------------- закупівлі/склад
def test_purchase_receive_updates_stock_and_cost(warehouse, db, products):
    cream, _ = products
    r = warehouse.post("/purchases/new", data={"supplier_id": "", "comment": "партія 1",
                                                "item_product_id": [str(cream.id)], "item_qty": ["10"],
                                                "item_cost": ["150"], "then": "receive"}, follow_redirects=False)
    assert r.status_code == 303
    cream = fresh(db, cream)
    assert cream.stock == 20
    assert cream.cost == Decimal("135.00")  # (10×120 + 10×150) / 20
    p = db.query(Purchase).one()
    assert p.status == "received"
    # повторне оприбуткування неможливе
    warehouse.post(f"/purchases/{p.id}", data={"then": "receive", "item_product_id": [str(cream.id)],
                                                "item_qty": ["10"], "item_cost": ["150"]})
    assert fresh(db, cream).stock == 20


def test_inventory_adjust(warehouse, db, products):
    cream, _ = products
    warehouse.post("/warehouse/adjust", data={"product_id": cream.id, "mode": "set", "qty": "7", "comment": "інвент"})
    assert fresh(db, cream).stock == 7
    warehouse.post("/warehouse/adjust", data={"product_id": cream.id, "mode": "delta", "qty": "-2"})
    assert fresh(db, cream).stock == 5


def test_product_create(warehouse, db):
    warehouse.post("/products/new", data={"name": "Новий товар", "sku": "NEW-1", "price": "250", "cost": "100",
                                          "weight": "1", "initial_stock": "5", "is_active": "1", "is_upsell": "0"})
    p = db.query(Product).filter(Product.sku == "NEW-1").one()
    assert p.stock == 5 and p.price == Decimal("250")


# ------------------------------------------------------------------ звіти
def test_reports_numbers(admin, db, products, webhook_key):
    for i, src in enumerate(["facebook", "facebook", "google", "facebook"]):
        admin.post(f"/api/v1/orders?key={webhook_key}", data={"phone": f"06700000{i:02d}", "sku": "CREAM-1",
                                                              "utm_source": src})
    orders = db.query(Order).order_by(Order.id).all()
    admin.post("/orders/bulk", data={"ids": [str(orders[0].id), str(orders[2].id)],
                                     "action": f"status:{status_id(db, 'delivered')}"})
    admin.post("/orders/bulk", data={"ids": [str(orders[1].id)], "action": f"status:{status_id(db, 'refused')}"})
    from datetime import date
    from app.services.reports import build
    db.expire_all()
    r = build(db, date.today(), date.today(), "utm_source")
    fb = dict(r["groups"])["facebook"]
    assert fb.leads == 3 and fb.approved == 2 and fb.delivered == 1 and fb.refused == 1
    assert round(fb.buyout_rate) == 50
    assert r["total"].revenue == Decimal("798") and r["total"].profit == Decimal("558")
    page = admin.get("/reports?dim=utm_source").text
    assert "facebook" in page and "google" in page
