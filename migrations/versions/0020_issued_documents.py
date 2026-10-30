"""Новий інтерфейс, крок 6: видаткові накладні — видані документи зі знімком даних і нумерацією для юрособи й типу

Revision ID: 0020
Revises: 0019
"""
from alembic import op
import sqlalchemy as sa

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade():
    insp = sa.inspect(op.get_bind())
    tables = set(insp.get_table_names())
    if "issued_documents" not in tables:
        op.create_table(
            "issued_documents",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("kind", sa.String(10), nullable=False),
            sa.Column("legal_entity_id", sa.Integer(), sa.ForeignKey("legal_entities.id", ondelete="SET NULL"), nullable=True),
            sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True),
            sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
            sa.Column("number", sa.Integer(), nullable=False),
            sa.Column("number_text", sa.String(30), nullable=False),
            sa.Column("issued_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("total", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("snapshot", sa.JSON(), nullable=False),
            sa.Column("payload_hash", sa.String(64), nullable=False, server_default=""),
            sa.Column("state", sa.String(10), nullable=False, server_default="active"),
            sa.Column("replaced_by_id", sa.Integer(), sa.ForeignKey("issued_documents.id", ondelete="SET NULL"), nullable=True),
            sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("print_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_printed_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_issued_documents_legal_entity_id", "issued_documents", ["legal_entity_id"])
        op.create_index("ix_issued_documents_order_id", "issued_documents", ["order_id"])
        op.create_index("ix_issued_documents_issued_at", "issued_documents", ["issued_at"])
        op.create_index("ux_issued_documents_number", "issued_documents", ["legal_entity_id", "kind", "number"], unique=True)
    if "document_counters" not in tables:
        op.create_table(
            "document_counters",
            sa.Column("legal_entity_id", sa.Integer(), primary_key=True),
            sa.Column("kind", sa.String(10), primary_key=True),
            sa.Column("next_number", sa.Integer(), nullable=False, server_default="1"),
        )
    have = {c["name"] for c in insp.get_columns("legal_entities")}
    for c in ("waybill_prefix", "invoice_prefix", "warranty_prefix"):
        if c not in have:
            op.add_column("legal_entities", sa.Column(c, sa.String(10), nullable=True))


def downgrade():
    for c in ("warranty_prefix", "invoice_prefix", "waybill_prefix"):
        op.drop_column("legal_entities", c)
    op.drop_table("document_counters")
    op.drop_table("issued_documents")
