"""Вид оплати — свій значок-картинка (власник завантажує офіційні логотипи платіжних систем)

Revision ID: 0013
Revises: 0012
"""
from alembic import op
import sqlalchemy as sa

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade():
    if "image" not in {c["name"] for c in sa.inspect(op.get_bind()).get_columns("payment_methods")}:
        op.add_column("payment_methods", sa.Column("image", sa.String(160), nullable=False, server_default=""))


def downgrade():
    op.drop_column("payment_methods", "image")
