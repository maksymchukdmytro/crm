"""Друк документів: дані для видаткової, рахунку-фактури й гарантійного талону; реквізити юрособи; налаштування."""
from app.models import Order, Product

from .test_api import api  # noqa: F401 — фікстура
from .test_orders import create_via_ui


def test_documents_payload(api, admin, db, products):
    cream, _ = products
    cream.warranty_months = 24
    db.commit()
    s = api.put("/api/settings/legal-entities", json=[{"name": "ФОП Максимчук О.В.", "code": "3012345678", "iban": "UA213223130000026007233566001",
                                                      "code_label": "РНОКПП", "address": "м. Тульчин", "bank": "ПриватБанк", "phone": "+380633496560",
                                                      "signer": "Максимчук О. В.", "is_default": True}]).json()
    le = s["legal_entities"][0]
    assert (le["address"], le["bank"], le["signer"], le["vat_note"]) == ("м. Тульчин", "ПриватБанк", "Максимчук О. В.", "Без ПДВ")
    oid = create_via_ui(admin, products, discount="10")
    d = api.get(f"/api/orders/{oid}/documents").json()
    assert d["seller"]["name"] == "ФОП Максимчук О.В." and d["seller"]["iban"].startswith("UA21")
    o = d["order"]
    assert o["id"] == oid and o["buyer"] == "Шевченко Тарас" and o["discount"] == 10 and o["total"] == 887
    assert [i["qty"] for i in o["items"]] == [2, 1] and o["items"][0]["warranty_months"] == 24
    assert d["docs"]["doc_prefix"] == "РН-" and "{months}" in d["docs"]["warranty_terms"] and d["docs"]["warranty_months"] == "12"


def test_document_settings_validation(api):
    assert api.put("/api/settings/docs", json={"doc_prefix": "ВН-", "warranty_months": "6", "doc_accent": "#112233"}).status_code == 200
    assert api.get("/api/settings").json()["values"]["doc_prefix"] == "ВН-"
    assert api.put("/api/settings/docs", json={"doc_logo": "javascript:alert(1)"}).status_code == 400
    assert api.put("/api/settings/docs", json={"doc_accent": "red"}).status_code == 400
    assert api.put("/api/settings/docs", json={"warranty_months": "дванадцять"}).status_code == 400


def test_product_warranty_saved(api, db, products):
    cream, _ = products
    r = api.patch(f"/api/products/{cream.id}", json={"warranty_months": 36})
    assert r.status_code == 200, r.text
    db.expire_all()
    assert db.get(Product, cream.id).warranty_months == 36
