"""Юридичні особи (каса Checkbox і ключ НП за юрособою), відділ як сукупність джерел

Revision ID: 0009
Revises: 0008
"""
from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    return any(c["name"] == column for c in sa.inspect(op.get_bind()).get_columns(table))


def upgrade():
    if "legal_entities" not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table(
            "legal_entities",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("code", sa.String(20), nullable=False, server_default=""),
            sa.Column("iban", sa.String(34), nullable=False, server_default=""),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("sort", sa.Integer(), nullable=False, server_default="100"),
        )
    fk = lambda: sa.ForeignKey("legal_entities.id", ondelete="SET NULL")  # noqa: E731
    for table in ("orders", "checkbox_cashiers", "np_accounts"):
        if not _has_column(table, "legal_entity_id"):
            op.add_column(table, sa.Column("legal_entity_id", sa.Integer(), fk(), nullable=True))
    op.create_index("ix_orders_legal_entity_id", "orders", ["legal_entity_id"])
    if not _has_column("order_sources", "office_id"):
        op.add_column("order_sources", sa.Column("office_id", sa.Integer(),
                                                 sa.ForeignKey("offices.id", ondelete="SET NULL"), nullable=True))

    # Кожна наявна каса Checkbox — окрема юрособа (назву потім можна виправити в налаштуваннях).
    op.execute("""
        INSERT INTO legal_entities (name, sort)
        SELECT DISTINCT COALESCE(NULLIF(c.name, ''), 'Юрособа ' || c.id), MIN(c.sort) OVER (PARTITION BY c.name)
          FROM checkbox_cashiers c
    """)
    op.execute("""
        UPDATE checkbox_cashiers c SET legal_entity_id = le.id
          FROM legal_entities le WHERE le.name = COALESCE(NULLIF(c.name, ''), 'Юрособа ' || c.id)
    """)
    # за замовчуванням — юрособа каси, що була першою за порядком (раніше вона спрацьовувала «для всіх»)
    op.execute("""
        UPDATE legal_entities SET is_default = TRUE WHERE id = (
            SELECT c.legal_entity_id FROM checkbox_cashiers c WHERE c.is_active AND c.legal_entity_id IS NOT NULL
             ORDER BY (c.condition = 'none') DESC, c.sort, c.id LIMIT 1)
    """)
    # Відділ джерела — той, що найчастіше трапляється в замовленнях із цим джерелом.
    op.execute("""
        UPDATE order_sources s SET office_id = x.office_id FROM (
            SELECT DISTINCT ON (source_id) source_id, office_id
              FROM orders WHERE source_id IS NOT NULL AND office_id IS NOT NULL
             GROUP BY source_id, office_id ORDER BY source_id, COUNT(*) DESC) x
         WHERE x.source_id = s.id AND s.office_id IS NULL
    """)


def downgrade():
    op.drop_column("order_sources", "office_id")
    op.drop_index("ix_orders_legal_entity_id", "orders")
    for table in ("np_accounts", "checkbox_cashiers", "orders"):
        op.drop_column(table, "legal_entity_id")
    op.drop_table("legal_entities")
