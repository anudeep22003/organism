"""convert datetime to timezone aware

Revision ID: 20251115125248
Revises: b18536562f7a
Create Date: 2025-11-15 12:52:48.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20251115125248"
down_revision: Union[str, Sequence[str], None] = "b18536562f7a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert TIMESTAMP WITHOUT TIME ZONE to TIMESTAMP WITH TIME ZONE."""
    # Convert user table datetime columns
    # Interpret existing timestamps as UTC and convert to TIMESTAMP WITH TIME ZONE
    op.execute(
        """
        ALTER TABLE "user" 
        ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING (created_at AT TIME ZONE 'UTC'),
        ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING (updated_at AT TIME ZONE 'UTC');
        """
    )

    # Convert session table datetime columns
    op.execute(
        """
        ALTER TABLE session 
        ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING (created_at AT TIME ZONE 'UTC'),
        ALTER COLUMN expires_at TYPE TIMESTAMP WITH TIME ZONE USING (expires_at AT TIME ZONE 'UTC'),
        ALTER COLUMN revoked_at TYPE TIMESTAMP WITH TIME ZONE USING (revoked_at AT TIME ZONE 'UTC'),
        ALTER COLUMN last_used_at TYPE TIMESTAMP WITH TIME ZONE USING (last_used_at AT TIME ZONE 'UTC');
        """
    )


def downgrade() -> None:
    """Convert TIMESTAMP WITH TIME ZONE back to TIMESTAMP WITHOUT TIME ZONE."""
    # Convert user table datetime columns back
    op.execute(
        """
        ALTER TABLE "user" 
        ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE,
        ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE;
        """
    )

    # Convert session table datetime columns back
    op.execute(
        """
        ALTER TABLE session 
        ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE,
        ALTER COLUMN expires_at TYPE TIMESTAMP WITHOUT TIME ZONE,
        ALTER COLUMN revoked_at TYPE TIMESTAMP WITHOUT TIME ZONE,
        ALTER COLUMN last_used_at TYPE TIMESTAMP WITHOUT TIME ZONE;
        """
    )
