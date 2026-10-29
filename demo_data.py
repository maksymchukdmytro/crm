"""Заповнює CRM демонстраційними даними, щоб подивитися, як усе працює.

Запуск: docker compose exec web python demo_data.py
Не запускайте на робочій базі — дані додаються до наявних.
"""
import random
from datetime import timedelta
from decimal import Decimal

from app import db as dbmod
from app.models import Order, Product, Status, User, utcnow
from app.security import hash_password
from app.services import orders as svc
from app.services import stock
from app.services.seed import seed

NAMES = ["Шевченко Тарас", "Коваленко Олена", "Бондаренко Ігор", "Ткаченко Марія", "Кравченко Андрій",
         "Олійник Світлана", "Мельник Дмитро", "Савченко Ірина", "Руденко Василь", "Петренко Наталія",
         "Лисенко Оксана", "Гончаренко Сергій", "Марченко Юлія", "Поліщук Віктор", "Захарченко Анна"]
CITIES = [("Київ", "Відділення №12: вул. Хрещатик, 22"), ("Львів", "Відділення №5: вул. Городоцька, 120"),
          ("Одеса", "Поштомат №4421"), ("Харків", "Відділення №33: просп. Науки, 9"),
          ("Вінниця", "Відділення №2: вул. Келецька, 57"), ("Дніпро", "Відділення №17: вул. Робоча, 23")]
SOURCES = [("facebook", "spring_sale"), ("facebook", "retarget"), ("instagram", "stories"), ("google", "brand"),
           ("tiktok", "video_1")]


def main(n: int = 140):
    dbmod.init_engine()
    db = dbmod.SessionLocal()
    seed(db)
    if not db.query(User).filter(User.role == "manager").count():
        for u, name in (("olena", "Олена"), ("maksym", "Максим")):
            db.add(User(username=u, full_name=name, role="manager", password_hash=hash_password("manager123")))
        db.add(User(username="sklad", full_name="Склад", role="warehouse", password_hash=hash_password("sklad1234")))
    if not db.query(Product).count():
        for sku, name, price, cost, qty, ups in [
            ("CREAM-01", "Крем для рук «Лаванда»", 399, 120, 180, False),
            ("SERUM-02", "Сироватка з вітаміном C", 649, 210, 90, False),
            ("MASK-03", "Маска для обличчя глиняна", 299, 85, 140, False),
            ("SOAP-01", "Мило ручної роботи", 99, 30, 400, True),
            ("BRUSH-01", "Щіточка для масок", 79, 18, 300, True),
        ]:
            p = Product(sku=sku, name=name, price=price, cost=cost, stock=0, reserved=0, weight=Decimal("0.3"),
                        is_upsell=ups, min_stock=15)
            db.add(p)
            db.flush()
            stock.move(db, p.id, "purchase", qty, 0, comment="початковий залишок")
    db.commit()

    products = db.query(Product).filter(Product.is_upsell.is_(False)).all()
    upsells = db.query(Product).filter(Product.is_upsell.is_(True)).all()
    statuses = {s.code: s for s in db.query(Status).all()}
    managers = db.query(User).filter(User.role == "manager").all()
    rnd = random.Random(42)
    for i in range(n):
        age = rnd.random() ** 1.6 * 30
        city, wh = rnd.choice(CITIES)
        src, camp = rnd.choice(SOURCES)
        main_p = rnd.choice(products)
        items = [{"product_id": main_p.id, "qty": rnd.choice([1, 1, 1, 2])}]
        if rnd.random() < 0.35:
            items.append({"product_id": rnd.choice(upsells).id, "qty": 1, "is_upsell": "1"})
        order = svc.create_order(db, {
            "customer_name": rnd.choice(NAMES), "phone": f"067{rnd.randint(1000000, 9999999)}",
            "delivery_method": rnd.choice(["novaposhta"] * 6 + ["ukrposhta", "pickup"]),
            "city_name": city, "warehouse_name": wh, "utm_source": src, "utm_campaign": camp,
            "site": "beauty-landing",
        }, items, None, source="webhook")
        order.created_at = utcnow() - timedelta(days=age, minutes=rnd.randint(0, 600))
        order.manager = rnd.choice(managers)
        if age < 0.6:
            flow = rnd.choice(["new", "new", "no_answer", "callback"])
        elif age < 3:
            flow = rnd.choice(["confirmed", "packing", "shipped", "cancelled", "no_answer"])
        else:
            flow = rnd.choices(["delivered", "refused", "returned", "cancelled", "shipped"], [55, 9, 6, 18, 12])[0]
        path = {"confirmed": ["confirmed"], "packing": ["confirmed", "packing"], "shipped": ["confirmed", "shipped"],
                "delivered": ["confirmed", "shipped", "delivered"], "refused": ["confirmed", "shipped", "refused"],
                "returned": ["confirmed", "shipped", "refused", "returned"]}.get(flow, [flow])
        for code in path:
            if code != "new":
                svc.change_status(db, order, statuses[code], order.manager)
        if order.stock_shipped and order.delivery_method != "pickup":
            order.ttn = f"2045{rnd.randint(10**9, 10**10 - 1)}"
            order.delivery_state = {"delivered": "delivered", "refused": "refused", "returned": "returned"}.get(
                flow, "in_transit")
            order.delivery_status = {"delivered": "Відправлення отримано", "refused": "Відмова одержувача",
                                     "returned": "Відмова одержувача"}.get(flow, "Відправлення прямує до міста")
            order.delivery_cost = Decimal(rnd.choice([70, 85, 95, 110]))
        if flow == "delivered" and age > 6:
            for p in order.payments:
                if p.status == "collected":
                    p.status, p.received_amount, p.received_at = "received", p.amount, utcnow()
    db.commit()
    print(f"Додано {n} демо-замовлень")


if __name__ == "__main__":
    main()
