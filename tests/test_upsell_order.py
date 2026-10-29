"""Порядок позицій: допродаж — одразу під своїм основним товаром."""
from app.services import orders as order_svc


def test_upsell_goes_right_under_its_main_item(db, products):
    """Допродаж зберігається одразу під своїм товаром, навіть якщо прийшов першим (лендинг, маркетплейс)."""
    cream, soap = products
    items = order_svc.build_items(db, [
        {"product_id": soap.id, "qty": 1, "is_upsell": "1", "upsell_for": cream.id},
        {"name": "Довільна", "qty": 1, "price": "10"},
        {"product_id": cream.id, "qty": 1},
        {"name": "Пакет", "qty": 1, "price": "5", "is_upsell": "1"},
    ])
    assert [(i.name, i.is_upsell) for i in items] == [
        ("Довільна", False), (cream.name, False), (soap.name, True), ("Пакет", True)]
