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
    stage: Literal["lead", "order"] = Field("order", description="Розділ: «Ліди» чи «Замовлення»")


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
    warranty_months: int = Field(0, description="Гарантія, міс.; 0 — як у налаштуваннях документів")
    upsell: bool
    upsell_for: list[int] = Field(default_factory=list, description="Допродаж: до яких товарів пропонувати (порожньо — до будь-якого)")
    active: bool
    category_id: int | None = None
    manufacturer_id: int | None = None
    model: str = ""
    countries: list[str] = Field(default_factory=list, description="Країни продажу; порожньо — усі")
    spec_price: float = Field(0, description="Акційна ціна; 0 — без акції")
    sale_price: float = Field(0, description="Ціна в замовленні: акційна або звичайна")
    discount_percent: int = 0
    wholesale_price: float = 0
    photo: str | None = Field(None, description="Головне фото: шлях від кореня CRM (/media/…)")
    variants: list[VariantOut] = Field(default_factory=list)


class VariantOut(Out):
    id: int
    name: str
    sku: str
    attribute_ids: list[int]
    price: float | None
    stock: int
    reserved: int
    available: int
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
    np_cod: Literal["", "control", "backward", "none"] = Field("", description="що має стояти в ТТН Нової Пошти: контроль оплати / грошовий переказ / без післяплати; порожньо — не перевіряти")
    image: str = Field("", description="свій значок (адреса картинки) замість стандартного")
    active: bool
    sort: int


class PayCheckOut(Out):
    state: Literal["ok", "bad", "wait"] = Field(description="ok — ТТН відповідає виду оплати, bad — ні, wait — ТТН ще немає або НП не повернула дані")
    text: str


class SourceOut(Out):
    """Довідник «назва + активний + порядок»: джерела, відділи, позначки."""
    id: int
    name: str
    active: bool
    sort: int
    office_id: int | None = Field(None, description="Лише для джерел: відділ, до якого належить джерело")
    icon: str | None = Field(None, description="Лише для позначок: ключ значка")
    color: str | None = Field(None, description="Лише для позначок: колір значка")


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
    extra_on: list[bool] = Field(default_factory=lambda: [True] * 4, description="Які з полів 1–4 показувати в картці")
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
    categories: list[CategoryShort] = Field(default_factory=list)
    manufacturers: list[NamedShort] = Field(default_factory=list)
    customer_groups: list[GroupShort] = Field(default_factory=list)
    legal_entities: list[EntityShort] = Field(default_factory=list)
    checkbox_ready: bool = False
    office: int | None = Field(None, description="Відділ, вибраний у боковій панелі; null — усі")
    leads_enabled: bool = True
    lead_wait_warn_min: int = 5
    lead_wait_bad_min: int = 15
    counters: CountersOut | None = None
    prefs: dict = Field(default_factory=dict, description="Налаштування користувача (user_prefs)")


class CountersOut(Out):
    leads_new: int = 0
    orders_unsorted: int = 0
    reminders_due: int = 0
    saved: dict[str, int] = Field(default_factory=dict, description="id збереженого фільтра → кількість")


class PrefIn(In):
    value: dict | list | str | int | float | bool | None = None


class OfficeIn(In):
    office_id: int | None = None


class SavedFilterIn(In):
    name: str | None = Field(None, max_length=80)
    section: Literal["orders", "leads", "products", "customers", "invoices"] | None = None
    color: str | None = Field(None, max_length=9)
    query: str | None = Field(None, max_length=2000)
    sort: int | None = None
    is_shared: bool | None = None


class SavedFilterOut(Out):
    id: int
    section: str
    name: str
    color: str
    query: str
    sort: int
    is_shared: bool
    mine: bool


class ReminderNote(Out):
    order_id: int
    customer: str
    at: str | None
    due: bool


class CommentNote(Out):
    id: int
    order_id: int
    customer: str
    user: str
    text: str
    at: str | None


class NotificationsOut(Out):
    reminders: list[ReminderNote] = Field(default_factory=list)
    comments: list[CommentNote] = Field(default_factory=list)


class EntityShort(Out):
    id: int
    name: str
    is_default: bool
    has_cashier: bool


class CategoryShort(Out):
    id: int
    name: str
    parent_id: int | None


class NamedShort(Out):
    id: int
    name: str


class GroupShort(Out):
    id: int
    name: str
    color: str


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


class GroupTag(Out):
    name: str
    color: str


class OrderRowOut(Out):
    id: int
    status_id: int
    manager_id: int | None
    warehouse_name: str = ""
    customer_group: GroupTag | None = None
    no_stock: bool = False
    call_attempts: int = 0
    last_call_at: str | None = None
    converted_at: str | None = None
    wait_minutes: int | None = Field(None, description="Ліди: скільки хвилин чекає дзвінка (None — не чекає)")
    office_id: int | None = None
    np_account_id: int | None = None
    legal_entity_id: int | None = None
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
    customer_id: int | None = None
    blacklisted: bool = False
    pay_check: PayCheckOut | None = None


class DayGroup(Out):
    day: str = Field(description="Дата за місцевим часом, YYYY-MM-DD")
    count: int
    sum: Num = Field(description="Сума без скасованих і дублів")


class LeadTabsOut(Out):
    open: int = 0
    new: int = 0
    no_answer: int = 0
    callback: int = 0
    duplicate: int = 0
    refused: int = 0
    converted: int = 0
    all: int = 0


class OrderListOut(Out):
    lead_tabs: LeadTabsOut | None = Field(None, description="Лічильники вкладок лідів (stage=lead)")
    items: list[OrderRowOut]
    next: int | None
    total: int | None = None
    counts: dict[str, int] | None = None
    all: int | None = None
    groups: list[DayGroup] = Field(default_factory=list, description="Підсумки за днями для дат на цій сторінці")


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
    variant_id: int | None = None
    variant_name: str = ""
    photo: str | None = None
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


class OrderCustomer(Out):
    id: int
    name: str
    group: str
    group_color: str
    blacklisted: bool
    blacklist_reason: str
    comment: str
    orders: int
    delivered: int
    refused: int
    buyout_rate: float | None
    sum_delivered: float


class OrderOut(Out):
    call_attempts: int = 0
    last_call_at: str | None = None
    converted_at: str | None = None
    label: Literal["", "rozetka", "carrier"] = Field("", description="що друкувати біля ТТН: маркування Rozetka чи наклейку перевізника")
    pay_check: PayCheckOut | None = None
    ttn_cod_kind: str = ""
    ttn_cod_sum: float = 0
    id: int
    status_id: int
    manager_id: int | None
    office_id: int | None = None
    np_account_id: int | None = None
    legal_entity_id: int | None = None
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
    customer: OrderCustomer | None = None
    receipts: list["ReceiptOut"] = Field(default_factory=list)
    checkbox_ready: bool = False



class OrderItemIn(In):
    product_id: int | None = None
    name: str = ""
    qty: int = Field(1, ge=1, le=100000)
    price: Money | None = None
    upsell: bool = False
    upsell_for: int | None = Field(None, description="Допродаж до якого товару (id)")
    variant_id: int | None = Field(None, description="Варіант товару (колір, розмір…)")


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
    legal_entity_id: int | None = Field(None, description="Юридична особа: за нею обирається каса Checkbox")
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
    action: Literal["status", "assign", "ttn", "track", "fiscalize"]
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


class PhotoOut(Out):
    id: int
    url: str


class ProductDetailOut(ProductOut):
    moves: list[MoveOut]
    sold: int
    description: str = ""
    photos: list[PhotoOut] = Field(default_factory=list)


class VariantIn(In):
    id: int | None = None
    name: str = Field("", max_length=255)
    sku: str = Field("", max_length=64)
    attribute_ids: list[int] = Field(default_factory=list)
    price: Money | None = None
    active: bool = True
    initial_stock: int = Field(0, ge=0, description="Лише для нового варіанта")


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
    warranty_months: int | None = Field(None, ge=0, le=240)
    upsell: bool | None = None
    upsell_for: list[int] | None = None
    active: bool | None = None
    initial_stock: int | str | None = Field(None, description="Лише при створенні")
    category_id: int | None = None
    manufacturer_id: int | None = None
    model: str | None = Field(None, max_length=120)
    description: str | None = None
    countries: list[str] | None = None
    spec_price: Money | None = None
    wholesale_price: Money | None = None
    variants: list[VariantIn] | None = Field(None, description="Повний список варіантів; відсутні буде видалено (або вимкнено, якщо вже продавались)")


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
    variant_id: int | None = None
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
    legal_entities: list["LegalEntityOut"] = Field(default_factory=list)
    np_statuses: dict[str, str] = Field(default_factory=dict)
    message: str | None = None


class PaymentMethodIn(In):
    id: int | None = None
    name: str = Field(..., min_length=1, max_length=80)
    icon: str = "cash"
    kind: Literal["cod", "partial", "prepaid"] = "cod"
    checkbox_type: str = ""
    np_cod: Literal["", "control", "backward", "none"] = ""
    active: bool = True
    sort: int = 100


class SourceIn(In):
    id: int | None = None
    name: str = Field(..., min_length=1, max_length=120)
    active: bool = True
    sort: int = 100
    delete: bool = False
    status_ids: list[int] | None = Field(None, description="Лише для причин")
    office_id: int | None = Field(None, description="Лише для джерел: відділ")
    icon: str | None = Field(None, max_length=24, description="Лише для позначок: ключ значка")
    color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$", description="Лише для позначок: колір")


class StatusIn(In):
    id: int | None = None
    name: str | None = None
    color: str | None = None
    sort: int | None = None
    stock_action: str | None = None
    approved: bool = False
    final: bool = False
    active: bool = True
    stage: Literal["lead", "order"] | None = None
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
    legal_entity_id: int | None = None
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
    legal_entity_id: int | None = None
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
    legal_entity_id: int | None = None
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
    legal_entity_id: int | None = None
    condition: Literal["none", "office", "user", "np_account"] = "none"
    condition_value: int | None = None
    is_active: bool = True
    delete: bool = False


class CashierCheckOut(Out):
    shift: str
    message: str


# ---------------------------------------------------------------- статистика
class StatsQuery(BaseModel):
    """Фільтри статистики. Списки — через кому; «__empty__» — «Пусте поле»."""
    model_config = ConfigDict(extra="ignore")
    date_field: Literal["created", "assigned", "confirmed", "shipped", "delivered", "status", "changed"] = "created"
    date_from: str = ""
    date_to: str = ""
    all_time: bool = False
    group: Literal["auto", "hour", "day", "week", "month"] = "auto"
    status: str = ""
    reason: str = ""
    product: str = ""
    category: str = ""
    payment: str = ""
    delivery: str = ""
    office: str = ""
    source: str = ""
    manager: str = ""
    shop: str = ""
    np_account: str = ""
    mark: str = ""
    legal_entity: str = ""
    country: str = ""
    site: str = ""
    utm_source: str = ""
    utm_medium: str = ""
    utm_term: str = ""
    utm_content: str = ""
    utm_campaign: str = ""
    extra1: str = ""
    extra2: str = ""
    extra3: str = ""
    extra4: str = ""
    upsell: Literal["", "with", "without"] = ""
    search: str = ""


class StatsPoint(Out):
    t: str = Field(description="Початок відрізка, місцевий час (YYYY-MM-DDTHH:MM)")
    total: int
    by_status: dict[str, int]


class StatsStatus(Out):
    status_id: int
    count: int
    share: float


class StatsSummary(Out):
    orders: int
    orders_plain: int
    orders_upsell: int
    upsell_rate: float
    qty: int
    qty_main: int
    qty_upsell: int
    qty_upsell_rate: float
    margin: float
    margin_main: float
    margin_upsell: float
    margin_avg: float
    sum: float
    sum_main: float
    sum_upsell: float
    avg_check: float
    duplicates: int
    approved: int
    approve_rate: float
    shipped: int
    delivered: int
    refused: int
    buyout_rate: float
    confirm_avg_min: float | None = None


class StatsPrev(StatsSummary):
    date_from: str
    date_to: str


class StatsOut(Out):
    date_from: str
    date_to: str
    date_field: str
    group: str
    series: list[StatsPoint]
    statuses: list[StatsStatus]
    summary: StatsSummary
    prev: StatsPrev | None = None


class StatsProduct(Out):
    product_id: int | None
    name: str
    sku: str
    category: str
    orders: int
    qty: int
    qty_main: int
    qty_upsell: int
    sum: float
    sum_main: float
    sum_upsell: float
    margin: float
    margin_main: float
    margin_upsell: float


class StatsProductsOut(Out):
    rows: list[StatsProduct]


class StatsBreakdownRow(StatsSummary):
    key: str
    label: str


class StatsBreakdownOut(Out):
    dim: str
    rows: list[StatsBreakdownRow]


class StatsSegment(Out):
    from_: float = Field(alias="from")
    to: float | None
    orders: int
    upsell: int
    delivered: int
    refused: int
    upsell_rate: float
    return_rate: float
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class StatsSegmentsOut(Out):
    metric: str
    step: float
    buckets: list[StatsSegment]


class StatsOrderItem(Out):
    name: str
    qty: int
    price: float
    cost: float
    is_upsell: bool


class StatsOrderRow(Out):
    id: int
    external_id: str
    status_id: int
    customer_name: str
    phone: str
    items: list[StatsOrderItem]
    total: float
    margin: float
    payment: str
    delivery: str
    ttn: str
    created_at: str | None
    confirm_secs: int | None
    assigned_at: str | None
    shipped_at: str | None
    delivered_at: str | None
    updated_at: str | None
    office: str
    manager: str
    site: str
    utm_source: str
    utm_medium: str
    utm_term: str
    utm_content: str
    utm_campaign: str
    extra1: str
    extra2: str
    extra3: str
    extra4: str


class StatsOrdersOut(Out):
    total: int
    offset: int
    rows: list[StatsOrderRow]


class StatsOption(Out):
    value: str
    count: int


class StatsOptionsOut(Out):
    values: dict[str, list[StatsOption]] = Field(description="Значення фільтрів-рядків: site, utm_*, extra1–4")
    date_fields: dict[str, str]
    dimensions: dict[str, str]
    segment_metrics: dict[str, str]


# ---------------------------------------------------------------- тестові дані
class TestDataIn(In):
    action: Literal["create", "delete"]


class TestDataOut(Out):
    products: int
    orders: int
    message: str


# ---------------------------------------------------------------- каталог: категорії, виробники, атрибути
class CategoryOut(Out):
    id: int
    name: str
    parent_id: int | None
    sort: int
    active: bool
    products: int


class CategoryIn(In):
    id: int | None = None
    name: str = Field(..., max_length=160)
    parent_id: int | None = None
    sort: int | None = None
    active: bool = True


class ManufacturerOut(Out):
    id: int
    name: str
    active: bool
    products: int


class ManufacturerIn(In):
    id: int | None = None
    name: str = Field(..., max_length=160)
    active: bool = True


class AttributeOut(Out):
    id: int
    name: str
    sort: int
    active: bool


class AttributeGroupOut(Out):
    id: int
    name: str
    sort: int
    attributes: list[AttributeOut]


class AttributeGroupIn(In):
    id: int | None = None
    name: str = Field(..., max_length=120)
    sort: int | None = None


class AttributeIn(In):
    id: int | None = None
    group_id: int
    name: str = Field(..., max_length=120)
    sort: int | None = None
    active: bool = True


# ---------------------------------------------------------------- покупці
class CustomerOut(Out):
    id: int
    phone: str
    name: str
    email: str
    country: str
    group_id: int | None
    group: str
    group_color: str
    comment: str
    blacklisted: bool
    blacklist_reason: str
    created_at: str | None
    orders: int
    delivered: int
    refused: int
    cancelled: int
    sum_delivered: float
    sum_total: float
    buyout_rate: float | None
    first_order_at: str | None
    last_order_at: str | None


class CustomerListOut(Out):
    total: int
    offset: int
    rows: list[CustomerOut]


class CustomerDetailOut(CustomerOut):
    history: list[OrderRowOut]


class CustomerIn(In):
    phone: str | None = Field(None, max_length=32)
    name: str | None = Field(None, max_length=255)
    email: str | None = Field(None, max_length=255)
    country: str | None = Field(None, max_length=2)
    group_id: int | None = None
    comment: str | None = None
    blacklisted: bool | None = None
    blacklist_reason: str | None = Field(None, max_length=255)


class CustomerGroupOut(Out):
    id: int
    name: str
    color: str
    sort: int
    customers: int


class CustomerGroupIn(In):
    id: int | None = None
    name: str = Field(..., max_length=80)
    color: str | None = Field(None, max_length=9)
    sort: int | None = None


class BlockedIpOut(Out):
    id: int
    ip: str
    comment: str
    created_at: str | None


class BlockedIpIn(In):
    ip: str = Field(..., max_length=64)
    comment: str | None = Field(None, max_length=255)


# ---------------------------------------------------------------- юридичні особи
class LegalEntityOut(Out):
    id: int
    name: str
    code: str
    iban: str
    code_label: str = "РНОКПП"
    address: str = ""
    bank: str = ""
    phone: str = ""
    vat_note: str = "Без ПДВ"
    signer: str = ""
    is_default: bool
    is_active: bool
    sort: int
    orders: int = 0
    cashier: str = Field("", description="Назва каси Checkbox цієї юрособи")


class LegalEntityIn(In):
    id: int | None = None
    name: str = Field(..., max_length=255)
    code: str = Field("", max_length=20)
    iban: str = Field("", max_length=34)
    code_label: str = "РНОКПП"
    address: str = Field("", max_length=255)
    bank: str = Field("", max_length=160)
    phone: str = Field("", max_length=40)
    vat_note: str = Field("Без ПДВ", max_length=80)
    signer: str = Field("", max_length=120)
    is_default: bool = False
    is_active: bool = True
    delete: bool = False


class ProductDeleteOut(Out):
    deleted: bool = Field(description="false — товар лише перенесено в архів (уже був у замовленнях)")
    message: str


class NameSplitOut(Out):
    last_name: str
    first_name: str
    middle_name: str
    full: str = Field(description="Як збережеться: «Прізвище Ім'я По батькові»")


# ---------------------------------------------------------------- головна сторінка
class DashToday(Out):
    date: str
    orders: int
    sum: float
    orders_delta: float | None = Field(None, description="зміна до вчора, %")
    sum_delta: float | None = None
    yesterday_orders: int
    yesterday_sum: float


class DashMonth(Out):
    date_from: str
    orders: int
    sum: float
    avg_check: float
    orders_delta: float | None = Field(None, description="зміна до того самого відрізка минулого місяця, %")
    sum_delta: float | None = None
    prev_orders: int
    prev_sum: float
    approve_rate: float
    buyout_rate: float
    upsell_rate: float
    margin: float


class DashCustomers(Out):
    total: int
    new: int
    new_delta: float | None = None


class DashAttention(Out):
    leads_new: int
    leads_open: int
    orders_unsorted: int = 0
    to_ship: int
    on_way: int
    arrived: int
    reminders: int
    low_stock: int
    cod_expected: float
    cod_collected: float


class DashDay(Out):
    day: str
    orders: int
    sum: float


class DashTop(Out):
    product_id: int | None
    name: str
    qty: int
    sum: float


class DashTeam(Out):
    id: int
    name: str
    role: str
    confirmed: int = Field(description="підтверджено сьогодні")
    new: int = Field(description="нових замовлень на ньому сьогодні")
    last_login: str | None = None


class DashboardOut(Out):
    today: DashToday
    month: DashMonth
    customers: DashCustomers
    attention: DashAttention
    days: list[DashDay]
    team: list[DashTeam] = Field(default_factory=list)
    top: list[DashTop]


# ---------------------------------------------------------------- друк документів
class DocItem(Out):
    name: str
    sku: str = ""
    qty: int
    price: float
    warranty_months: int = 0
    upsell: bool = False


class DocOrder(Out):
    id: int
    date: str = Field(description="дата документа (сьогодні, за часовим поясом CRM)")
    created: str | None = None
    buyer: str
    phone: str
    email: str = ""
    delivery: str = ""
    address: str = ""
    ttn: str = ""
    items: list[DocItem]
    discount: float = 0
    total: float
    prepayment: float = 0
    cod_amount: float = 0
    payment: str = ""


class DocSeller(Out):
    name: str
    code: str = ""
    code_label: str = "РНОКПП"
    iban: str = ""
    address: str = ""
    bank: str = ""
    phone: str = ""
    vat_note: str = "Без ПДВ"
    signer: str = ""


class DocumentsOut(Out):
    order: DocOrder
    seller: DocSeller
    docs: dict[str, str]



# ---------------------------------------------------------------- ліди
class LeadResultIn(In):
    result: Literal["no_answer", "callback", "refused", "duplicate"]
    at: str | None = Field(None, description="Час передзвону (ISO)")
    reason_id: int | None = None
    duplicate_of_id: int | None = None
    note: str | None = Field(None, max_length=2000)


class LeadStepOut(Out):
    order: OrderOut
    next_id: int | None = None


class LeadQueueOut(Out):
    ids: list[int]


class LeadsPreviewOut(Out):
    enabled: bool
    open: int


class LeadsToggleIn(In):
    enabled: bool
    move_open: bool = False


class LeadsToggleOut(Out):
    enabled: bool
    moved: int = 0
