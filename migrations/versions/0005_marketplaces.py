"""Маркетплейси: магазини Rozetka / Prom, звʼязок замовлення з магазином

Revision ID: 0005
Revises: 0004
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "marketplace_shops",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("name", sa.String(160), nullable=False, server_default=""),
        sa.Column("login", sa.String(160), nullable=False, server_default=""),
        sa.Column("secret", sa.String(255), nullable=False, server_default=""),
        sa.Column("office_id", sa.Integer(), sa.ForeignKey("offices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("order_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("import_status_id", sa.Integer(), sa.ForeignKey("statuses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("extra_field", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status_map", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("payment_map", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("delivery_map", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("directory", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("token", sa.Text(), nullable=False, server_default=""),
        sa.Column("token_until", sa.DateTime(), nullable=True),
        sa.Column("since", sa.DateTime(), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=False, server_default=""),
        sa.Column("imported", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column("orders", sa.Column("shop_id", sa.Integer(), sa.ForeignKey("marketplace_shops.id", ondelete="SET NULL"), nullable=True))
    op.add_column("orders", sa.Column("external_id", sa.String(64), nullable=False, server_default=""))
    op.add_column("orders", sa.Column("external_status", sa.String(120), nullable=False, server_default=""))
    op.create_index("ix_orders_external_id", "orders", ["external_id"])
    op.create_index("ux_orders_shop_external", "orders", ["shop_id", "external_id"], unique=True,
                    postgresql_where=sa.text("shop_id IS NOT NULL"))


def downgrade():
    op.drop_index("ux_orders_shop_external", "orders")
    op.drop_index("ix_orders_external_id", "orders")
    for c in ("external_status", "external_id", "shop_id"):
        op.drop_column("orders", c)
    op.drop_table("marketplace_shops")
