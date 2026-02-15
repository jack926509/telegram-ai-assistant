"""migrate user_id columns to bigint

Revision ID: 0002_user_id_to_bigint
Revises: 0001_initial_schema
Create Date: 2026-02-15 22:10:00
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_user_id_to_bigint"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade():
    # Only alter when existing type is integer (for upgraded deployments).
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'calendar_events'
                  AND column_name = 'user_id'
                  AND data_type = 'integer'
            ) THEN
                ALTER TABLE calendar_events
                ALTER COLUMN user_id TYPE BIGINT;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'expenses'
                  AND column_name = 'user_id'
                  AND data_type = 'integer'
            ) THEN
                ALTER TABLE expenses
                ALTER COLUMN user_id TYPE BIGINT;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_preferences'
                  AND column_name = 'user_id'
                  AND data_type = 'integer'
            ) THEN
                ALTER TABLE user_preferences
                ALTER COLUMN user_id TYPE BIGINT;
            END IF;
        END$$;
        """
    )


def downgrade():
    op.execute(
        """
        ALTER TABLE calendar_events ALTER COLUMN user_id TYPE INTEGER;
        ALTER TABLE expenses ALTER COLUMN user_id TYPE INTEGER;
        ALTER TABLE user_preferences ALTER COLUMN user_id TYPE INTEGER;
        """
    )
