"""Розділи «Ліди» і «Замовлення»: етап статусу

Revision ID: 0010
Revises: 0009
"""
from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade():
    if not any(c["name"] == "stage" for c in sa.inspect(op.get_bind()).get_columns("statuses")):
        op.add_column("statuses", sa.Column("stage", sa.String(8), nullable=False, server_default="order"))
        # обробка заявки — «Ліди»; усе після підтвердження — «Замовлення»
        op.execute("UPDATE statuses SET stage = 'lead' WHERE code IN ('new', 'no_answer', 'callback', 'duplicate')")


def downgrade():
    op.drop_column("statuses", "stage")
