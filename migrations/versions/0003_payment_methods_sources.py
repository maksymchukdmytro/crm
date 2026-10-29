"""Довідники як у LP-CRM: види оплат, відділи, джерела, причини статусів, позначки; країна й додаткові поля замовлення

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "payment_methods",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("icon", sa.String(32), nullable=False, server_default="cash"),
        sa.Column("kind", sa.String(10), nullable=False, server_default="cod"),
        sa.Column("checkbox_type", sa.String(20), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort", sa.Integer(), nullable=False, server_default="100"),
    )
    op.create_table(
        "order_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort", sa.Integer(), nullable=False, server_default="100"),
    )
    op.create_table(
        "offices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort", sa.Integer(), nullable=False, server_default="100"),
    )
    op.create_table(
        "status_reasons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("status_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort", sa.Integer(), nullable=False, server_default="100"),
    )
    op.create_table(
        "order_marks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort", sa.Integer(), nullable=False, server_default="100"),
    )
    op.add_column("users", sa.Column("offices", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("orders", sa.Column("office_id", sa.Integer(), sa.ForeignKey("offices.id"), nullable=True))
    op.create_index("ix_orders_office_id", "orders", ["office_id"])
    op.add_column("orders", sa.Column("reason_id", sa.Integer(), sa.ForeignKey("status_reasons.id"), nullable=True))
    op.add_column("orders", sa.Column("mark_id", sa.Integer(), sa.ForeignKey("order_marks.id"), nullable=True))
    op.add_column("orders", sa.Column("remind_at", sa.DateTime(), nullable=True))
    op.create_index("ix_orders_remind_at", "orders", ["remind_at"])
    op.add_column("orders", sa.Column("country", sa.String(2), nullable=False, server_default="UA"))
    op.add_column("orders", sa.Column("payment_method_id", sa.Integer(), sa.ForeignKey("payment_methods.id"), nullable=True))
    op.add_column("orders", sa.Column("source_id", sa.Integer(), sa.ForeignKey("order_sources.id"), nullable=True))
    op.create_index("ix_orders_source_id", "orders", ["source_id"])
    for i in range(1, 5):
        op.add_column("orders", sa.Column(f"extra{i}", sa.String(255), nullable=False, server_default=""))

    from app.services.seed import DEFAULT_MARKS, DEFAULT_PAYMENT_METHODS, DEFAULT_REASONS, DEFAULT_SOURCES
    conn = op.get_bind()
    for sort, (pid, name, icon, kind, cb, active) in enumerate(DEFAULT_PAYMENT_METHODS):
        conn.execute(sa.text("INSERT INTO payment_methods (id, name, icon, kind, checkbox_type, is_active, sort) "
                             "VALUES (:id, :n, :i, :k, :c, :a, :s)"),
                     {"id": pid, "n": name, "i": icon, "k": kind, "c": cb, "a": active, "s": sort * 10})
    if conn.dialect.name == "postgresql":
        conn.execute(sa.text("SELECT setval(pg_get_serial_sequence('payment_methods','id'), (SELECT MAX(id) FROM payment_methods))"))
    for sort, name in enumerate(DEFAULT_SOURCES):
        conn.execute(sa.text("INSERT INTO order_sources (name, sort) VALUES (:n, :s)"), {"n": name, "s": sort * 10})
    refuse = [r[0] for r in conn.execute(sa.text("SELECT id FROM statuses WHERE code = 'cancelled'")).fetchall()]
    import json
    for sort, name in enumerate(DEFAULT_REASONS):
        conn.execute(sa.text("INSERT INTO status_reasons (name, status_ids, sort) VALUES (:n, :st, :s)"),
                     {"n": name, "st": json.dumps(refuse), "s": sort * 10})
    for sort, name in enumerate(DEFAULT_MARKS):
        conn.execute(sa.text("INSERT INTO order_marks (name, sort) VALUES (:n, :s)"), {"n": name, "s": sort * 10})
    # наявні замовлення: вид оплати з типу, джерело «Сайти», якщо заявка з лендингу
    conn.execute(sa.text("UPDATE orders SET payment_method_id = CASE payment_type WHEN 'prepaid' THEN 1 "
                         "WHEN 'partial' THEN 2 ELSE 16 END"))
    conn.execute(sa.text("UPDATE orders SET source_id = (SELECT id FROM order_sources WHERE name = 'Сайти') "
                         "WHERE site <> '' OR utm_source <> ''"))


def downgrade():
    for col in ("country", "remind_at", "mark_id", "reason_id"):
        op.drop_column("orders", col)
    op.drop_index("ix_orders_office_id", "orders")
    op.drop_column("orders", "office_id")
    op.drop_column("users", "offices")
    for t in ("order_marks", "status_reasons", "offices"):
        op.drop_table(t)
    for i in range(1, 5):
        op.drop_column("orders", f"extra{i}")
    op.drop_index("ix_orders_source_id", "orders")
    op.drop_column("orders", "source_id")
    op.drop_column("orders", "payment_method_id")
    op.drop_table("order_sources")
    op.drop_table("payment_methods")
