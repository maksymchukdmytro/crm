"""Новий інтерфейс, крок 3: статуси «Несортований», «Очікує на отримання», «Відмова ліда»; нові назви й кольори

Назви й кольори, які користувач уже змінив, не чіпаємо: оновлюємо лише рядки зі старими типовими значеннями.
Коди статусів не змінюються.

Revision ID: 0017
Revises: 0016
"""
from alembic import op
import sqlalchemy as sa

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None

# code: (старa назва, старий колір, нова назва, новий колір)
RENAME = {
    "new": ("Новий", "#3b82f6", "Новий", "#2E6BE6"),
    "no_answer": ("Недозвон", "#a855f7", "Недодзвон", "#D97706"),
    "callback": ("Передзвонити", "#8b5cf6", "Передзвонити", "#7C3AED"),
    "confirmed": ("Підтверджено", "#0ea5e9", "Прийнятий", "#2E6BE6"),
    "shipped": ("Відправлено", "#f59e0b", "Відправлений", "#6D5BD0"),
    "delivered": ("Отримано", "#16a34a", "Завершений", "#16A34A"),
    "refused": ("Відмова / повертається", "#ef4444", "Відмова на пошті", "#E11D48"),
    "returned": ("Повернення на складі", "#78716c", "Повернуто на склад", "#64748B"),
    "cancelled": ("Скасовано", "#6b7280", "Відмова", "#DC2626"),
}
# code, назва, колір, порядок, дія зі складом, апрув, фінальний, розділ
NEW = [
    ("unsorted", "Несортований", "#7C7B76", 5, "none", False, False, "order"),
    ("arrived", "Очікує на отримання", "#D97706", 65, "none", True, False, "order"),
    ("lead_refused", "Відмова ліда", "#94A3B8", 105, "release", False, True, "lead"),
]


def upgrade():
    bind = op.get_bind()
    statuses = sa.table("statuses", sa.column("id", sa.Integer), sa.column("code", sa.String), sa.column("name", sa.String),
                        sa.column("color", sa.String), sa.column("sort", sa.Integer), sa.column("stock_action", sa.String),
                        sa.column("counts_as_approved", sa.Boolean), sa.column("is_final", sa.Boolean), sa.column("is_system", sa.Boolean),
                        sa.column("is_active", sa.Boolean), sa.column("stage", sa.String))
    rows = {r.code: r for r in bind.execute(sa.select(statuses.c.id, statuses.c.code, statuses.c.name, statuses.c.color))}
    for code, (old_name, old_color, name, color) in RENAME.items():
        r = rows.get(code)
        if r is None:
            continue
        if r.name == old_name and name != old_name:
            bind.execute(statuses.update().where(statuses.c.id == r.id).values(name=name))
        if (r.color or "").lower() == old_color.lower():
            bind.execute(statuses.update().where(statuses.c.id == r.id).values(color=color))
    for code, name, color, sort, action, approved, final, stage in NEW:
        if code not in rows:
            bind.execute(statuses.insert().values(code=code, name=name, color=color, sort=sort, stock_action=action,
                                                  counts_as_approved=approved, is_final=final, is_system=True, is_active=True, stage=stage))
    # «Комплектується» — у новій доріжці статусів немає; ховаємо, якщо в ньому немає замовлень
    if "packing" in rows:
        n = bind.execute(sa.text("SELECT COUNT(*) FROM orders WHERE status_id = :s"), {"s": rows["packing"].id}).scalar()
        if not n:
            bind.execute(statuses.update().where(statuses.c.id == rows["packing"].id).values(is_active=False))
    # НП: «прибув у відділення / поштомат» → «Очікує на отримання» — лише якщо правила вже налаштовано й цих кодів у них немає
    arrived = bind.execute(sa.select(statuses.c.id).where(statuses.c.code == "arrived")).scalar()
    have = {r[0] for r in bind.execute(sa.text("SELECT np_code FROM np_status_rules"))}
    if have and arrived:
        for code in ("7", "8"):
            if code not in have:
                bind.execute(sa.text("INSERT INTO np_status_rules (np_code, status_id, except_ids, sort) VALUES (:c, :s, '[]', 65)"),
                             {"c": code, "s": arrived})


def downgrade():
    pass  # назви й нові статуси лишаються: на них уже можуть посилатися замовлення
