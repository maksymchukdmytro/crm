"""«Можливий дубль» лише при збігу телефону, товарів і суми: зняти старі позначки, поставлені лише за телефоном

Ліди, які менеджер сам позначив статусом «Дубль», не чіпаємо. Повторний запуск нічого не змінює.

Revision ID: 0022
Revises: 0021
"""
from alembic import op
import sqlalchemy as sa

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def _sig(rows):
    return tuple(sorted((r.product_id or 0, r.variant_id or 0, "" if r.product_id else (r.name or "").strip().lower(), int(r.qty or 0)) for r in rows))


def upgrade():
    bind = op.get_bind()
    flagged = bind.execute(sa.text(
        "SELECT o.id, o.duplicate_of_id, o.total, o.phone FROM orders o LEFT JOIN statuses s ON s.id = o.status_id "
        "WHERE o.duplicate_of_id IS NOT NULL AND COALESCE(s.code, '') <> 'duplicate'")).fetchall()
    if not flagged:
        return

    def items(order_id):
        return bind.execute(sa.text("SELECT product_id, variant_id, name, qty FROM order_items WHERE order_id = :i"), {"i": order_id}).fetchall()

    clear = []
    for o in flagged:
        other = bind.execute(sa.text("SELECT id, total, phone FROM orders WHERE id = :i"), {"i": o.duplicate_of_id}).fetchone()
        same = (other is not None and other.phone == o.phone and (other.total or 0) == (o.total or 0)
                and _sig(items(o.id)) == _sig(items(other.id)))
        if not same:
            clear.append(o.id)
    for i in range(0, len(clear), 500):
        bind.execute(sa.text("UPDATE orders SET duplicate_of_id = NULL WHERE id = ANY(:ids)"), {"ids": clear[i:i + 500]})


def downgrade():
    pass
