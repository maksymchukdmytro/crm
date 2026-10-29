"""Checkbox (ПРРО): каси на ФОП, чеки замовлень

Revision ID: 0006
Revises: 0005
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "checkbox_cashiers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False, server_default=""),
        sa.Column("license_key", sa.String(128), nullable=False, server_default=""),
        sa.Column("login", sa.String(128), nullable=False, server_default=""),
        sa.Column("password", sa.String(128), nullable=False, server_default=""),
        sa.Column("test_mode", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("auto_shift", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("condition", sa.String(16), nullable=False, server_default="none"),
        sa.Column("condition_value", sa.Integer(), nullable=True),
        sa.Column("sort", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("token", sa.Text(), nullable=False, server_default=""),
        sa.Column("token_until", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=False, server_default=""),
    )
    op.create_table(
        "checkbox_receipts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cashier_id", sa.Integer(), sa.ForeignKey("checkbox_cashiers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("kind", sa.String(10), nullable=False),
        sa.Column("checkbox_id", sa.String(64), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="new"),
        sa.Column("fiscal_code", sa.String(64), nullable=False, server_default=""),
        sa.Column("total", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=False, server_default=""),
        sa.Column("test", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_checkbox_receipts_order_id", "checkbox_receipts", ["order_id"])


def downgrade():
    op.drop_table("checkbox_receipts")
    op.drop_table("checkbox_cashiers")
