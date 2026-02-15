"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-02-15 20:15:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "calendar_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("reminder_time", sa.DateTime(), nullable=True),
        sa.Column("is_reminded", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_calendar_events_user_id", "calendar_events", ["user_id"], unique=False)

    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column("transaction_type", sa.String(length=10), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_expenses_user_id", "expenses", ["user_id"], unique=False)

    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("default_currency", sa.String(length=10), nullable=True),
        sa.Column("reminder_enabled", sa.Boolean(), nullable=True),
        sa.Column("daily_reminder_time", sa.String(length=5), nullable=True),
        sa.Column("monthly_budget", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )


def downgrade():
    op.drop_table("user_preferences")
    op.drop_index("ix_expenses_user_id", table_name="expenses")
    op.drop_table("expenses")
    op.drop_index("ix_calendar_events_user_id", table_name="calendar_events")
    op.drop_table("calendar_events")
