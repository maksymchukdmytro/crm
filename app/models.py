from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

Money = Numeric(12, 2)


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


ROLES = {
    "admin": "Адміністратор",
    "manager": "Менеджер",
    "warehouse": "Склад",
}

DELIVERY_METHODS = {
    "novaposhta": "Нова Пошта",
    "ukrposhta": "Укрпошта",
    "meest": "Meest",
    "pickup": "Самовивіз",
    "courier": "Кур'єр",
}

PAYMENT_TYPES = {
    "cod": "Накладений платіж",
    "partial": "Передоплата + накладений",
    "prepaid": "Повна передоплата",
}

# Узагальнений стан доставки, у який зводяться статуси всіх перевізників
DELIVERY_STATES = {
    "created": "Створено ТТН",
    "in_transit": "В дорозі",
    "arrived": "У відділенні",
    "delivered": "Отримано",
    "refused": "Відмова / повернення",
    "returned": "Повернуто відправнику",
    "deleted": "ТТН видалено",
    "unknown": "Невідомо",
}

STOCK_ACTIONS = {
    "none": "Без дії",
    "reserve": "Резервувати товар",
    "ship": "Списати зі складу (відправка)",
    "return": "Повернути на склад",
    "release": "Зняти резерв",
}


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(128), default="")
    role: Mapped[str] = mapped_column(String(20), default="manager")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    @property
    def display(self) -> str:
        return self.full_name or self.username

    @property
    def role_name(self) -> str:
        return ROLES.get(self.role, self.role)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")


class Status(Base):
    __tablename__ = "statuses"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    color: Mapped[str] = mapped_column(String(9), default="#64748b")
    sort: Mapped[int] = mapped_column(Integer, default=100)
    stock_action: Mapped[str] = mapped_column(String(10), default="none")
    counts_as_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_final: Mapped[bool] = mapped_column(Boolean, default=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    price: Mapped[Decimal] = mapped_column(Money, default=0)
    cost: Mapped[Decimal] = mapped_column(Money, default=0)  # собівартість
    weight: Mapped[Decimal] = mapped_column(Numeric(8, 3), default=Decimal("0.5"))  # кг
    stock: Mapped[int] = mapped_column(Integer, default=0)  # фізично на складі
    reserved: Mapped[int] = mapped_column(Integer, default=0)  # у резерві під замовлення
    min_stock: Mapped[int] = mapped_column(Integer, default=0)  # поріг для попередження
    is_upsell: Mapped[bool] = mapped_column(Boolean, default=False)  # товар для допродажу
    # до яких основних товарів пропонувати допродаж (id товарів); порожньо — до будь-якого замовлення
    upsell_for: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    @property
    def available(self) -> int:
        return (self.stock or 0) - (self.reserved or 0)


class Supplier(Base):
    __tablename__ = "suppliers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(32), default="")
    comment: Mapped[str] = mapped_column(Text, default="")


class Purchase(Base):
    __tablename__ = "purchases"
    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="draft")  # draft/ordered/received/cancelled
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    received_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    supplier: Mapped[Supplier | None] = relationship()
    items: Mapped[list[PurchaseItem]] = relationship(
        back_populates="purchase", cascade="all, delete-orphan", order_by="PurchaseItem.id"
    )

    @property
    def total(self) -> Decimal:
        return sum((Decimal(i.cost) * i.qty for i in self.items), Decimal(0))


class PurchaseItem(Base):
    __tablename__ = "purchase_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_id: Mapped[int] = mapped_column(ForeignKey("purchases.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    qty: Mapped[int] = mapped_column(Integer, default=1)
    cost: Mapped[Decimal] = mapped_column(Money, default=0)

    purchase: Mapped[Purchase] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()


class StockMovement(Base):
    __tablename__ = "stock_movements"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    kind: Mapped[str] = mapped_column(String(16))  # purchase/reserve/unreserve/ship/return/adjust
    stock_delta: Mapped[int] = mapped_column(Integer, default=0)
    reserved_delta: Mapped[int] = mapped_column(Integer, default=0)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True, index=True)
    purchase_id: Mapped[int | None] = mapped_column(ForeignKey("purchases.id"), nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    comment: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    product: Mapped[Product] = relationship()
    user: Mapped[User | None] = relationship()


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    status_id: Mapped[int] = mapped_column(ForeignKey("statuses.id"), index=True)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    customer_name: Mapped[str] = mapped_column(String(255), default="")  # «Прізвище Ім'я По батькові» — для пошуку й показу
    last_name: Mapped[str] = mapped_column(String(100), default="")
    first_name: Mapped[str] = mapped_column(String(100), default="")
    middle_name: Mapped[str] = mapped_column(String(100), default="")
    phone: Mapped[str] = mapped_column(String(32), default="", index=True)
    email: Mapped[str] = mapped_column(String(255), default="")
    comment: Mapped[str] = mapped_column(Text, default="")  # коментар клієнта / з лендингу

    # Доставка
    delivery_method: Mapped[str] = mapped_column(String(20), default="novaposhta")
    city_name: Mapped[str] = mapped_column(String(255), default="")
    city_ref: Mapped[str] = mapped_column(String(64), default="")
    warehouse_name: Mapped[str] = mapped_column(String(255), default="")
    warehouse_ref: Mapped[str] = mapped_column(String(64), default="")
    address: Mapped[str] = mapped_column(String(255), default="")
    postcode: Mapped[str] = mapped_column(String(10), default="")
    ttn: Mapped[str] = mapped_column(String(40), default="", index=True)
    carrier_ref: Mapped[str] = mapped_column(String(64), default="")
    delivery_cost: Mapped[Decimal] = mapped_column(Money, default=0)
    delivery_state: Mapped[str] = mapped_column(String(16), default="")
    delivery_status: Mapped[str] = mapped_column(String(255), default="")
    delivery_status_code: Mapped[str] = mapped_column(String(16), default="")
    delivery_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Гроші
    payment_type: Mapped[str] = mapped_column(String(10), default="cod")
    prepayment: Mapped[Decimal] = mapped_column(Money, default=0)
    discount: Mapped[Decimal] = mapped_column(Money, default=0)
    total: Mapped[Decimal] = mapped_column(Money, default=0)
    cod_amount: Mapped[Decimal] = mapped_column(Money, default=0)

    # Джерело трафіку
    site: Mapped[str] = mapped_column(String(255), default="")
    utm_source: Mapped[str] = mapped_column(String(255), default="")
    utm_medium: Mapped[str] = mapped_column(String(255), default="")
    utm_campaign: Mapped[str] = mapped_column(String(255), default="")
    utm_content: Mapped[str] = mapped_column(String(255), default="")
    utm_term: Mapped[str] = mapped_column(String(255), default="")
    ip: Mapped[str] = mapped_column(String(64), default="")

    duplicate_of_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True)
    stock_reserved: Mapped[bool] = mapped_column(Boolean, default=False)
    stock_shipped: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    status_changed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    status: Mapped[Status] = relationship()
    manager: Mapped[User | None] = relationship()
    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order", cascade="all, delete-orphan", order_by="OrderItem.id"
    )
    comments: Mapped[list[OrderComment]] = relationship(
        back_populates="order", cascade="all, delete-orphan", order_by="OrderComment.id"
    )
    payments: Mapped[list[Payment]] = relationship(
        back_populates="order", cascade="all, delete-orphan", order_by="Payment.id"
    )

    @property
    def delivery_method_name(self) -> str:
        return DELIVERY_METHODS.get(self.delivery_method, self.delivery_method)

    @property
    def payment_type_name(self) -> str:
        return PAYMENT_TYPES.get(self.payment_type, self.payment_type)

    @property
    def delivery_state_name(self) -> str:
        return DELIVERY_STATES.get(self.delivery_state, "") if self.delivery_state else ""

    @property
    def items_cost(self) -> Decimal:
        return sum((Decimal(i.cost or 0) * i.qty for i in self.items), Decimal(0))



Index("ix_orders_status_created", Order.status_id, Order.created_at)


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    price: Mapped[Decimal] = mapped_column(Money, default=0)
    cost: Mapped[Decimal] = mapped_column(Money, default=0)  # собівартість на момент продажу
    qty: Mapped[int] = mapped_column(Integer, default=1)
    is_upsell: Mapped[bool] = mapped_column(Boolean, default=False)
    # допродаж до якого основного товару (id товару); NULL — не допродаж або «до замовлення загалом»
    upsell_for_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True)

    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped[Product | None] = relationship(foreign_keys=[product_id])
    upsell_for: Mapped[Product | None] = relationship(foreign_keys=[upsell_for_id])

    @property
    def sum(self) -> Decimal:
        return Decimal(self.price or 0) * self.qty


class OrderComment(Base):
    __tablename__ = "order_comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    order: Mapped[Order] = relationship(back_populates="comments")
    user: Mapped[User | None] = relationship()


PAYMENT_KINDS = {"prepayment": "Передоплата", "cod": "Накладений платіж", "refund": "Повернення коштів"}
PAYMENT_STATUSES = {
    "expected": "Очікується",
    "collected": "Оплачено клієнтом",
    "received": "Гроші отримано",
    "cancelled": "Скасовано",
}


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(16), default="cod")
    amount: Mapped[Decimal] = mapped_column(Money, default=0)
    status: Mapped[str] = mapped_column(String(16), default="expected", index=True)
    method: Mapped[str] = mapped_column(String(20), default="")
    reference: Mapped[str] = mapped_column(String(255), default="")
    received_amount: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    comment: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    collected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    order: Mapped[Order] = relationship(back_populates="payments")

    @property
    def kind_name(self) -> str:
        return PAYMENT_KINDS.get(self.kind, self.kind)

    @property
    def status_name(self) -> str:
        return PAYMENT_STATUSES.get(self.status, self.status)


class SmsTemplate(Base):
    __tablename__ = "sms_templates"
    id: Mapped[int] = mapped_column(primary_key=True)
    status_id: Mapped[int] = mapped_column(ForeignKey("statuses.id"))
    channel: Mapped[str] = mapped_column(String(10), default="sms")  # sms / viber / hybrid
    text: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    status: Mapped[Status] = relationship()


class SmsMessage(Base):
    __tablename__ = "sms_messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=True, index=True)
    phone: Mapped[str] = mapped_column(String(32))
    channel: Mapped[str] = mapped_column(String(10), default="sms")
    text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(10), default="queued", index=True)  # queued/sent/failed
    provider_id: Mapped[str] = mapped_column(String(64), default="")
    error: Mapped[str] = mapped_column(String(255), default="")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    entity: Mapped[str] = mapped_column(String(32))
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(64))
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    user: Mapped[User | None] = relationship()


Index("ix_audit_entity", AuditLog.entity, AuditLog.entity_id)
