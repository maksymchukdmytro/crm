"""Дати замовлення для статистики: закріплене за менеджером і підтверджене

Revision ID: 0007
Revises: 0006
"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    return any(c["name"] == column for c in sa.inspect(op.get_bind()).get_columns(table))


def _has_index(table: str, name: str) -> bool:
    return any(i["name"] == name for i in sa.inspect(op.get_bind()).get_indexes(table))


def upgrade():
    for col in ("assigned_at", "confirmed_at"):
        if not _has_column("orders", col):
            op.add_column("orders", sa.Column(col, sa.DateTime(), nullable=True))
    # Наявні замовлення: найкраща оцінка з того, що вже є в базі.
    # Закріплене — дата першого призначення менеджера з журналу, інакше дата створення.
    op.execute("""
        UPDATE orders o SET assigned_at = COALESCE(
            (SELECT MIN(a.created_at) FROM audit_log a
              WHERE a.entity = 'order' AND a.entity_id = o.id AND a.action = 'assign'),
            o.created_at)
        WHERE o.manager_id IS NOT NULL AND o.assigned_at IS NULL
    """)
    # Підтверджене — перша зміна на статус «апрув» із журналу, інакше дата відправки / зміни статусу.
    op.execute("""
        UPDATE orders o SET confirmed_at = COALESCE(
            (SELECT MIN(a.created_at) FROM audit_log a
              WHERE a.entity = 'order' AND a.entity_id = o.id AND a.action = 'status'
                AND a.details->>'на' IN (SELECT name FROM statuses WHERE counts_as_approved)),
            o.shipped_at, o.status_changed_at)
        FROM statuses s
        WHERE s.id = o.status_id AND s.counts_as_approved AND o.confirmed_at IS NULL
    """)
    for col in ("assigned_at", "confirmed_at", "shipped_at", "delivered_at", "updated_at", "status_changed_at"):
        name = f"ix_orders_{col}"
        if not _has_index("orders", name):
            op.create_index(name, "orders", [col])


def downgrade():
    for col in ("assigned_at", "confirmed_at", "shipped_at", "delivered_at", "updated_at", "status_changed_at"):
        op.drop_index(f"ix_orders_{col}", "orders")
    op.drop_column("orders", "confirmed_at")
    op.drop_column("orders", "assigned_at")
