"""add canonical_render_id to character

Revision ID: c4f4431c3cd5
Revises: 49f4ab84e6e6
Create Date: 2026-04-06 13:30:19.964628

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4f4431c3cd5"
down_revision: Union[str, Sequence[str], None] = "49f4ab84e6e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add canonical_render_id FK to character table.

    Nullable — existing rows default to NULL and fall back to recency-ordered
    render query. Auto-populated on every new render going forward.
    ON DELETE SET NULL: deleting the referenced image clears the pointer
    without deleting the character.
    """
    op.add_column(
        "character",
        sa.Column(
            "canonical_render_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("image.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("character", "canonical_render_id")
