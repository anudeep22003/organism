"""add timestamps to story

Revision ID: 1831e46d4370
Revises: 6028e3da1ef9
Create Date: 2026-05-17 14:48:24.438609

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1831e46d4370"
down_revision: Union[str, Sequence[str], None] = "6028e3da1ef9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "story", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "story", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True)
    )

    op.execute(
        """
        UPDATE story
        SET
            created_at = COALESCE(
                (
                    SELECT edit_event.created_at
                    FROM edit_event
                    WHERE edit_event.id = story.source_event_id
                ),
                NOW()
            ),
            updated_at = COALESCE(
                (
                    SELECT edit_event.created_at
                    FROM edit_event
                    WHERE edit_event.id = story.source_event_id
                ),
                NOW()
            )
        """
    )

    op.alter_column("story", "created_at", nullable=False)
    op.alter_column("story", "updated_at", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("story", "updated_at")
    op.drop_column("story", "created_at")
