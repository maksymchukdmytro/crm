"""Позначки — значок і колір (як у LP-CRM: «Терміново» — червоний знак оклику, «Очікує» — жовтий годинник…)

Revision ID: 0012
Revises: 0011
"""
from alembic import op
import sqlalchemy as sa

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade():
    cols = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("order_marks")}
    if "icon" not in cols:
        op.add_column("order_marks", sa.Column("icon", sa.String(24), nullable=False, server_default="tag"))
    if "color" not in cols:
        op.add_column("order_marks", sa.Column("color", sa.String(16), nullable=False, server_default="#475569"))
    from app.services.seed import MARK_LOOKS  # ті самі значки, що й для нової установки
    conn = op.get_bind()
    for name, (icon, color) in MARK_LOOKS.items():
        conn.execute(sa.text("UPDATE order_marks SET icon = :i, color = :c WHERE name = :n AND icon = 'tag'"),
                     {"i": icon, "c": color, "n": name})


def downgrade():
    op.drop_column("order_marks", "color")
    op.drop_column("order_marks", "icon")
