from sqlalchemy.orm import Session

from ..config import config
from ..models import SmsTemplate, Status, User
from ..security import hash_password
from . import settings as st

# code, назва, колір, порядок, дія зі складом, рахується як апрув, фінальний
DEFAULT_STATUSES = [
    ("new", "Новий", "#3b82f6", 10, "none", False, False),
    ("no_answer", "Недозвон", "#a855f7", 20, "none", False, False),
    ("callback", "Передзвонити", "#8b5cf6", 30, "none", False, False),
    ("confirmed", "Підтверджено", "#0ea5e9", 40, "reserve", True, False),
    ("packing", "Комплектується", "#14b8a6", 50, "reserve", True, False),
    ("shipped", "Відправлено", "#f59e0b", 60, "ship", True, False),
    ("delivered", "Отримано", "#16a34a", 70, "ship", True, True),
    ("refused", "Відмова / повертається", "#ef4444", 80, "ship", True, False),
    ("returned", "Повернення на складі", "#78716c", 90, "return", True, True),
    ("cancelled", "Скасовано", "#6b7280", 100, "release", False, True),
    ("duplicate", "Дубль", "#9ca3af", 110, "release", False, True),
]

DEFAULT_TEMPLATES = {
    "shipped": "Замовлення №{order_id} відправлено. {carrier}, ТТН {ttn}. До сплати при отриманні: {cod} грн. {company}",
    "confirmed": "{first_name}, дякуємо! Замовлення №{order_id} на {total} грн підтверджено. {company}",
}


def seed(db: Session):
    if db.query(Status).count() == 0:
        for code, name, color, sort, action, approved, final in DEFAULT_STATUSES:
            db.add(Status(code=code, name=name, color=color, sort=sort, stock_action=action,
                          counts_as_approved=approved, is_final=final, is_system=True))
        db.flush()
        for code, text in DEFAULT_TEMPLATES.items():
            s = db.query(Status).filter(Status.code == code).one()
            db.add(SmsTemplate(status_id=s.id, channel="sms", text=text, is_active=True))
    if db.query(User).count() == 0:
        db.add(User(username=config.ADMIN_USERNAME, password_hash=hash_password(config.ADMIN_PASSWORD),
                    full_name="Адміністратор", role="admin"))
    st.ensure_webhook_key(db)
    db.commit()
