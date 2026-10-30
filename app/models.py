from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy import event, inspect
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

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
    "rozetka": "Rozetka Delivery",  # доставка у відділення ROZETKA; ТТН RMP-… створюється в кабінеті продавця Rozetka
    "pickup": "Самовивіз",
    "courier": "Кур'єр",
}

# Типи оплати в чеку Checkbox (вид оплати CRM → один із цих), як у модулі Checkbox LP-CRM
CHECKBOX_PAYMENTS = {
    "cash": "Готівка",
    "card": "Картка",
    "novapay": "Платіж через інтегратора NovaPay",
    "rozetkapay": "Платіж через інтегратора RozetkaPay",
    "monopay": "Платіж через інтегратора mono",
    "liqpay": "Платіж через інтегратора LiqPay",
    "wayforpay": "Платіж через інтегратора WayForPay",
    "easypay": "Платіж через інтегратора EasyPay",
    "acquiring": "Інтернет еквайринг",
    "iban": "За реквізитами (IBAN)",
    "internet_banking": "Інтернет банкінг",
    "gift": "Подарунковий сертифікат",
    "coupon": "Талон",
    "token": "Жетон",
    "nnpp": "Переказ через ННПП",
    "ptks_nnpp": "Переказ через ПТКС ННПП",
    "ptks_bank": "Переказ через ПТКС банку",
    "current_account": "З поточного рахунку",
    "chip": "Фішка",
    "e_money": "Електронний грошовий замінник",
    "game_money": "Ігровий замінник гривні",
}

# Країни замовлень (код ISO → назва), як у LP-CRM
COUNTRIES = {
    "UA": "Україна", "MD": "Молдова", "PL": "Польща", "DE": "Німеччина", "CZ": "Чехія", "SK": "Словаччина",
    "RO": "Румунія", "HU": "Угорщина", "LT": "Литва", "LV": "Латвія", "EE": "Естонія", "GB": "Велика Британія",
    "US": "США", "CA": "Канада", "IT": "Італія", "ES": "Іспанія", "FR": "Франція", "NL": "Нідерланди",
    "BE": "Бельгія", "AT": "Австрія", "CH": "Швейцарія", "IE": "Ірландія", "PT": "Португалія", "GR": "Греція",
    "BG": "Болгарія", "HR": "Хорватія", "SI": "Словенія", "RS": "Сербія", "ME": "Чорногорія", "MK": "Північна Македонія",
    "AL": "Албанія", "BA": "Боснія і Герцеговина", "DK": "Данія", "SE": "Швеція", "NO": "Норвегія", "FI": "Фінляндія",
    "IS": "Ісландія", "LU": "Люксембург", "LI": "Ліхтенштейн", "MC": "Монако", "GE": "Грузія", "AM": "Вірменія",
    "AZ": "Азербайджан", "KZ": "Казахстан", "UZ": "Узбекистан", "KG": "Киргизстан", "TJ": "Таджикистан",
    "TM": "Туркменістан", "TR": "Туреччина", "IL": "Ізраїль", "AE": "ОАЕ", "SA": "Саудівська Аравія", "EG": "Єгипет",
    "IQ": "Ірак", "IN": "Індія", "PK": "Пакистан", "BD": "Бангладеш", "CN": "Китай", "JP": "Японія",
    "KR": "Південна Корея", "TW": "Тайвань", "VN": "Вʼєтнам", "ID": "Індонезія", "MN": "Монголія",
}

NP_COD_KINDS = {"": "не перевіряти", "control": "контроль оплати", "backward": "грошовий переказ", "none": "без післяплати"}

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
    # відділи, замовлення яких бачить користувач (id відділів); порожньо — усі
    offices: Mapped[list] = mapped_column(JSON, default=list)

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
    # розділ: lead — «Ліди» (обробка заявки: новий, недозвон, передзвонити…), order — «Замовлення»
    stage: Mapped[str] = mapped_column(String(8), default="order")


class Category(Base):
    """Категорія товарів (два рівні: розділ і підкатегорія), як у LP-CRM."""
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    sort: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Manufacturer(Base):
    """Виробник / бренд."""
    __tablename__ = "manufacturers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class AttributeGroup(Base):
    """Категорія атрибутів: «Колір», «Розмір», «Пам'ять»…"""
    __tablename__ = "attribute_groups"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    sort: Mapped[int] = mapped_column(Integer, default=100)
    attributes: Mapped[list[Attribute]] = relationship(back_populates="group", order_by="Attribute.sort, Attribute.id",
                                                        cascade="all, delete-orphan")


class Attribute(Base):
    """Значення атрибута: «Чорний», «XL», «64 ГБ»."""
    __tablename__ = "attributes"
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("attribute_groups.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    sort: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    group: Mapped[AttributeGroup] = relationship(back_populates="attributes")


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
    length: Mapped[Decimal] = mapped_column(Numeric(7, 1), default=0)  # розміри в упаковці, см — для ТТН
    width: Mapped[Decimal] = mapped_column(Numeric(7, 1), default=0)
    height: Mapped[Decimal] = mapped_column(Numeric(7, 1), default=0)
    ship_description: Mapped[str] = mapped_column(String(255), default="")  # опис відправлення для НП
    warranty_months: Mapped[int] = mapped_column(Integer, default=0)  # гарантія, міс.; 0 — як у налаштуваннях документів
    is_upsell: Mapped[bool] = mapped_column(Boolean, default=False)  # товар для допродажу
    # до яких основних товарів пропонувати допродаж (id товарів); порожньо — до будь-якого замовлення
    upsell_for: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    # картка товару (етап 6)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    manufacturer_id: Mapped[int | None] = mapped_column(ForeignKey("manufacturers.id", ondelete="SET NULL"), nullable=True)
    model: Mapped[str] = mapped_column(String(120), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    countries: Mapped[list] = mapped_column(JSON, default=list)  # країни продажу; порожньо — усі
    spec_price: Mapped[Decimal] = mapped_column(Money, default=0)  # акційна ціна (зі знижкою); 0 — без акції
    wholesale_price: Mapped[Decimal] = mapped_column(Money, default=0)

    category: Mapped[Category | None] = relationship()
    manufacturer: Mapped[Manufacturer | None] = relationship()
    variants: Mapped[list[ProductVariant]] = relationship(back_populates="product", cascade="all, delete-orphan",
                                                          order_by="ProductVariant.sort, ProductVariant.id")
    photos: Mapped[list[ProductPhoto]] = relationship(back_populates="product", cascade="all, delete-orphan",
                                                      order_by="ProductPhoto.sort, ProductPhoto.id")

    @property
    def available(self) -> int:
        return (self.stock or 0) - (self.reserved or 0)

    @property
    def sale_price(self) -> Decimal:
        """Ціна в замовленні: акційна, якщо задана, інакше звичайна."""
        return Decimal(self.spec_price) if self.spec_price and Decimal(self.spec_price) > 0 else Decimal(self.price or 0)

    @property
    def discount_percent(self) -> int:
        if not self.spec_price or not self.price or Decimal(self.spec_price) <= 0:
            return 0
        return max(0, round((1 - Decimal(self.spec_price) / Decimal(self.price)) * 100))


class ProductVariant(Base):
    """Варіант товару (поєднання атрибутів: «Чорний / XL») зі своїм залишком і, за потреби, ціною та артикулом."""
    __tablename__ = "product_variants"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    sku: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    attribute_ids: Mapped[list] = mapped_column(JSON, default=list)
    price: Mapped[Decimal | None] = mapped_column(Money, nullable=True)  # NULL — ціна товару
    stock: Mapped[int] = mapped_column(Integer, default=0)
    reserved: Mapped[int] = mapped_column(Integer, default=0)
    sort: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    product: Mapped[Product] = relationship(back_populates="variants")

    @property
    def available(self) -> int:
        return (self.stock or 0) - (self.reserved or 0)


class ProductPhoto(Base):
    """Фото товару: файл у каталозі MEDIA_DIR/products. Перше за порядком — головне."""
    __tablename__ = "product_photos"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    file: Mapped[str] = mapped_column(String(255))
    sort: Mapped[int] = mapped_column(Integer, default=100)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    product: Mapped[Product] = relationship(back_populates="photos")


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
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)
    qty: Mapped[int] = mapped_column(Integer, default=1)
    cost: Mapped[Decimal] = mapped_column(Money, default=0)

    purchase: Mapped[Purchase] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()


class StockMovement(Base):
    __tablename__ = "stock_movements"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True, index=True)
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


class PaymentMethod(Base):
    """Вид оплати (довідник як у LP-CRM). id збігаються з LP-CRM — для перенесення даних."""
    __tablename__ = "payment_methods"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    icon: Mapped[str] = mapped_column(String(32), default="cash")
    # як рахувати гроші: cod — увесь залишок післяплатою, partial — передоплата + післяплата решти,
    # prepaid — оплачено повністю, при створенні ТТН післяплати немає
    kind: Mapped[str] = mapped_column(String(10), default="cod")
    checkbox_type: Mapped[str] = mapped_column(String(20), default="")  # тип оплати в чеку Checkbox
    # що має стояти в ТТН Нової Пошти (колонка «Перевірка оплати»): "" — не перевіряти,
    # control — контроль оплати (NovaPay), backward — грошовий переказ, none — без післяплати
    np_cod: Mapped[str] = mapped_column(String(10), default="")
    image: Mapped[str] = mapped_column(String(160), default="")  # свій значок (файл у MEDIA_DIR/pay), напр. офіційний логотип
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort: Mapped[int] = mapped_column(Integer, default=100)


class LegalEntity(Base):
    """Юридична особа (ФОП / ТОВ), від імені якої продається замовлення. За нею обирається каса Checkbox
    (і ключ Нової Пошти, якщо його прив'язано). Одна юрособа — за замовчуванням."""
    __tablename__ = "legal_entities"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(20), default="")  # ЄДРПОУ / РНОКПП
    iban: Mapped[str] = mapped_column(String(34), default="")
    # реквізити для документів (видаткова, рахунок-фактура, гарантійний талон)
    code_label: Mapped[str] = mapped_column(String(10), default="РНОКПП")  # РНОКПП / ІПН / ЄДРПОУ
    address: Mapped[str] = mapped_column(String(255), default="")
    bank: Mapped[str] = mapped_column(String(160), default="")
    phone: Mapped[str] = mapped_column(String(40), default="")
    vat_note: Mapped[str] = mapped_column(String(80), default="Без ПДВ")
    signer: Mapped[str] = mapped_column(String(120), default="")  # хто підписує документи: «Прізвище І.П.»
    # префікси нумерації документів цієї юрособи; порожньо — загальні з «Налаштування → Документи»
    waybill_prefix: Mapped[str | None] = mapped_column(String(10), nullable=True)
    invoice_prefix: Mapped[str | None] = mapped_column(String(10), nullable=True)
    warranty_prefix: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort: Mapped[int] = mapped_column(Integer, default=100)


class LegalEntityAccount(Base):
    """Рахунок юрособи, куди надходять передоплати: картка, IBAN, готівка, сервіс (Monobank · ФОП Максимчук)."""
    __tablename__ = "legal_entity_accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    legal_entity_id: Mapped[int] = mapped_column(ForeignKey("legal_entities.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    kind: Mapped[str] = mapped_column(String(10), default="card")  # card / iban / cash / service
    iban: Mapped[str] = mapped_column(String(34), default="")
    card_mask: Mapped[str] = mapped_column(String(20), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort: Mapped[int] = mapped_column(Integer, default=100)


class NpAccount(Base):
    """Ключ API Нової Пошти (ФОП) з типовими параметрами ТТН. Ключів може бути кілька."""
    __tablename__ = "np_accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), default="")
    api_key: Mapped[str] = mapped_column(String(64), default="")
    sender_ref: Mapped[str] = mapped_column(String(255), default="")
    sender_name: Mapped[str] = mapped_column(String(255), default="")
    contact_ref: Mapped[str] = mapped_column(String(255), default="")
    contact_name: Mapped[str] = mapped_column(String(255), default="")
    sender_phone: Mapped[str] = mapped_column(String(255), default="")
    city_name: Mapped[str] = mapped_column(String(255), default="")
    city_ref: Mapped[str] = mapped_column(String(255), default="")
    warehouse_name: Mapped[str] = mapped_column(String(255), default="")
    warehouse_ref: Mapped[str] = mapped_column(String(255), default="")
    payer: Mapped[str] = mapped_column(String(16), default="Recipient")  # Recipient / Sender / ThirdPerson
    cargo_type: Mapped[str] = mapped_column(String(16), default="Parcel")  # Parcel / Cargo / Documents / TiresWheels / Pallet
    service_type: Mapped[str] = mapped_column(String(24), default="WarehouseWarehouse")
    cod_mode: Mapped[str] = mapped_column(String(16), default="backward")  # backward — грошовий переказ, afterpayment — контроль оплати
    cod_payer: Mapped[str] = mapped_column(String(16), default="Recipient")  # хто платить за переказ
    info_comment: Mapped[bool] = mapped_column(Boolean, default=False)  # «Додаткова інформація»: коментар замовлення
    info_items: Mapped[bool] = mapped_column(Boolean, default=True)  # … список товарів
    info_item_ids: Mapped[bool] = mapped_column(Boolean, default=False)  # … номери товарів
    default_weight: Mapped[Decimal] = mapped_column(Numeric(8, 3), default=Decimal("0.5"))
    seat_size: Mapped[str] = mapped_column(String(32), default="20x15x10")
    description: Mapped[str] = mapped_column(String(255), default="Товар")
    office_id: Mapped[int | None] = mapped_column(ForeignKey("offices.id", ondelete="SET NULL"), nullable=True)
    legal_entity_id: Mapped[int | None] = mapped_column(ForeignKey("legal_entities.id", ondelete="SET NULL"), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # кеш із кабінету НП: контрагенти й контактні особи для вибору в налаштуваннях
    directory: Mapped[dict] = mapped_column(JSON, default=dict)


class NpStatusRule(Base):
    """Автозміна статусу: статус ТТН Нової Пошти → статус замовлення, крім статусів-винятків."""
    __tablename__ = "np_status_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    np_code: Mapped[str] = mapped_column(String(8))
    status_id: Mapped[int] = mapped_column(ForeignKey("statuses.id", ondelete="CASCADE"))
    except_ids: Mapped[list] = mapped_column(JSON, default=list)
    sort: Mapped[int] = mapped_column(Integer, default=100)


class MarketplaceShop(Base):
    """Магазин на маркетплейсі (Rozetka, Prom): імпорт замовлень і передача статусів назад."""
    __tablename__ = "marketplace_shops"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(16))  # rozetka / prom
    name: Mapped[str] = mapped_column(String(160), default="")
    login: Mapped[str] = mapped_column(String(160), default="")  # Rozetka: логін кабінету продавця
    secret: Mapped[str] = mapped_column(String(255), default="")  # Rozetka: пароль; Prom: API-токен
    office_id: Mapped[int | None] = mapped_column(ForeignKey("offices.id", ondelete="SET NULL"), nullable=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("order_sources.id", ondelete="SET NULL"), nullable=True)
    import_status_id: Mapped[int | None] = mapped_column(ForeignKey("statuses.id", ondelete="SET NULL"), nullable=True)
    extra_field: Mapped[int] = mapped_column(Integer, default=1)  # у яке додаткове поле писати «Rozetka(магазин)», 0 — ні
    status_map: Mapped[dict] = mapped_column(JSON, default=dict)  # id статусу CRM → статус маркетплейсу
    payment_map: Mapped[dict] = mapped_column(JSON, default=dict)  # спосіб оплати маркетплейсу → id виду оплати
    delivery_map: Mapped[dict] = mapped_column(JSON, default=dict)  # служба доставки маркетплейсу → код доставки CRM
    directory: Mapped[dict] = mapped_column(JSON, default=dict)  # статуси маркетплейсу, бачені способи оплати й доставки
    token: Mapped[str] = mapped_column(Text, default="")  # кеш токена Rozetka
    token_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    since: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # з якої дати імпортувати
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str] = mapped_column(Text, default="")
    imported: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class CheckboxCashier(Base):
    """Каса Checkbox (ПРРО): одна каса — один ФОП. Умова вибору перевіряється згори вниз."""
    __tablename__ = "checkbox_cashiers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), default="")  # ПІБ касира — друкується в чеку
    license_key: Mapped[str] = mapped_column(String(128), default="")
    login: Mapped[str] = mapped_column(String(128), default="")
    password: Mapped[str] = mapped_column(String(128), default="")
    test_mode: Mapped[bool] = mapped_column(Boolean, default=False)  # тестовий сервер Checkbox
    auto_shift: Mapped[bool] = mapped_column(Boolean, default=True)  # відкривати зміну для чека, закривати о 23:00
    legal_entity_id: Mapped[int | None] = mapped_column(ForeignKey("legal_entities.id", ondelete="SET NULL"), nullable=True)
    # застаріле (до юросіб): умова вибору каси; використовується, лише якщо юросіб ще не заведено
    condition: Mapped[str] = mapped_column(String(16), default="none")  # none / office / user / np_account
    condition_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sort: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    token: Mapped[str] = mapped_column(Text, default="")
    token_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str] = mapped_column(Text, default="")


class CheckboxReceipt(Base):
    """Чек Checkbox по замовленню: продажу, повернення, передоплати, післяплати."""
    __tablename__ = "checkbox_receipts"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    cashier_id: Mapped[int | None] = mapped_column(ForeignKey("checkbox_cashiers.id", ondelete="SET NULL"), nullable=True)
    kind: Mapped[str] = mapped_column(String(10))  # sell / return / prepay / postpay
    checkbox_id: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(20), default="new")  # new / done / error
    fiscal_code: Mapped[str] = mapped_column(String(64), default="")
    total: Mapped[Decimal] = mapped_column(Money, default=0)
    error: Mapped[str] = mapped_column(Text, default="")
    test: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Office(Base):
    """Відділ (ФОП, PROM, сайт, OLX…): доступ менеджерів, вибір каси Checkbox, замовлення маркетплейсів."""
    __tablename__ = "offices"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort: Mapped[int] = mapped_column(Integer, default=100)


class StatusReason(Base):
    """Причина (атрибут статусу): «Дорого», «Дубль», «Не відповідає»… — до яких статусів застосовна."""
    __tablename__ = "status_reasons"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    status_ids: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort: Mapped[int] = mapped_column(Integer, default=100)


class OrderMark(Base):
    """Позначка замовлення: «Терміново», «Покласти чек», «Написати в Rozetka»…"""
    __tablename__ = "order_marks"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    icon: Mapped[str] = mapped_column(String(24), default="tag")  # ключ значка (frontend/src/components/marks.tsx)
    color: Mapped[str] = mapped_column(String(16), default="#475569")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort: Mapped[int] = mapped_column(Integer, default=100)


class OrderSource(Base):
    """Джерело замовлення (сайт, Instagram, Rozetka…). Додається лише в налаштуваннях; належить відділу —
    відділ замовлення визначається його джерелом."""
    __tablename__ = "order_sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    office_id: Mapped[int | None] = mapped_column(ForeignKey("offices.id", ondelete="SET NULL"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort: Mapped[int] = mapped_column(Integer, default=100)


class CustomerGroup(Base):
    """Група покупців: «Покупець», «Оптовик», «Дропшипер», «Партнер»…"""
    __tablename__ = "customer_groups"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    color: Mapped[str] = mapped_column(String(9), default="#64748b")
    sort: Mapped[int] = mapped_column(Integer, default=100)


class Customer(Base):
    """Покупець: один на номер телефону. Історію й суми рахуємо із замовлень."""
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    phone2: Mapped[str] = mapped_column(String(20), default="", index=True)  # додатковий телефон (пошук покупця за обома)
    name: Mapped[str] = mapped_column(String(255), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    country: Mapped[str] = mapped_column(String(2), default="UA")
    group_id: Mapped[int | None] = mapped_column(ForeignKey("customer_groups.id", ondelete="SET NULL"), nullable=True)
    comment: Mapped[str] = mapped_column(Text, default="")
    is_blacklisted: Mapped[bool] = mapped_column(Boolean, default=False)
    blacklist_reason: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    group: Mapped[CustomerGroup | None] = relationship()


class BlockedIp(Base):
    """Заблокована IP-адреса: заявки з неї через webhook не приймаються."""
    __tablename__ = "blocked_ips"
    id: Mapped[int] = mapped_column(primary_key=True)
    ip: Mapped[str] = mapped_column(String(64), unique=True)
    comment: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    status_id: Mapped[int] = mapped_column(ForeignKey("statuses.id"), index=True)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    office_id: Mapped[int | None] = mapped_column(ForeignKey("offices.id"), nullable=True, index=True)
    np_account_id: Mapped[int | None] = mapped_column(ForeignKey("np_accounts.id", ondelete="SET NULL"), nullable=True)
    shop_id: Mapped[int | None] = mapped_column(ForeignKey("marketplace_shops.id", ondelete="SET NULL"), nullable=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    legal_entity_id: Mapped[int | None] = mapped_column(ForeignKey("legal_entities.id", ondelete="SET NULL"), nullable=True, index=True)
    external_id: Mapped[str] = mapped_column(String(64), default="", index=True)  # номер замовлення на маркетплейсі
    external_status: Mapped[str] = mapped_column(String(120), default="")
    reason_id: Mapped[int | None] = mapped_column(ForeignKey("status_reasons.id"), nullable=True)
    mark_id: Mapped[int | None] = mapped_column(ForeignKey("order_marks.id"), nullable=True)
    remind_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)  # нагадати менеджеру / час передзвону ліда
    call_attempts: Mapped[int] = mapped_column(Integer, default=0)  # спроби дзвінка ліду (недодзвон, передзвонити)
    last_call_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    converted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)  # коли з ліда створено замовлення
    label_printed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # «наклейку надруковано» (Що лишилось)
    np_registry_ref: Mapped[str] = mapped_column(String(40), default="")  # реєстр НП (ScanSheet), номер
    delivery_eta: Mapped[date | None] = mapped_column(Date, nullable=True)  # очікувана дата доставки
    country: Mapped[str] = mapped_column(String(2), default="UA")

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
    # що фактично стоїть у ТТН (з відповіді НП при створенні або з трекінгу): "" — ще невідомо,
    # none — без післяплати, backward — грошовий переказ, control — контроль оплати
    ttn_cod_kind: Mapped[str] = mapped_column(String(10), default="")
    ttn_cod_sum: Mapped[Decimal] = mapped_column(Money, default=0)

    # Гроші
    payment_type: Mapped[str] = mapped_column(String(10), default="cod")  # cod / partial / prepaid — із виду оплати
    payment_method_id: Mapped[int | None] = mapped_column(ForeignKey("payment_methods.id"), nullable=True)
    prepayment: Mapped[Decimal] = mapped_column(Money, default=0)
    discount: Mapped[Decimal] = mapped_column(Money, default=0)
    total: Mapped[Decimal] = mapped_column(Money, default=0)
    cod_amount: Mapped[Decimal] = mapped_column(Money, default=0)

    # Джерело трафіку
    source_id: Mapped[int | None] = mapped_column(ForeignKey("order_sources.id"), nullable=True, index=True)
    extra1: Mapped[str] = mapped_column(String(255), default="")  # додаткові поля 1–4, назви — у налаштуваннях
    extra2: Mapped[str] = mapped_column(String(255), default="")
    extra3: Mapped[str] = mapped_column(String(255), default="")
    extra4: Mapped[str] = mapped_column(String(255), default="")
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
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, index=True)
    status_changed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)  # закріплене за менеджером
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)  # перший статус «апрув»
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)

    status: Mapped[Status] = relationship()
    manager: Mapped[User | None] = relationship()
    payment_method: Mapped[PaymentMethod | None] = relationship()
    source: Mapped[OrderSource | None] = relationship()
    customer: Mapped[Customer | None] = relationship()
    legal_entity: Mapped[LegalEntity | None] = relationship()
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
# один номер маркетплейсу — одне замовлення в магазині (захист від подвійного імпорту)
Index("ux_orders_shop_external", Order.shop_id, Order.external_id, unique=True,
      postgresql_where=text("shop_id IS NOT NULL"))


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
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)

    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped[Product | None] = relationship(foreign_keys=[product_id])
    upsell_for: Mapped[Product | None] = relationship(foreign_keys=[upsell_for_id])
    variant: Mapped[ProductVariant | None] = relationship()

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
    # куди надійшли кошти й хто підтвердив (передоплата)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("legal_entity_accounts.id", ondelete="SET NULL"), nullable=True)
    confirmed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    order: Mapped[Order] = relationship(back_populates="payments")
    account: Mapped[LegalEntityAccount | None] = relationship()
    confirmed_by: Mapped[User | None] = relationship()

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


DOC_KINDS = {"waybill": "Видаткова накладна", "invoice": "Рахунок-фактура", "warranty": "Гарантійний талон"}


class IssuedDocument(Base):
    """Виданий документ (UI-DESIGN §6.1): номер окремий для юрособи й типу й не повторюється; знімок даних на момент видачі —
    документ через рік виглядає так само; перевипуск не стирає старий (state=void + посилання на нову версію)."""
    __tablename__ = "issued_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(10))  # waybill / invoice / warranty
    legal_entity_id: Mapped[int | None] = mapped_column(ForeignKey("legal_entities.id", ondelete="SET NULL"), nullable=True, index=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    number: Mapped[int] = mapped_column(Integer)
    number_text: Mapped[str] = mapped_column(String(30))
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    total: Mapped[Decimal] = mapped_column(Money, default=0)
    snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    payload_hash: Mapped[str] = mapped_column(String(64), default="")
    state: Mapped[str] = mapped_column(String(10), default="active")  # active / void
    replaced_by_id: Mapped[int | None] = mapped_column(ForeignKey("issued_documents.id", ondelete="SET NULL"), nullable=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    print_count: Mapped[int] = mapped_column(Integer, default=0)
    last_printed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    legal_entity: Mapped[LegalEntity | None] = relationship()
    created_by: Mapped[User | None] = relationship()


Index("ux_issued_documents_number", IssuedDocument.legal_entity_id, IssuedDocument.kind, IssuedDocument.number, unique=True)


class DocumentCounter(Base):
    """Наступний номер документа для юрособи й типу. legal_entity_id = 0 — документи без юрособи."""
    __tablename__ = "document_counters"
    legal_entity_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(10), primary_key=True)
    next_number: Mapped[int] = mapped_column(Integer, default=1)


class SavedFilter(Base):
    """Збережений фільтр списку (бокова панель): назва, кольорова мітка, рядок адреси «?status=…&manager=…»."""
    __tablename__ = "saved_filters"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    section: Mapped[str] = mapped_column(String(20), default="orders")
    name: Mapped[str] = mapped_column(String(80))
    color: Mapped[str] = mapped_column(String(9), default="#2E6BE6")
    query: Mapped[str] = mapped_column(Text, default="")
    sort: Mapped[int] = mapped_column(Integer, default=100)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class UserPref(Base):
    """Налаштування користувача: колонки списків, щільність, згорнута панель, поточний відділ."""
    __tablename__ = "user_prefs"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    value: Mapped[dict | list | str | int | None] = mapped_column(JSON, nullable=True)


# ---------------------------------------------------------------- автоматичні дати замовлення
@event.listens_for(Session, "before_flush")
def _order_dates(session: Session, _ctx, _instances):
    """«Закріплене» — коли замовлення отримало менеджера; «підтверджене» — перший статус, що рахується апрувом.
    Працює для будь-якого шляху зміни: картка, API, масові дії, webhook, маркетплейси."""
    now = utcnow()
    for o in [*session.new, *session.dirty]:
        if not isinstance(o, Order):
            continue
        state = inspect(o)
        is_new = o in session.new
        if is_new or state.attrs.manager_id.history.has_changes() or state.attrs.manager.history.has_changes():
            has_manager = o.manager_id is not None or o.__dict__.get("manager") is not None
            if not has_manager:
                o.assigned_at = None
            elif not (is_new and o.assigned_at):
                o.assigned_at = now
        if is_new and o.legal_entity_id is None and o.__dict__.get("legal_entity") is None:
            default = session.query(LegalEntity.id).filter(LegalEntity.is_default.is_(True), LegalEntity.is_active.is_(True)).first()
            if default:
                o.legal_entity_id = default[0]
        if o.source_id and (is_new or state.attrs.source_id.history.has_changes()):
            src = session.get(OrderSource, o.source_id)
            if src is not None and src.office_id:
                o.office_id = src.office_id  # відділ = сукупність джерел
        if o.confirmed_at is None and (is_new or state.attrs.status_id.history.has_changes()
                                       or state.attrs.status.history.has_changes()):
            st = o.__dict__.get("status") or (session.get(Status, o.status_id) if o.status_id else None)
            if st is not None and st.counts_as_approved:
                o.confirmed_at = now
