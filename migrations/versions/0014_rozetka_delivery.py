"""ROZETKA Delivery — окрема служба доставки: замовлення з ТТН RMP-… переводимо на неї

Revision ID: 0014
Revises: 0013
"""
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE orders SET delivery_method = 'rozetka' WHERE upper(ttn) LIKE 'RMP-%' AND delivery_method <> 'rozetka'")


def downgrade():
    op.execute("UPDATE orders SET delivery_method = 'novaposhta' WHERE delivery_method = 'rozetka'")
