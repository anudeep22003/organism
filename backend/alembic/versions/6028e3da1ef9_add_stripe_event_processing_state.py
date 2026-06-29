"""add stripe event processing state

Revision ID: 6028e3da1ef9
Revises: 83cfc31b233c
Create Date: 2026-05-15 07:20:20.419681

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6028e3da1ef9"
down_revision: Union[str, Sequence[str], None] = "83cfc31b233c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "event",
        sa.Column(
            "processing_status",
            sa.String(length=32),
            nullable=False,
            server_default="pending",
        ),
        schema="stripe",
    )
    op.add_column(
        "event",
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        schema="stripe",
    )
    op.add_column(
        "event",
        sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True),
        schema="stripe",
    )
    op.execute(
        """
        UPDATE stripe.event
        SET
            processing_status = CASE
                WHEN processed_at IS NOT NULL THEN 'processed'
                WHEN processing_error IS NOT NULL THEN 'retryable_failed'
                ELSE 'pending'
            END,
            attempt_count = CASE
                WHEN processed_at IS NOT NULL OR processing_error IS NOT NULL THEN 1
                ELSE 0
            END,
            last_attempted_at = CASE
                WHEN processed_at IS NOT NULL THEN processed_at
                WHEN processing_error IS NOT NULL THEN updated_at
                ELSE NULL
            END
        """
    )
    op.alter_column(
        "event",
        "processing_status",
        schema="stripe",
        server_default=None,
    )
    op.alter_column(
        "event",
        "attempt_count",
        schema="stripe",
        server_default=None,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("event", "last_attempted_at", schema="stripe")
    op.drop_column("event", "attempt_count", schema="stripe")
    op.drop_column("event", "processing_status", schema="stripe")
