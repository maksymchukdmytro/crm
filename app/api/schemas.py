"""Схеми JSON API (Pydantic). З них будуються документація OpenAPI (/api/docs) і типи для фронтенду.

Відповіді будуються функціями j_* у common.py і перевіряються цими схемами.
Запити з частковими змінами (PATCH) — усі поля необов'язкові; змінюються лише передані.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Num = float | int
Money = float | int | str  # у запитах суму можна передати рядком «399,50»


class Out(BaseModel):
    model_config = ConfigDict(extra="ignore")


class In(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Ok(Out):
    ok: bool = True


# ---------------------------------------------------------------- довідники
class UserOut(Out):
    id: int
    username: str
    name: str
    full_name: str
    role: Literal["admin", "manager", "warehouse"]
    role_name: str
    is_active: bool
    last_login_at: str | None = None
    offices: list[int] = Field(default_factory=list, description="Доступні відділи; порожньо — усі")


class StatusOut(Out):
    id: int
    code: str
    name: str
    color: str
    sort: int
    stock_action: str
    approved: bool
    final: bool
    system: bool
    active: bool


class ProductOut(Out):
    id: int
    sku: str
    name: str
    price: float
    cost: float
    weight: float
    stock: int
    reserved: int
    available: int
    min_stock: int
    length: float = 0
    width: float = 0
    height: float = 0
    ship_description: str = ""
    upsell: bool
    upsell_for: list[int] = Field(default_factory=list, description="Допродаж: до яких товарів пропонувати (порожньо — до будь-якого)")
    active: bool


class CarrierOut(Out):
    name: str
    beta: bool
    configured: bool


class NpAccountShort(Out):
    id: int
    name: str
    office_id: int | None = None
    is_default: bool = False


class PaymentMethodOut(Out):
    id: int
    name: str
    icon: str
    kind: Literal["cod", "partial", "prepaid"] = Field(description="cod — післяплата, partial — передоплата + післяплата, prepaid — без післяплати")
    checkbox_type: str
    active: bool
    sort: int


class SourceOut(Out):
    """Довідник «назва + активний + порядок»: джерела, відділи, позначки."""
    id: int
    name: str
    active: bool
    sort: int


class ReasonOut(SourceOut):
    status_ids: list[int] = Field(default_factory=list, description="До яких статусів застосовна причина")


class MetaOut(Out):
    user: UserOut
    company: str
    nav: list[str]
    statuses: list[StatusOut]
    managers: list[UserOut]
    products: list[ProductOut]
    delivery_methods: dict[str, str]
    delivery_states: dict[str, str]
    payment_types: dict[str, str]
    payment_methods: list[PaymentMethodOut] = Field(default_factory=list, description="Активні види оплат")
    order_sources: list[SourceOut] = Field(default_factory=list)
    offices: list[SourceOut] = Field(default_factory=list)
    reasons: list[ReasonOut] = Field(default_factory=list)
    marks: list[SourceOut] = Field(default_factory=list)
    countries: dict[str, str] = Field(default_factory=dict)
    np_accounts: list[NpAccountShort] = Field(default_factory=list)
    shops: dict[str, str] = Field(default_factory=dict, description="id магазину → «Rozetka · назва»")
    extra_fields: list[str] = Field(default_factory=list, description="Назви додаткових полів 1–4")
    checkbox_payments: dict[str, str] = Field(default_factory=dict)
    payment_kinds: dict[str, str]
    payment_statuses: dict[str, str]
    stock_actions: dict[str, str]
    roles: dict[str, str]
    carriers: dict[str, CarrierOut]
    sms_ready: bool
    managers_see_own_only: bool
    realtime: bool
    root: str


class LoginIn(In):
    username: str
    password: str


class LoginOut(Out):
    user: UserOut


class MeIn(In):
    full_name: str | None = None
    old_password: str | None = None
    new_password: str | None = None


# ---------------------------------------------------------------- замовлення
class OrderRowItem(Out):
    name: str
    qty: int
    upsell: bool


class OrderRowOut(Out):
    id: int
    status_id: int
    manager_id: int | None
    office_id: int | None = None
    np_account_id: int | None = None
    shop_id: int | None = None
    external_id: str = ""
    external_status: str = ""
    reason_id: int | None = None
    mark_id: int | None = None
    remind_at: str | None = None
    country: str = "UA"
    customer_name: str
    phone: str
    items: list[OrderRowItem]
    total: float
    cod_amount: float
    payment_type: str
    payment_method_id: int | None = None
    source_id: int | None = None
    delivery_method: str
    city_name: str
    ttn: str
    delivery_state: str
    delivery_status: str
    utm_source: str
    utm_campaign: str
    site: str
    duplicate_of_id: int | None
    created_at: str | None
    status_changed_at: str | None


class OrderListOut(Out):
    items: list[OrderRowOut]
    next: int | None
    total: int | None = None
    counts: dict[str, int] | None = None
    all: int | None = None


class OrderItemOut(Out):
    id: int | None = None
    product_id: int | None
    name: str
    price: float
    qty: int
    upsell: bool
    upsell_for: int | None = None
    upsell_for_name: str = ""
    base_price: float | None = Field(None, description="Ціна товару в каталозі — щоб показати, що ціну в замовленні змінено")
    sku: str = ""
    available: int | None = None


class PaymentOut(Out):
    id: int
    order_id: int
    kind: str
    kind_name: str
    amount: float
    status: str
    status_name: str
    method: str
    reference: str
    received_amount: float | None
    created_at: str | None
    collected_at: str | None
    received_at: str | None
    ttn: str | None = None
    customer: str | None = None


class CommentOut(Out):
    id: int
    text: str
    user: str
    created_at: str | None


class HistoryOut(Out):
    id: int
    user: str
    action: str
    details: str
    created_at: str | None


class SmsOut(Out):
    id: int
    text: str
    channel: str
    status: str
    error: str
    created_at: str | None


class OrderOut(Out):
    id: int
    status_id: int
    manager_id: int | None
    office_id: int | None = None
    np_account_id: int | None = None
    shop_id: int | None = None
    external_id: str = ""
    external_status: str = ""
    reason_id: int | None = None
    mark_id: int | None = None
    remind_at: str | None = None
    country: str = "UA"
    manager: UserOut | None
    customer_name: str
    last_name: str = ""
    first_name: str = ""
    middle_name: str = ""
    phone: str
    email: str
    comment: str
    delivery_method: str
    city_name: str
    city_ref: str
    warehouse_name: str
    warehouse_ref: str
    address: str
    postcode: str
    ttn: str
    carrier_ref: str
    delivery_state: str
    delivery_status: str
    payment_type: str
    payment_method_id: int | None = None
    source_id: int | None = None
    extra1: str = ""
    extra2: str = ""
    extra3: str = ""
    extra4: str = ""
    site: str
    utm_source: str
    utm_medium: str
    utm_campaign: str
    utm_content: str
    utm_term: str
    ip: str
    delivery_cost: float
    prepayment: float
    discount: float
    total: float
    cod_amount: float
    duplicate_of_id: int | None
    stock_reserved: bool
    stock_shipped: bool
    created_at: str | None
    updated_at: str | None
    shipped_at: str | None
    delivered_at: str | None
    delivery_checked_at: str | None
    version: str
    items: list[OrderItemOut]
    payments: list[PaymentOut]
    comments: list[CommentOut]
    history: list[HistoryOut]
    sms: list[SmsOut]
    others: list[OrderRowOut]
    receipts: list["ReceiptOut"] = Field(default_factory=list)
    checkbox_ready: bool = False



class OrderItemIn(In):
    product_id: int | None = None
    name: str = ""
    qty: int = Field(1, ge=1, le=100000)
    price: Money | None = None
    upsell: bool = False
    upsell_for: int | None = Field(None, description="Допродаж до якого товару (id)")


class OrderIn(In):
    """Створення або зміна замовлення. У PATCH змінюються лише передані поля.
    ПІБ — окремими полями last_name / first_name / middle_name; customer_name (одним рядком) CRM розбере сама."""
    customer_name: str | None = None
    last_name: str | None = Field(None, max_length=100)
    first_name: str | None = Field(None, max_length=100)
    middle_name: str | None = Field(None, max_length=100)
    phone: str | None = None
    email: str | None = None
    comment: str | None = None
    delivery_method: Literal["novaposhta", "ukrposhta", "meest", "pickup", "courier"] | None = None
    city_name: str | None = None
    city_ref: str | None = None
    warehouse_name: str | None = None
    warehouse_ref: str | None = None
    address: str | None = None
    postcode: str | None = None
    ttn: str | None = None
    delivery_cost: Money | None = None
    payment_type: Literal["cod", "partial", "prepaid"] | None = Field(None, description="Застаріле: краще payment_method_id")
    payment_method_id: int | None = None
    source_id: int | None = None
    office_id: int | None = None
    np_account_id: int | None = Field(None, description="Ключ Нової Пошти (ФОП) для ТТН")
    reason_id: int | None = None
    mark_id: int | None = None
    remind_at: str | None = Field(None, description="ISO-дата нагадування, порожньо — прибрати")
    country: str | None = Field(None, max_length=2)
    extra1: str | None = Field(None, max_length=255)
    extra2: str | None = Field(None, max_length=255)
    extra3: str | None = Field(None, max_length=255)
    extra4: str | None = Field(None, max_length=255)
    prepayment: Money | None = None
    discount: Money | None = None
    site: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None
    utm_term: str | None = None
    status_id: int | None = None
    manager_id: int | None = None
    items: list[OrderItemIn] | None = None
    note: str | None = Field(None, description="Коментар менеджера, що додається разом зі створенням")
    version: str | None = Field(None, description="updated_at, отриманий з картки: захист від одночасного редагування (409)")


class BulkIn(In):
    ids: list[int]
    action: Literal["status", "assign", "ttn", "track"]
    value: int | str | None = None


class BulkOut(Out):
    done: int
    queued: int
    errors: list[str]


class TextIn(In):
    text: str


class SmsIn(In):
    text: str
    channel: Literal["sms", "viber", "hybrid"] = "sms"


class PaymentIn(In):
    amount: Money
    method: Literal["card", "iban", "cash", "other"] = "card"
    reference: str = ""


class TrackOut(OrderOut):
    changed: bool = False


# ---------------------------------------------------------------- склад
class MoveOut(Out):
    id: int
    product_id: int
    product: str
    kind: str
    kind_name: str
    stock_delta: int
    reserved_delta: int
    order_id: int | None
    purchase_id: int | None
    user: str
    comment: str
    created_at: str | None


class ProductDetailOut(ProductOut):
    moves: list[MoveOut]
    sold: int


class ProductIn(In):
    name: str | None = None
    sku: str | None = None
    price: Money | None = None
    cost: Money | None = None
    weight: Money | None = None
    min_stock: int | str | None = None
    length: float | None = Field(None, ge=0, le=1000)
    width: float | None = Field(None, ge=0, le=1000)
    height: float | None = Field(None, ge=0, le=1000)
    ship_description: str | None = Field(None, max_length=255)
    upsell: bool | None = None
    upsell_for: list[int] | None = None
    active: bool | None = None
    initial_stock: int | str | None = Field(None, description="Лише при створенні")


class WarehouseOut(Out):
    products: list[ProductOut]
    value: float
    units: int
    reserved: int
    low: int
    moves: list[MoveOut]
    kinds: dict[str, str]


class AdjustIn(In):
    product_id: int
    mode: Literal["set", "delta"] = "set"
    qty: int | str
    comment: str = ""


class PurchaseItemOut(Out):
    id: int | None = None
    product_id: int
    name: str
    qty: int
    cost: float


class PurchaseOut(Out):
    id: int
    supplier_id: int | None
    supplier: str
    status: Literal["draft", "ordered", "received", "cancelled"]
    comment: str
    total: float
    created_at: str | None
    received_at: str | None
    items: list[PurchaseItemOut]


class PurchaseItemIn(In):
    product_id: int | str
    qty: int | str
    cost: Money | None = None


class PurchaseIn(In):
    supplier_id: int | str | None = None
    comment: str | None = None
    items: list[PurchaseItemIn] | None = None
    then: Literal["", "save", "ordered", "receive", "cancel"] = ""


class SupplierOut(Out):
    id: int
    name: str
    phone: str
    comment: str


class SupplierIn(In):
    id: int | None = None
    name: str
    phone: str = ""
    comment: str = ""


# ---------------------------------------------------------------- гроші, звіти, журнал
class PaymentTotal(Out):
    count: int
    sum: float


class PaymentsOut(Out):
    items: list[PaymentOut]
    totals: dict[str, PaymentTotal]


class ReceiveIn(In):
    ids: list[int]
    reference: str = ""


class DoneOut(Out):
    done: int


class RegistryRow(Out):
    ttn: str
    order_id: int | None = None
    expected: float | None = None
    amount: float | None = None


class RegistryOut(Out):
    matched: list[RegistryRow]
    mismatch: list[RegistryRow]
    not_found: list[RegistryRow]
    already: list[RegistryRow]


class Bucket(Out):
    leads: int
    unique: int
    approved: int
    shipped: int
    delivered: int
    refused: int
    revenue: float
    cost: float
    profit: float
    avg_check: float
    approve_rate: float
    buyout_rate: float


class GroupRow(Bucket):
    name: str


class DayRow(Out):
    day: str
    leads: int
    approved: int


class ProductReportRow(Out):
    name: str
    qty: int
    orders: int
    revenue: float
    cost: float
    upsell_qty: int


class ReportOut(Out):
    date_from: str
    date_to: str
    dim: str
    dims: dict[str, str]
    total: Bucket
    groups: list[GroupRow]
    days: list[DayRow]
    products: list[ProductReportRow]


class AuditRow(Out):
    id: int
    user: str
    entity: str
    entity_id: int | None
    action: str
    action_name: str
    details: str
    created_at: str | None


class AuditOut(Out):
    items: list[AuditRow]
    next: int | None
    actions: dict[str, str]


# ---------------------------------------------------------------- налаштування
class SmsTemplateOut(Out):
    id: int
    status_id: int
    channel: str
    text: str
    active: bool


class SmsLogOut(Out):
    id: int
    phone: str
    text: str
    status: str
    error: str
    channel: str
    created_at: str | None


class SettingsOut(Out):
    values: dict[str, str]
    secret_keys: list[str]
    webhook_url: str
    statuses: list[StatusOut]
    users: list[UserOut]
    sms_templates: list[SmsTemplateOut]
    placeholders: dict[str, str]
    sms_log: list[SmsLogOut]
    stock_actions: dict[str, str]
    roles: dict[str, str]
    payment_methods: list[PaymentMethodOut] = Field(default_factory=list, description="Усі види оплат, з вимкненими")
    order_sources: list[SourceOut] = Field(default_factory=list)
    offices: list[SourceOut] = Field(default_factory=list)
    reasons: list[ReasonOut] = Field(default_factory=list)
    marks: list[SourceOut] = Field(default_factory=list)
    checkbox_payments: dict[str, str] = Field(default_factory=dict)
    np_accounts: list["NpAccountOut"] = Field(default_factory=list)
    np_status_rules: list["NpRuleOut"] = Field(default_factory=list)
    shops: list["ShopOut"] = Field(default_factory=list)
    cashiers: list["CashierOut"] = Field(default_factory=list)
    np_statuses: dict[str, str] = Field(default_factory=dict)
    message: str | None = None


class PaymentMethodIn(In):
    id: int | None = None
    name: str = Field(..., min_length=1, max_length=80)
    icon: str = "cash"
    kind: Literal["cod", "partial", "prepaid"] = "cod"
    checkbox_type: str = ""
    active: bool = True
    sort: int = 100


class SourceIn(In):
    id: int | None = None
    name: str = Field(..., min_length=1, max_length=120)
    active: bool = True
    sort: int = 100
    delete: bool = False
    status_ids: list[int] | None = Field(None, description="Лише для причин")


class StatusIn(In):
    id: int | None = None
    name: str | None = None
    color: str | None = None
    sort: int | None = None
    stock_action: str | None = None
    approved: bool = False
    final: bool = False
    active: bool = True
    # поля відповіді, які інтерфейс може надіслати назад, ігноруються
    code: str | None = None
    system: bool | None = None


class SmsTemplateIn(In):
    id: int | None = None
    status_id: int | None = None
    channel: Literal["sms", "viber", "hybrid"] = "sms"
    text: str = ""
    active: bool = True
    delete: bool = False


class SmsTestIn(In):
    phone: str
    channel: Literal["sms", "viber"] = "sms"


class UserIn(In):
    username: str | None = None
    full_name: str | None = None
    role: Literal["admin", "manager", "warehouse"] | None = None
    password: str | None = None
    is_active: bool | None = None
    offices: list[int] | None = None


# ---------------------------------------------------------------- стан системи
class CheckOut(Out):
    ok: bool
    detail: str = ""


class SystemOut(Out):
    version: str
    checks: dict[str, CheckOut]
    queue_length: int | None
    worker_seen_at: str | None
    tracking: dict | None
    sms: dict[str, int]
    orders_today: int
    last_order_at: str | None
    alerts: list[str]
    sentry: bool
    metrics_url: str | None


# ---------------------------------------------------------------- ТТН Нової Пошти
NpPayer = Literal["Recipient", "Sender", "ThirdPerson"]
NpCargo = Literal["Parcel", "Cargo", "Documents", "TiresWheels", "Pallet"]
NpService = Literal["WarehouseWarehouse", "WarehouseDoors", "DoorsWarehouse", "DoorsDoors"]
NpCod = Literal["backward", "afterpayment", "none"]


class SeatIn(In):
    length: float = Field(..., gt=0, le=1000, description="см")
    width: float = Field(..., gt=0, le=1000)
    height: float = Field(..., gt=0, le=1000)
    weight: float = Field(..., gt=0, le=1000, description="кг")


class TtnParams(Out):
    payer: NpPayer
    cargo_type: NpCargo
    service_type: NpService
    weight: float
    seats: list[SeatIn]
    description: str
    declared_cost: int
    cod_mode: NpCod
    cod_amount: float
    cod_payer: NpPayer
    additional_info: str


class TtnIn(In):
    """Створення ТТН. Без тіла — з параметрами за замовчуванням; передані поля їх замінюють."""
    np_account_id: int | None = None
    payer: NpPayer | None = None
    cargo_type: NpCargo | None = None
    service_type: NpService | None = None
    seats: list[SeatIn] | None = Field(None, min_length=1, max_length=20)
    description: str | None = Field(None, max_length=100)
    declared_cost: int | None = Field(None, ge=1)
    cod_mode: NpCod | None = None
    cod_amount: float | None = Field(None, ge=0)
    cod_payer: NpPayer | None = None
    additional_info: str | None = Field(None, max_length=100)


class TtnPreviewOut(Out):
    supported: bool
    np_account_id: int | None = None
    accounts: list[NpAccountShort] = Field(default_factory=list)
    sender: str = ""
    params: TtnParams | None = None
    prepaid: bool = Field(False, description="Вид оплати виключає післяплату")


class NpAccountOut(Out):
    id: int
    name: str
    api_key: str = Field(description="Маскований: ******** якщо заданий")
    sender_ref: str
    sender_name: str
    contact_ref: str
    contact_name: str
    sender_phone: str
    city_name: str
    city_ref: str
    warehouse_name: str
    warehouse_ref: str
    payer: str
    cargo_type: str
    service_type: str
    cod_mode: str
    cod_payer: str
    info_comment: bool
    info_items: bool
    info_item_ids: bool
    default_weight: float
    seat_size: str
    description: str
    office_id: int | None = None
    is_default: bool
    is_active: bool
    directory: dict = Field(default_factory=dict)


class NpAccountIn(In):
    id: int | None = None
    name: str = Field("", max_length=160)
    api_key: str | None = Field(None, max_length=64, description="******** — не змінювати")
    sender_ref: str = ""
    sender_name: str = ""
    contact_ref: str = ""
    contact_name: str = ""
    sender_phone: str = ""
    city_name: str = ""
    city_ref: str = ""
    warehouse_name: str = ""
    warehouse_ref: str = ""
    payer: NpPayer = "Recipient"
    cargo_type: NpCargo = "Parcel"
    service_type: NpService = "WarehouseWarehouse"
    cod_mode: Literal["backward", "afterpayment"] = "backward"
    cod_payer: NpPayer = "Recipient"
    info_comment: bool = False
    info_items: bool = True
    info_item_ids: bool = False
    default_weight: float = Field(0.5, gt=0, le=1000)
    seat_size: str = Field("20x15x10", max_length=32)
    description: str = Field("Товар", max_length=255)
    office_id: int | None = None
    is_default: bool = False
    is_active: bool = True
    delete: bool = False
    directory: dict | None = None


class NpRuleOut(Out):
    id: int
    np_code: str
    status_id: int
    except_ids: list[int]


class NpRuleIn(In):
    id: int | None = None
    np_code: str = Field(..., max_length=8)
    status_id: int
    except_ids: list[int] = Field(default_factory=list)


# ---------------------------------------------------------------- маркетплейси
class ShopOut(Out):
    id: int
    kind: Literal["rozetka", "prom"]
    name: str
    login: str
    secret: str = Field(description="Маскований: ******** якщо заданий")
    office_id: int | None = None
    source_id: int | None = None
    import_status_id: int | None = None
    extra_field: int
    status_map: dict[str, str]
    payment_map: dict[str, int]
    delivery_map: dict[str, str]
    directory: dict
    since: str | None = None
    last_sync_at: str | None = None
    last_error: str
    imported: int
    is_active: bool


class ShopIn(In):
    id: int | None = None
    kind: Literal["rozetka", "prom"]
    name: str = Field("", max_length=160)
    login: str = Field("", max_length=160)
    secret: str | None = Field(None, max_length=255, description="******** — не змінювати")
    office_id: int | None = None
    source_id: int | None = None
    import_status_id: int | None = None
    extra_field: int = Field(1, ge=0, le=4)
    status_map: dict[str, str] = Field(default_factory=dict)
    payment_map: dict[str, int] = Field(default_factory=dict)
    delivery_map: dict[str, str] = Field(default_factory=dict)
    since: str | None = Field(None, description="Дата, з якої імпортувати замовлення (YYYY-MM-DD)")
    is_active: bool = True
    delete: bool = False


class ShopCheckOut(Out):
    statuses: dict[str, str]
    orders_30d: int
    sample_parsed: dict | None = None
    sample_keys: list[str] = Field(default_factory=list)


class ShopSyncOut(Out):
    new: int
    updated: int
    seen: int
    error: str


# ---------------------------------------------------------------- Checkbox
class ReceiptOut(Out):
    id: int
    kind: Literal["sell", "return", "prepay", "postpay"]
    kind_name: str
    status: Literal["new", "done", "error"]
    fiscal_code: str
    total: float
    error: str
    url: str
    test: bool
    cashier: str
    created_at: str | None


class ReceiptIn(In):
    kind: Literal["sell", "return", "prepay", "postpay"]


class CashierOut(Out):
    id: int
    name: str
    license_key: str = Field(description="Маскований")
    login: str
    password: str = Field(description="Маскований")
    test_mode: bool
    auto_shift: bool
    condition: Literal["none", "office", "user", "np_account"]
    condition_value: int | None = None
    sort: int
    is_active: bool
    last_error: str


class CashierIn(In):
    id: int | None = None
    name: str = Field("", max_length=160)
    license_key: str | None = Field(None, max_length=128)
    login: str = Field("", max_length=128)
    password: str | None = Field(None, max_length=128)
    test_mode: bool = False
    auto_shift: bool = True
    condition: Literal["none", "office", "user", "np_account"] = "none"
    condition_value: int | None = None
    is_active: bool = True
    delete: bool = False


class CashierCheckOut(Out):
    shift: str
    message: str
