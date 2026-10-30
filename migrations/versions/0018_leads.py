"""Новий інтерфейс, крок 4: ліди — спроби дзвінка, час останнього дзвінка, коли створено замовлення

Revision ID: 0018
Revises: 0017
"""
from alembic import op
import sqlalchemy as sa

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def _cols(t):
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(t)}


def _indexes(t):
    return {i["name"] for i in sa.inspect(op.get_bind()).get_indexes(t)}


def upgrade():
    have = _cols("orders")
    if "call_attempts" not in have:
        op.add_column("orders", sa.Column("call_attempts", sa.Integer(), nullable=False, server_default="0"))
    if "last_call_at" not in have:
        op.add_column("orders", sa.Column("last_call_at", sa.DateTime(), nullable=True))
    if "converted_at" not in have:
        op.add_column("orders", sa.Column("converted_at", sa.DateTime(), nullable=True))
    if "ix_orders_converted_at" not in _indexes("orders"):
        op.create_index("ix_orders_converted_at", "orders", ["converted_at"])


def downgrade():
    op.drop_index("ix_orders_converted_at", table_name="orders")
    for c in ("converted_at", "last_call_at", "call_attempts"):
        op.drop_column("orders", c)
