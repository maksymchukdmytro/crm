"""Етап 6: категорії, виробники, атрибути, варіанти й фото товарів; покупці, групи, заблоковані IP

Revision ID: 0008
Revises: 0007
"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

MONEY = sa.Numeric(12, 2)


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _has_column(table: str, column: str) -> bool:
    return any(c["name"] == column for c in sa.inspect(op.get_bind()).get_columns(table))


def _add(table: str, column: sa.Column):
    if not _has_column(table, column.name):
        op.add_column(table, column)


def upgrade():
    t = _tables()
    if "categories" not in t:
        op.create_table(
            "categories",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(160), nullable=False),
            sa.Column("parent_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
            sa.Column("sort", sa.Integer(), nullable=False, server_default="100"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
        op.create_index("ix_categories_parent_id", "categories", ["parent_id"])
    if "manufacturers" not in t:
        op.create_table(
            "manufacturers",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(160), nullable=False, unique=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
    if "attribute_groups" not in t:
        op.create_table(
            "attribute_groups",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(120), nullable=False),
            sa.Column("sort", sa.Integer(), nullable=False, server_default="100"),
        )
    if "attributes" not in t:
        op.create_table(
            "attributes",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("group_id", sa.Integer(), sa.ForeignKey("attribute_groups.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(120), nullable=False),
            sa.Column("sort", sa.Integer(), nullable=False, server_default="100"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
        op.create_index("ix_attributes_group_id", "attributes", ["group_id"])

    _add("products", sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True))
    _add("products", sa.Column("manufacturer_id", sa.Integer(), sa.ForeignKey("manufacturers.id", ondelete="SET NULL"), nullable=True))
    _add("products", sa.Column("model", sa.String(120), nullable=False, server_default=""))
    _add("products", sa.Column("description", sa.Text(), nullable=False, server_default=""))
    _add("products", sa.Column("countries", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
    _add("products", sa.Column("spec_price", MONEY, nullable=False, server_default="0"))
    _add("products", sa.Column("wholesale_price", MONEY, nullable=False, server_default="0"))
    if not any(i["name"] == "ix_products_category_id" for i in sa.inspect(op.get_bind()).get_indexes("products")):
        op.create_index("ix_products_category_id", "products", ["category_id"])

    if "product_variants" not in t:
        op.create_table(
            "product_variants",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(255), nullable=False, server_default=""),
            sa.Column("sku", sa.String(64), nullable=True, unique=True),
            sa.Column("attribute_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
            sa.Column("price", MONEY, nullable=True),
            sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("reserved", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("sort", sa.Integer(), nullable=False, server_default="100"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
        op.create_index("ix_product_variants_product_id", "product_variants", ["product_id"])
    if "product_photos" not in t:
        op.create_table(
            "product_photos",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
            sa.Column("file", sa.String(255), nullable=False),
            sa.Column("sort", sa.Integer(), nullable=False, server_default="100"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_product_photos_product_id", "product_photos", ["product_id"])

    fk = lambda: sa.ForeignKey("product_variants.id", ondelete="SET NULL")  # noqa: E731
    _add("order_items", sa.Column("variant_id", sa.Integer(), fk(), nullable=True))
    _add("purchase_items", sa.Column("variant_id", sa.Integer(), fk(), nullable=True))
    _add("stock_movements", sa.Column("variant_id", sa.Integer(), fk(), nullable=True))
    if not any(i["name"] == "ix_stock_movements_variant_id" for i in sa.inspect(op.get_bind()).get_indexes("stock_movements")):
        op.create_index("ix_stock_movements_variant_id", "stock_movements", ["variant_id"])

    if "customer_groups" not in t:
        op.create_table(
            "customer_groups",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(80), nullable=False),
            sa.Column("color", sa.String(9), nullable=False, server_default="#64748b"),
            sa.Column("sort", sa.Integer(), nullable=False, server_default="100"),
        )
        op.execute("""INSERT INTO customer_groups (name, color, sort) VALUES
            ('Покупець', '#64748b', 10), ('Оптовик', '#0ea5e9', 20), ('Дропшипер', '#a855f7', 30), ('Партнер', '#16a34a', 40)""")
    if "customers" not in t:
        op.create_table(
            "customers",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("phone", sa.String(32), nullable=False),
            sa.Column("name", sa.String(255), nullable=False, server_default=""),
            sa.Column("email", sa.String(255), nullable=False, server_default=""),
            sa.Column("country", sa.String(2), nullable=False, server_default="UA"),
            sa.Column("group_id", sa.Integer(), sa.ForeignKey("customer_groups.id", ondelete="SET NULL"), nullable=True),
            sa.Column("comment", sa.Text(), nullable=False, server_default=""),
            sa.Column("is_blacklisted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("blacklist_reason", sa.String(255), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_customers_phone", "customers", ["phone"], unique=True)
    if "blocked_ips" not in t:
        op.create_table(
            "blocked_ips",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("ip", sa.String(64), nullable=False, unique=True),
            sa.Column("comment", sa.String(255), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
    _add("orders", sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True))
    if not any(i["name"] == "ix_orders_customer_id" for i in sa.inspect(op.get_bind()).get_indexes("orders")):
        op.create_index("ix_orders_customer_id", "orders", ["customer_id"])

    # Покупці з наявних замовлень: один на телефон, ім'я й пошта — з найсвіжішого замовлення.
    op.execute("""
        INSERT INTO customers (phone, name, email, country, group_id, created_at, updated_at)
        SELECT o.phone,
               (array_agg(o.customer_name ORDER BY o.created_at DESC))[1],
               COALESCE((array_agg(o.email ORDER BY o.created_at DESC) FILTER (WHERE o.email <> ''))[1], ''),
               COALESCE((array_agg(o.country ORDER BY o.created_at DESC))[1], 'UA'),
               (SELECT id FROM customer_groups ORDER BY sort, id LIMIT 1),
               MIN(o.created_at), MAX(o.created_at)
          FROM orders o
         WHERE o.phone <> ''
         GROUP BY o.phone
        ON CONFLICT (phone) DO NOTHING
    """)
    op.execute("UPDATE orders o SET customer_id = c.id FROM customers c WHERE c.phone = o.phone AND o.customer_id IS NULL")


def downgrade():
    op.drop_index("ix_orders_customer_id", "orders")
    op.drop_column("orders", "customer_id")
    for tname in ("blocked_ips", "customers", "customer_groups"):
        op.drop_table(tname)
    op.drop_index("ix_stock_movements_variant_id", "stock_movements")
    for tname in ("stock_movements", "purchase_items", "order_items"):
        op.drop_column(tname, "variant_id")
    op.drop_table("product_photos")
    op.drop_table("product_variants")
    op.drop_index("ix_products_category_id", "products")
    for c in ("wholesale_price", "spec_price", "countries", "description", "model", "manufacturer_id", "category_id"):
        op.drop_column("products", c)
    op.drop_table("attributes")
    op.drop_table("attribute_groups")
    op.drop_table("manufacturers")
    op.drop_table("categories")
