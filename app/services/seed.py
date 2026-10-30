from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import config
from ..models import OrderMark, OrderSource, PaymentMethod, SmsTemplate, Status, StatusReason, User
from ..security import hash_password
from . import settings as st

# code, назва, колір, порядок, дія зі складом, рахується як апрув, фінальний
DEFAULT_STATUSES = [
    ("new", "Новий", "#2E6BE6", 10, "none", False, False),
    ("no_answer", "Недодзвон", "#D97706", 20, "none", False, False),
    ("callback", "Передзвонити", "#7C3AED", 30, "none", False, False),
    ("unsorted", "Несортований", "#7C7B76", 5, "none", False, False),
    ("confirmed", "Прийнятий", "#2E6BE6", 40, "reserve", True, False),
    ("packing", "Комплектується", "#14b8a6", 50, "reserve", True, False),
    ("shipped", "Відправлений", "#6D5BD0", 60, "ship", True, False),
    ("arrived", "Очікує на отримання", "#D97706", 65, "none", True, False),
    ("delivered", "Завершений", "#16A34A", 70, "ship", True, True),
    ("refused", "Відмова на пошті", "#E11D48", 80, "ship", True, False),
    ("returned", "Повернуто на склад", "#64748B", 90, "return", True, True),
    ("cancelled", "Відмова", "#DC2626", 100, "release", False, True),
    ("duplicate", "Дубль", "#9ca3af", 110, "release", False, True),
    ("lead_refused", "Відмова ліда", "#94A3B8", 105, "release", False, True),
]

# Види оплат як у LP-CRM (ті самі id): id, назва, значок, розрахунок (cod / partial / prepaid), тип Checkbox, активний.
# prepaid = «при створенні ТТН виключає можливість післяплати»
DEFAULT_PAYMENT_METHODS = [
    (4, "Післяплата", "cod", "cod", "", False),
    (2, "Передоплата", "prepay", "partial", "", True),
    (7, "Передоплата на картку", "prepay_card", "partial", "", False),
    (13, "Передоплата отримана", "prepay_ok", "partial", "", True),
    (1, "Оплачено", "paid", "prepaid", "", True),
    (11, "Онлайн-оплата", "online", "cod", "", False),
    (10, "Пром-оплата", "prom", "prepaid", "rozetkapay", True),
    (6, "Оплата на картку", "card", "cod", "", True),
    (12, "OLX доставка", "olx", "prepaid", "", False),
    (9, "Оплата готівкою", "cash", "cod", "", True),
    (5, "Обмін", "exchange", "cod", "", True),
    (8, "Повернення коштів", "refund", "cod", "", True),
    (3, "POS-термінал", "pos", "cod", "", False),
    (14, "RozetkaPay", "rozetkapay", "prepaid", "rozetkapay", True),
    (15, "Післяплата Rozetka", "rozetka", "cod", "rozetkapay", True),
    (16, "Післяплата NovaPay", "novapay", "cod", "novapay", True),
    (17, "Післяплата Укрпошта", "ukrposhta", "cod", "", True),
    (18, "Післяплата Meest", "meest", "cod", "", True),
] + [(pid, name, "bank", "cod", "", False) for pid, name in [
    (19, "Apple Pay"), (20, "Google Pay"), (21, "Mastercard"), (22, "VISA"), (23, "PayPal"), (24, "ПРОСТІР"),
    (25, "Кредит"), (26, "Оплата частинами"), (27, "Розстрочка"), (28, "Portmone"), (29, "whitepay"), (30, "LiqPay"),
    (31, "Приват24"), (32, "ПриватБанк"), (33, "Western Union"), (34, "monobank"), (35, "Ощадбанк"),
    (36, "UKRSIBBANK"), (37, "Укрексімбанк"), (38, "Укргазбанк"), (39, "Креді Агріколь Банк"), (40, "Південний"),
    (41, "Universal Bank"), (42, "ПУМБ"), (43, "Forward Bank"), (44, "абанк"), (45, "Raiffeisen Bank"),
    (46, "OTP Bank"), (47, "sense bank")]]
DEFAULT_SOURCES = ["Маркетплейси", "Сайти", "Соціальні мережі", "Інше"]
DEFAULT_REASONS = ["Дубль", "Передумав", "Не замовляв", "Невірний номер", "Знайшов дешевше", "Вже купив",
                   "Не актуально", "Не підходить", "Не відповідає", "Дорого", "Передплата", "Сумніви в якості",
                   "Погані відгуки", "Дивись коментар"]
DEFAULT_MARKS = [
    "Терміново", "Очікує", "Переробити", "Перевірити", "Виконано", "Не виконано", "Подарунок до замовлення",
    "Покласти гарантію", "Покласти чек", "Перевірити перед відправленням", "Відправити сьогодні", "Відправити по дропу",
    "Роздрукувати (гарантію, інструкцію, чек, ТТН)", "Відправити (гарантію, інструкцію, чек, ТТН)", "Перевірити ТТН",
    "Перевірити чек", "Очікує дзвінка", "Недодзвон", "Поганий сигнал", "Відмова під час дзвінка",
    "Відмова навіть з подарунком", "Відмова навіть зі знижкою", "Не забирати з пошти", "Повернути відправлення",
    "Написати покупцеві", "Написати в Telegram", "Написати в TikTok", "Написати у Viber", "Написати в Instagram",
    "Написати у Messenger", "Написати у Facebook", "Написати в Rozetka", "Написати в Prom", "Написати в OLX",
    "Написати в WhatsApp", "Попросити відгук",
]

# значки й кольори позначок — за змістом, як у LP-CRM (ключі — frontend/src/components/marks.tsx)
MARK_LOOKS = {
    "Терміново": ("alert", "#dc2626"), "Очікує": ("clock", "#ca8a04"), "Переробити": ("pencil", "#475569"),
    "Перевірити": ("eye", "#475569"), "Виконано": ("check", "#16a34a"), "Не виконано": ("x", "#dc2626"),
    "Подарунок до замовлення": ("gift", "#475569"), "Покласти гарантію": ("file", "#475569"), "Покласти чек": ("receipt", "#475569"),
    "Перевірити перед відправленням": ("package", "#475569"), "Відправити сьогодні": ("truck", "#2563eb"),
    "Відправити по дропу": ("handshake", "#475569"), "Роздрукувати (гарантію, інструкцію, чек, ТТН)": ("printer", "#475569"),
    "Відправити (гарантію, інструкцію, чек, ТТН)": ("mail", "#475569"), "Перевірити ТТН": ("barcode", "#475569"),
    "Перевірити чек": ("qr", "#475569"), "Очікує дзвінка": ("phone-wait", "#2563eb"), "Недодзвон": ("phone-missed", "#64748b"),
    "Поганий сигнал": ("signal", "#64748b"), "Відмова під час дзвінка": ("phone-off", "#dc2626"),
    "Відмова навіть з подарунком": ("gift", "#dc2626"), "Відмова навіть зі знижкою": ("percent", "#dc2626"),
    "Не забирати з пошти": ("trash", "#dc2626"), "Повернути відправлення": ("undo", "#475569"),
    "Написати покупцеві": ("message", "#475569"), "Написати в Telegram": ("send", "#229ed9"), "Написати в TikTok": ("music", "#111827"),
    "Написати у Viber": ("message", "#7360f2"), "Написати в Instagram": ("camera", "#e1306c"),
    "Написати у Messenger": ("message", "#0084ff"), "Написати у Facebook": ("message", "#1877f2"),
    "Написати в Rozetka": ("bag", "#00a046"), "Написати в Prom": ("store", "#7c3aed"), "Написати в OLX": ("tag", "#0f766e"),
    "Написати в WhatsApp": ("message", "#25d366"), "Попросити відгук": ("star", "#ca8a04"),
}

LEAD_CODES = ("new", "no_answer", "callback", "duplicate", "lead_refused")  # статуси розділу «Ліди»

DEFAULT_CUSTOMER_GROUPS = [("Покупець", "#64748b"), ("Оптовик", "#0ea5e9"), ("Дропшипер", "#a855f7"), ("Партнер", "#16a34a")]

DEFAULT_TEMPLATES = {
    "shipped": "Замовлення №{order_id} відправлено. {carrier}, ТТН {ttn}. До сплати при отриманні: {cod} грн. {company}",
    "confirmed": "{first_name}, дякуємо! Замовлення №{order_id} на {total} грн підтверджено. {company}",
}


def seed(db: Session):
    if db.query(Status).count() == 0:
        for code, name, color, sort, action, approved, final in DEFAULT_STATUSES:
            db.add(Status(code=code, name=name, color=color, sort=sort, stock_action=action,
                          counts_as_approved=approved, is_final=final, is_system=True,
                          is_active=code != "packing",  # «Комплектується» — запасний, у новій доріжці статусів його немає
                          stage="lead" if code in LEAD_CODES else "order"))
        db.flush()
        for code, text in DEFAULT_TEMPLATES.items():
            s = db.query(Status).filter(Status.code == code).one()
            db.add(SmsTemplate(status_id=s.id, channel="sms", text=text, is_active=True))
    seed_directories(db)
    if db.query(User).count() == 0:
        db.add(User(username=config.ADMIN_USERNAME, password_hash=hash_password(config.ADMIN_PASSWORD),
                    full_name="Адміністратор", role="admin"))
    st.ensure_webhook_key(db)
    db.commit()


def seed_directories(db: Session):
    """Довідники видів оплат і джерел — один раз, далі їх редагує адміністратор."""
    if db.query(PaymentMethod).count() == 0:
        for sort, (pid, name, icon, kind, cb, active) in enumerate(DEFAULT_PAYMENT_METHODS):
            db.add(PaymentMethod(id=pid, name=name, icon=icon, kind=kind, checkbox_type=cb, is_active=active, sort=sort * 10,
                                  np_cod="control" if cb == "novapay" else ("none" if kind == "prepaid" else "")))
        db.flush()
        if db.get_bind().dialect.name == "postgresql":  # id задані явно — підтягнути лічильник
            db.execute(text("SELECT setval(pg_get_serial_sequence('payment_methods','id'), (SELECT MAX(id) FROM payment_methods))"))
    if db.query(OrderSource).count() == 0:
        for sort, name in enumerate(DEFAULT_SOURCES):
            db.add(OrderSource(name=name, sort=sort * 10))
    if db.query(StatusReason).count() == 0:
        refuse = [s.id for s in db.query(Status).filter(Status.code.in_(["cancelled"])).all()]
        for sort, name in enumerate(DEFAULT_REASONS):
            db.add(StatusReason(name=name, status_ids=refuse, sort=sort * 10))
    if db.query(OrderMark).count() == 0:
        for sort, name in enumerate(DEFAULT_MARKS):
            icon, color = MARK_LOOKS.get(name, ("tag", "#475569"))
            db.add(OrderMark(name=name, icon=icon, color=color, sort=sort * 10))
    from ..models import CustomerGroup
    if db.query(CustomerGroup).count() == 0:
        for sort, (name, color) in enumerate(DEFAULT_CUSTOMER_GROUPS):
            db.add(CustomerGroup(name=name, color=color, sort=(sort + 1) * 10))
    db.flush()
