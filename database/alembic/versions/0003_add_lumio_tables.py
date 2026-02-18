"""add conversation_history, memos, todo_items tables

Revision ID: 0003_add_lumio_tables
Revises: 0002_user_id_to_bigint
Create Date: 2026-02-18 00:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_add_lumio_tables"
down_revision = "0002_user_id_to_bigint"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "conversation_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversation_history_user_id", "conversation_history", ["user_id"], unique=False)

    op.create_table(
        "memos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_memos_user_id", "memos", ["user_id"], unique=False)

    op.create_table(
        "todo_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("content", sa.String(length=500), nullable=False),
        sa.Column("is_done", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("done_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_todo_items_user_id", "todo_items", ["user_id"], unique=False)


def downgrade():
    op.drop_index("ix_todo_items_user_id", table_name="todo_items")
    op.drop_table("todo_items")
    op.drop_index("ix_memos_user_id", table_name="memos")
    op.drop_table("memos")
    op.drop_index("ix_conversation_history_user_id", table_name="conversation_history")
    op.drop_table("conversation_history")
