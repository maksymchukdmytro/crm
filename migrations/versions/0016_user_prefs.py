"""Новий інтерфейс, крок 2: збережені фільтри й налаштування користувача

Revision ID: 0016
Revises: 0015
"""
from alembic import op
import sqlalchemy as sa

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def _tables():
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade():
    have = _tables()
    if "saved_filters" not in have:
        op.create_table(
            "saved_filters",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("section", sa.String(20), nullable=False, server_default="orders"),
            sa.Column("name", sa.String(80), nullable=False),
            sa.Column("color", sa.String(9), nullable=False, server_default="#2E6BE6"),
            sa.Column("query", sa.Text(), nullable=False, server_default=""),
            sa.Column("sort", sa.Integer(), nullable=False, server_default="100"),
            sa.Column("is_shared", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_saved_filters_user_id", "saved_filters", ["user_id"])
    if "user_prefs" not in have:
        op.create_table(
            "user_prefs",
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("key", sa.String(60), primary_key=True),
            sa.Column("value", sa.JSON(), nullable=True),
        )


def downgrade():
    op.drop_table("user_prefs")
    op.drop_index("ix_saved_filters_user_id", table_name="saved_filters")
    op.drop_table("saved_filters")
