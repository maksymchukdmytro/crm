"""Видаткові накладні (крок 6): нумерація для юрособи й типу, знімок даних, перевипуск, анулювання, автовидача, «змінилось», реєстр."""
from app.models import IssuedDocument, LegalEntity, Order, Status

from .test_api import api, new_order  # noqa: F401 — фікстури


def _sid(db, code):
    return db.query(Status).filter(Status.code == code).one().id


def _entities(db):
    a = LegalEntity(name="ФОП Максимчук О. В.", is_default=True)
    b = LegalEntity(name="ФОП Максимчук Д. О.", waybill_prefix="ДМ-")
    db.add_all([a, b])
    db.commit()
    return a, b


def test_numbering_per_entity_and_kind(api, db, products):
    a, b = _entities(db)
    o1 = new_order(api, products, phone="0501113301")["id"]
    o2 = new_order(api, products, phone="0501113302")["id"]
    o3 = new_order(api, products, phone="0501113303", legal_entity_id=b.id)["id"]
    d1 = api.post(f"/api/orders/{o1}/documents/waybill").json()
    d2 = api.post(f"/api/orders/{o2}/documents/waybill").json()
    d3 = api.post(f"/api/orders/{o3}/documents/waybill").json()
    i1 = api.post(f"/api/orders/{o1}/documents/invoice").json()
    assert (d1["number_text"], d2["number_text"], d3["number_text"], i1["number_text"]) == ("РН-0001", "РН-0002", "ДМ-0001", "СФ-0001")
    assert api.post(f"/api/orders/{o1}/documents/waybill").json()["id"] == d1["id"]  # чинний повертається, не новий
    assert d1["snapshot"]["number_text"] == "РН-0001" and d1["snapshot"]["seller"]["name"] == "ФОП Максимчук О. В."


def test_snapshot_frozen_and_changed_flag(api, db, products):
    _entities(db)
    oid = new_order(api, products)["id"]
    d = api.post(f"/api/orders/{oid}/documents/waybill").json()
    total = d["snapshot"]["order"]["total"]
    api.patch(f"/api/orders/{oid}", json={"discount": "100"})
    again = api.get(f"/api/documents/{d['id']}").json()
    assert again["snapshot"]["order"]["total"] == total and again["changed"] is True
    rows = api.get("/api/documents").json()["rows"]
    assert rows[0]["changed"] is True


def test_reissue_and_void(api, db, products):
    _entities(db)
    oid = new_order(api, products)["id"]
    d = api.post(f"/api/orders/{oid}/documents/waybill").json()
    new = api.post(f"/api/documents/{d['id']}/reissue").json()
    assert new["number_text"] == "РН-0002" and new["state"] == "active"
    old = api.get(f"/api/documents/{d['id']}").json()
    assert old["state"] == "void" and old["replaced_by_id"] == new["id"]
    assert api.post(f"/api/documents/{d['id']}/reissue").status_code == 400
    assert api.post(f"/api/documents/{new['id']}/void").json()["state"] == "void"
    # номер не використовується повторно
    assert api.post(f"/api/orders/{oid}/documents/waybill").json()["number_text"] == "РН-0003"


def test_auto_issue_on_shipped_and_register(api, db, products):
    a, b = _entities(db)
    oid = new_order(api, products)["id"]
    api.patch(f"/api/orders/{oid}", json={"status_id": _sid(db, "shipped")})
    kinds = sorted(d.kind for d in db.query(IssuedDocument).filter(IssuedDocument.order_id == oid))
    assert kinds == ["warranty", "waybill"]
    api.post(f"/api/orders/{oid}/documents/invoice")
    reg = api.get("/api/documents").json()
    row = reg["rows"][0]
    assert row["docs"]["invoice"] and row["docs"]["warranty"] and row["entity"] == "ФОП Максимчук О. В."
    assert reg["count_active"] == 1 and reg["sum"] > 0 and reg["entities"][0]["count"] == 1
    assert api.get(f"/api/documents?entity={b.id}").json()["rows"] == []
    assert len(api.get("/api/documents?has_invoice=1").json()["rows"]) == 1
    csv = api.get("/api/documents/export").text
    assert "РН-0001" in csv and "ФОП Максимчук О. В." in csv
    assert api.post(f"/api/documents/{row['id']}/printed").json()["print_count"] == 1


def test_auto_issue_off(api, db, products):
    _entities(db)
    api.put("/api/settings/docs", json={"doc_auto_issue": "off"})
    oid = new_order(api, products)["id"]
    api.patch(f"/api/orders/{oid}", json={"status_id": _sid(db, "shipped")})
    assert db.query(IssuedDocument).filter(IssuedDocument.order_id == oid).count() == 0
    assert api.put("/api/settings/docs", json={"doc_auto_issue": "never"}).status_code == 400
    assert db.get(Order, oid).status.code == "shipped"
