"""Нова Пошта: кілька ключів (акаунтів), правила статусів ТТН → статус замовлення, розміри товару

Revision ID: 0004
Revises: 0003
"""
import re

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    s = lambda n, d="": sa.Column(n, sa.String(255), nullable=False, server_default=d)  # noqa: E731
    op.create_table(
        "np_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False, server_default=""),
        sa.Column("api_key", sa.String(64), nullable=False, server_default=""),
        s("sender_ref"), s("sender_name"), s("contact_ref"), s("contact_name"), s("sender_phone"),
        s("city_name"), s("city_ref"), s("warehouse_name"), s("warehouse_ref"),
        sa.Column("payer", sa.String(16), nullable=False, server_default="Recipient"),
        sa.Column("cargo_type", sa.String(16), nullable=False, server_default="Parcel"),
        sa.Column("service_type", sa.String(24), nullable=False, server_default="WarehouseWarehouse"),
        sa.Column("cod_mode", sa.String(16), nullable=False, server_default="backward"),
        sa.Column("cod_payer", sa.String(16), nullable=False, server_default="Recipient"),
        sa.Column("info_comment", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("info_items", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("info_item_ids", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("default_weight", sa.Numeric(8, 3), nullable=False, server_default="0.5"),
        sa.Column("seat_size", sa.String(32), nullable=False, server_default="20x15x10"),
        s("description", "Товар"),
        sa.Column("office_id", sa.Integer(), sa.ForeignKey("offices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("directory", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.create_table(
        "np_status_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("np_code", sa.String(8), nullable=False),
        sa.Column("status_id", sa.Integer(), sa.ForeignKey("statuses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("except_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("sort", sa.Integer(), nullable=False, server_default="100"),
    )
    op.add_column("orders", sa.Column("np_account_id", sa.Integer(),
                                      sa.ForeignKey("np_accounts.id", ondelete="SET NULL"), nullable=True))
    for col in ("length", "width", "height"):
        op.add_column("products", sa.Column(col, sa.Numeric(7, 1), nullable=False, server_default="0"))
    op.add_column("products", sa.Column("ship_description", sa.String(255), nullable=False, server_default=""))

    # перенести наявні налаштування НП (один ключ) у перший акаунт.
    # Старі налаштування зберігалися без перевірки, тож значення чистимо: «0,5 кг» → 0.5, задовгі рядки обрізаємо.
    conn = op.get_bind()
    st = {k: (v or "").strip() for k, v in conn.execute(sa.text("SELECT key, value FROM settings WHERE key LIKE 'np%'")).fetchall()}

    def cut(key, n, default=""):
        return (st.get(key) or default)[:n]

    def weight():
        m = re.search(r"\d+(?:[.,]\d+)?", st.get("np_default_weight", ""))
        try:
            w = float(m.group(0).replace(",", ".")) if m else 0.5
        except ValueError:
            w = 0.5
        return w if 0 < w < 10000 else 0.5

    def pick(key, allowed, default):
        v = st.get(key, "")
        return v if v in allowed else default

    if st.get("np_api_key"):
        conn.execute(sa.text(
            "INSERT INTO np_accounts (name, api_key, sender_ref, contact_ref, sender_phone, city_name, city_ref, "
            "warehouse_name, warehouse_ref, payer, cod_mode, default_weight, seat_size, description, is_default) "
            "VALUES (:name, :key, :sref, :cref, :phone, :city, :cityref, :wh, :whref, :payer, :cod, :w, :size, :descr, true)"),
            {"name": "Основний ключ", "key": cut("np_api_key", 64), "sref": cut("np_sender_ref", 255),
             "cref": cut("np_contact_ref", 255), "phone": cut("np_sender_phone", 255),
             "city": cut("np_city_name", 255), "cityref": cut("np_city_ref", 255),
             "wh": cut("np_warehouse_name", 255), "whref": cut("np_warehouse_ref", 255),
             "payer": pick("np_payer", ("Recipient", "Sender", "ThirdPerson"), "Recipient"),
             "cod": pick("np_cod_mode", ("backward", "afterpayment", "none"), "backward"),
             "w": weight(), "size": cut("np_seat_size", 32, "20x15x10"), "descr": cut("np_description", 255, "Товар")})

def downgrade():
    op.drop_column("products", "ship_description")
    for col in ("length", "width", "height"):
        op.drop_column("products", col)
    op.drop_column("orders", "np_account_id")
    op.drop_table("np_status_rules")
    op.drop_table("np_accounts")
