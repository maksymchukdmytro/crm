"""Документи: реквізити юрособи (адреса, банк, телефон, ПДВ, підписант) і гарантія товару

Revision ID: 0015
Revises: 0014
"""
from alembic import op
import sqlalchemy as sa

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None

LE = [("code_label", sa.String(10), "РНОКПП"), ("address", sa.String(255), ""), ("bank", sa.String(160), ""),
      ("phone", sa.String(40), ""), ("vat_note", sa.String(80), "Без ПДВ"), ("signer", sa.String(120), "")]


def _cols(t):
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(t)}


def upgrade():
    have = _cols("legal_entities")
    for name, typ, default in LE:
        if name not in have:
            op.add_column("legal_entities", sa.Column(name, typ, nullable=False, server_default=default))
    if "warranty_months" not in _cols("products"):
        op.add_column("products", sa.Column("warranty_months", sa.Integer(), nullable=False, server_default="0"))


def downgrade():
    op.drop_column("products", "warranty_months")
    for name, _t, _d in LE:
        op.drop_column("legal_entities", name)
