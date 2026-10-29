"""Перевірка оплати в ТТН Нової Пошти: що має стояти (вид оплати) і що фактично стоїть (ТТН)

Revision ID: 0011
Revises: 0010
"""
from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def _cols(table: str) -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade():
    if "np_cod" not in _cols("payment_methods"):
        op.add_column("payment_methods", sa.Column("np_cod", sa.String(10), nullable=False, server_default=""))
        # NovaPay — контроль оплати; оплачено повністю — без післяплати. Решту власник налаштує сам.
        op.execute("UPDATE payment_methods SET np_cod = 'control' WHERE checkbox_type = 'novapay' OR icon = 'novapay'")
        op.execute("UPDATE payment_methods SET np_cod = 'none' WHERE kind = 'prepaid' AND np_cod = ''")
    cols = _cols("orders")
    if "ttn_cod_kind" not in cols:
        op.add_column("orders", sa.Column("ttn_cod_kind", sa.String(10), nullable=False, server_default=""))
    if "ttn_cod_sum" not in cols:
        op.add_column("orders", sa.Column("ttn_cod_sum", sa.Numeric(12, 2), nullable=False, server_default="0"))


def downgrade():
    op.drop_column("orders", "ttn_cod_sum")
    op.drop_column("orders", "ttn_cod_kind")
    op.drop_column("payment_methods", "np_cod")
