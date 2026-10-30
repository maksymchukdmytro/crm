"""Новий інтерфейс, крок 7: додатковий телефон покупця

Revision ID: 0021
Revises: 0020
"""
from alembic import op
import sqlalchemy as sa

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade():
    insp = sa.inspect(op.get_bind())
    if "phone2" not in {c["name"] for c in insp.get_columns("customers")}:
        op.add_column("customers", sa.Column("phone2", sa.String(20), nullable=False, server_default=""))
    if "ix_customers_phone2" not in {i["name"] for i in insp.get_indexes("customers")}:
        op.create_index("ix_customers_phone2", "customers", ["phone2"])


def downgrade():
    op.drop_index("ix_customers_phone2", table_name="customers")
    op.drop_column("customers", "phone2")
