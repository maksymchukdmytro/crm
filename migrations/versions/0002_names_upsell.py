"""ПІБ окремими полями; допродаж — звʼязок з основним товаром

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("orders", sa.Column("last_name", sa.String(100), nullable=False, server_default=""))
    op.add_column("orders", sa.Column("first_name", sa.String(100), nullable=False, server_default=""))
    op.add_column("orders", sa.Column("middle_name", sa.String(100), nullable=False, server_default=""))
    op.add_column("products", sa.Column("upsell_for", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("order_items", sa.Column("upsell_for_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_order_items_upsell_for", "order_items", "products", ["upsell_for_id"], ["id"], ondelete="SET NULL")

    # розкласти наявні ПІБ на частини
    from app.services.names import join_name, split_full_name
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, customer_name FROM orders WHERE customer_name <> ''")).fetchall()
    for oid, full in rows:
        last, first, middle = split_full_name(full)
        conn.execute(sa.text("UPDATE orders SET last_name=:l, first_name=:f, middle_name=:m, customer_name=:c WHERE id=:id"),
                     {"l": last[:100], "f": first[:100], "m": middle[:100], "c": join_name(last, first, middle)[:255], "id": oid})


def downgrade():
    op.drop_constraint("fk_order_items_upsell_for", "order_items", type_="foreignkey")
    op.drop_column("order_items", "upsell_for_id")
    op.drop_column("products", "upsell_for")
    op.drop_column("orders", "middle_name")
    op.drop_column("orders", "first_name")
    op.drop_column("orders", "last_name")
