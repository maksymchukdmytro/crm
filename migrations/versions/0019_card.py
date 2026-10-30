"""Новий інтерфейс, крок 5: рахунки юрособ для передоплат, підтвердження оплати, наклейка, реєстр НП, очікувана дата доставки

Revision ID: 0019
Revises: 0018
"""
from alembic import op
import sqlalchemy as sa

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def _cols(t):
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(t)}


def upgrade():
    if "legal_entity_accounts" not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table(
            "legal_entity_accounts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("legal_entity_id", sa.Integer(), sa.ForeignKey("legal_entities.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(80), nullable=False),
            sa.Column("kind", sa.String(10), nullable=False, server_default="card"),
            sa.Column("iban", sa.String(34), nullable=False, server_default=""),
            sa.Column("card_mask", sa.String(20), nullable=False, server_default=""),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("sort", sa.Integer(), nullable=False, server_default="100"),
        )
        op.create_index("ix_legal_entity_accounts_legal_entity_id", "legal_entity_accounts", ["legal_entity_id"])
    pay = _cols("payments")
    if "account_id" not in pay:
        op.add_column("payments", sa.Column("account_id", sa.Integer(), sa.ForeignKey("legal_entity_accounts.id", ondelete="SET NULL"), nullable=True))
    if "confirmed_by_id" not in pay:
        op.add_column("payments", sa.Column("confirmed_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))
    if "confirmed_at" not in pay:
        op.add_column("payments", sa.Column("confirmed_at", sa.DateTime(), nullable=True))
    o = _cols("orders")
    if "label_printed_at" not in o:
        op.add_column("orders", sa.Column("label_printed_at", sa.DateTime(), nullable=True))
    if "np_registry_ref" not in o:
        op.add_column("orders", sa.Column("np_registry_ref", sa.String(40), nullable=False, server_default=""))
    if "delivery_eta" not in o:
        op.add_column("orders", sa.Column("delivery_eta", sa.Date(), nullable=True))


def downgrade():
    for c in ("delivery_eta", "np_registry_ref", "label_printed_at"):
        op.drop_column("orders", c)
    for c in ("confirmed_at", "confirmed_by_id", "account_id"):
        op.drop_column("payments", c)
    op.drop_table("legal_entity_accounts")
