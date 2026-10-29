"""«Перевірка оплати»: вид оплати ↔ що стоїть у ТТН Нової Пошти (створеній у CRM або вставленій вручну)."""
from decimal import Decimal

from app.models import Order, PaymentMethod
from app.services import delivery, pay_check
from app.services import orders as order_svc
from app.services import settings as st

from .test_delivery_payments import configure_np, np_mock
from .test_api import api  # noqa: F401 — фікстура
from .test_orders import create_via_ui, fresh

NOVAPAY, PAID = 16, 1  # id видів оплат як у LP-CRM


def _with_method(db, oid, method_id):
    o = db.get(Order, oid)
    order_svc.update_order(db, o, {"payment_method_id": method_id}, None)
    db.commit()
    return fresh(db, o)


def _track(mock_api, ttn, **fields):
    mock_api.on(lambda c: c["json"].get("calledMethod") == "getStatusDocuments",
                lambda c: {"success": True, "data": [{"Number": ttn, "StatusCode": "5", "Status": "В дорозі", **fields}]})


def test_defaults_of_payment_methods(db):
    assert db.get(PaymentMethod, NOVAPAY).np_cod == "control"
    assert db.get(PaymentMethod, PAID).np_cod == "none"


def test_novapay_ttn_with_payment_control_is_ok(admin, db, products, mock_api):
    configure_np(db)
    st.set_value(db, "np_cod_mode", "afterpayment")
    db.commit()
    np_mock(mock_api)
    o = _with_method(db, create_via_ui(admin, products), NOVAPAY)
    assert pay_check.check(o)["state"] == "wait"  # ТТН ще немає
    admin.post(f"/orders/{o.id}/ttn")
    o = fresh(db, o)
    assert (o.ttn_cod_kind, o.ttn_cod_sum) == ("control", Decimal("897.00"))
    assert pay_check.check(o) == {"state": "ok", "text": "Контроль оплати 897 ₴ — збігається"}


def test_novapay_ttn_with_money_transfer_is_wrong(admin, db, products, mock_api):
    configure_np(db)  # за замовчуванням — грошовий переказ
    np_mock(mock_api)
    o = _with_method(db, create_via_ui(admin, products), NOVAPAY)
    admin.post(f"/orders/{o.id}/ttn")
    c = pay_check.check(fresh(db, o))
    assert c["state"] == "bad" and "грошовий переказ" in c["text"]


def test_paid_order_ttn_without_cod_is_ok(admin, db, products, mock_api):
    configure_np(db)
    np_mock(mock_api)
    o = _with_method(db, create_via_ui(admin, products), PAID)
    admin.post(f"/orders/{o.id}/ttn")
    o = fresh(db, o)
    assert o.ttn_cod_kind == "none" and pay_check.check(o)["state"] == "ok"


def test_pasted_ttn_checked_by_tracking(admin, db, products, mock_api):
    configure_np(db)
    o = _with_method(db, create_via_ui(admin, products, ttn="20450000000777"), PAID)
    assert pay_check.check(o)["state"] == "wait"  # що в чужій ТТН — ще невідомо
    # оплачене замовлення, а в ТТН контроль оплати — помилка
    _track(mock_api, "20450000000777", AfterpaymentOnGoodsCost="897", Redelivery="0", RedeliverySum="0")
    delivery.sync_tracking(db, force=True)
    o = fresh(db, o)
    assert (o.ttn_cod_kind, o.ttn_cod_sum) == ("control", Decimal("897.00"))
    c = pay_check.check(o)
    assert c["state"] == "bad" and "оплачене" in c["text"]


def test_payment_control_sum_mismatch(admin, db, products, mock_api):
    configure_np(db)
    o = _with_method(db, create_via_ui(admin, products, ttn="20450000000778"), NOVAPAY)
    _track(mock_api, "20450000000778", AfterpaymentOnGoodsCost="500", Redelivery="0", RedeliverySum="0")
    delivery.sync_tracking(db, force=True)
    c = pay_check.check(fresh(db, o))
    assert c["state"] == "bad" and "500 ₴" in c["text"] and "897 ₴" in c["text"]


def test_changed_ttn_resets_check_and_api_shows_it(api, admin, db, products, mock_api):
    configure_np(db)
    o = _with_method(db, create_via_ui(admin, products, ttn="20450000000779"), NOVAPAY)
    _track(mock_api, "20450000000779", AfterpaymentOnGoodsCost="897", Redelivery="0", RedeliverySum="0")
    delivery.sync_tracking(db, force=True)
    row = next(r for r in api.get("/api/orders").json()["items"] if r["id"] == o.id)
    assert row["pay_check"]["state"] == "ok"
    order_svc.update_order(db, fresh(db, o), {"ttn": "20450000000780"}, None)
    db.commit()
    o = fresh(db, o)
    assert o.ttn_cod_kind == "" and pay_check.check(o)["state"] == "wait"
    # не Нова Пошта — перевірки немає
    order_svc.update_order(db, o, {"delivery_method": "pickup"}, None)
    db.commit()
    assert pay_check.check(fresh(db, o)) is None
