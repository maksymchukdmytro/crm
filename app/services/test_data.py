"""Тестові дані для перевірки статистики на робочому сервері: 10 товарів і 10 замовлень за останній місяць.

Безпечно для справжніх даних:
- товари мають артикул TEST-…, замовлення — сайт «test-data», тож їх видно й легко прибрати;
- статуси й дати ставляться напряму: без руху складу, SMS/Viber, чеків Checkbox і передачі на маркетплейси;
- «Видалити тестові дані» прибирає лише позначені записи (і їхній журнал змін).
"""
from __future__ import annotations

import random
from datetime import timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from ..models import AuditLog, Order, OrderItem, Product, Status, User, utcnow
from . import orders as svc

SITE = "test-data"
SKU_PREFIX = "TEST-"

PRODUCTS = [  # артикул, назва, ціна, собівартість, допродаж
    ("TEST-01", "Тест · Бездротовий мікрофон", 1899, 1250, False),
    ("TEST-02", "Тест · Кільцева лампа 26 см", 899, 520, False),
    ("TEST-03", "Тест · Штатив-монопод", 1299, 780, False),
    ("TEST-04", "Тест · Накамерне світло RGB", 2499, 1700, False),
    ("TEST-05", "Тест · Стабілізатор для смартфона", 3999, 2900, False),
    ("TEST-06", "Тест · Повербанк 20000 мА·год", 1599, 1100, False),
    ("TEST-07", "Тест · Екшн-камера 4K", 5499, 4300, False),
    ("TEST-08", "Тест · Чохол для мікрофона", 199, 60, True),
    ("TEST-09", "Тест · Адаптер Lightning", 349, 140, True),
    ("TEST-10", "Тест · Карта пам'яті 64 ГБ", 399, 210, True),
]
NAMES = ["Тестова Олена", "Тестовий Андрій", "Тестова Марія", "Тестовий Ігор", "Тестова Світлана",
         "Тестовий Дмитро", "Тестова Ірина", "Тестовий Василь", "Тестова Наталія", "Тестовий Сергій"]
UTM = [("facebook", "cpc", "autumn_sale"), ("instagram", "stories", "reels_1"), ("google", "cpc", "brand"),
       ("tiktok", "video", "creative_2"), ("", "", "")]
# шлях статусів (коди) і частота
FLOWS = [("delivered", 4), ("refused", 1), ("shipped", 1), ("confirmed", 1), ("cancelled", 1), ("no_answer", 1), ("new", 1)]


def counts(db: Session) -> dict:
    return {
        "products": db.query(Product).filter(Product.sku.like(f"{SKU_PREFIX}%")).count(),
        "orders": db.query(Order).filter(Order.site == SITE).count(),
    }


def create(db: Session, user: User | None, n_orders: int = 10, days: int = 30) -> dict:
    products = []
    for sku, name, price, cost, up in PRODUCTS:
        p = db.query(Product).filter(Product.sku == sku).one_or_none()
        if p is None:
            p = Product(sku=sku, name=name, price=price, cost=cost, stock=100, reserved=0, weight=Decimal("0.4"),
                        length=20, width=15, height=10, ship_description="Тестовий товар", is_upsell=up)
            db.add(p)
        products.append(p)
    db.flush()
    main = [p for p in products if not p.is_upsell]
    upsells = [p for p in products if p.is_upsell]
    statuses = {s.code: s for s in db.query(Status).filter(Status.is_active.is_(True))}
    fallback = statuses.get("new") or db.query(Status).order_by(Status.sort).first()
    managers = db.query(User).filter(User.role == "manager", User.is_active.is_(True)).all()
    rnd = random.Random()
    flows = [code for code, k in FLOWS for _ in range(k)]
    rnd.shuffle(flows)
    now = utcnow()
    made = []
    for i in range(n_orders):
        flow = flows[i % len(flows)]
        # свіжіші замовлення — у ранніх статусах, старші — уже доставлені або з відмовою
        age = {"new": rnd.uniform(0.05, 0.8), "no_answer": rnd.uniform(0.3, 2), "confirmed": rnd.uniform(0.5, 3),
               "shipped": rnd.uniform(1.5, 5)}.get(flow, rnd.uniform(5, days - 0.5))
        created = now - timedelta(days=age, minutes=rnd.randint(0, 59))
        src, med, camp = rnd.choice(UTM)
        mp = rnd.choice(main)
        items = [{"product_id": mp.id, "name": mp.name, "qty": rnd.choice([1, 1, 1, 2]), "price": str(mp.price)}]
        if rnd.random() < 0.45:
            u = rnd.choice(upsells)
            items.append({"product_id": u.id, "name": u.name, "qty": 1, "price": str(u.price), "is_upsell": "1", "upsell_for": mp.id})
        order = svc.create_order(db, {
            "customer_name": NAMES[i % len(NAMES)], "phone": f"38099000{rnd.randint(1000, 9999)}",
            "delivery_method": rnd.choice(["novaposhta"] * 5 + ["ukrposhta"]), "city_name": "Київ",
            "warehouse_name": "Відділення №1 (тест)", "site": SITE, "utm_source": src, "utm_medium": med,
            "utm_campaign": camp, "comment": "Тестове замовлення для перевірки статистики",
        }, items, None, source="test")
        order.duplicate_of_id = None
        status = statuses.get(flow) or fallback
        order.status = status
        order.status_id = status.id
        order.manager = rnd.choice(managers) if managers else None
        db.flush()
        # дати після flush, щоб автоматичні «закріплене / підтверджене» не перезаписали їх поточним часом
        order.created_at = created
        order.status_changed_at = created + timedelta(hours=rnd.uniform(0.2, 30))
        order.assigned_at = created + timedelta(minutes=rnd.randint(1, 20)) if order.manager_id else None
        approved = status.counts_as_approved
        order.confirmed_at = created + timedelta(minutes=rnd.randint(5, 240)) if approved else None
        if flow in ("shipped", "delivered", "refused"):
            order.shipped_at = created + timedelta(hours=rnd.uniform(4, 30))
            order.ttn = f"2045{rnd.randint(10**9, 10**10 - 1)}"
            order.delivery_state = {"delivered": "delivered", "refused": "refused"}.get(flow, "in_transit")
        if flow == "delivered":
            order.delivered_at = order.shipped_at + timedelta(days=rnd.uniform(1, 3))
        order.updated_at = max(d for d in (order.status_changed_at, order.shipped_at, order.delivered_at) if d)
        made.append(order)
    db.flush()
    return {**counts(db), "created_orders": len(made)}


def delete(db: Session) -> dict:
    ids = [i for (i,) in db.query(Order.id).filter(Order.site == SITE)]
    if ids:
        db.query(AuditLog).filter(AuditLog.entity == "order", AuditLog.entity_id.in_(ids)).delete(synchronize_session=False)
        for o in db.query(Order).filter(Order.id.in_(ids)):
            db.delete(o)
        db.flush()
    removed_p = kept_p = 0
    for p in db.query(Product).filter(Product.sku.like(f"{SKU_PREFIX}%")):
        if db.query(OrderItem).filter(OrderItem.product_id == p.id).count():
            p.is_active = False  # товар потрапив у справжнє замовлення — лише вимикаємо
            kept_p += 1
        else:
            db.delete(p)
            removed_p += 1
    db.flush()
    return {**counts(db), "deleted_orders": len(ids), "deleted_products": removed_p, "disabled_products": kept_p}
