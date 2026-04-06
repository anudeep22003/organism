"""add canonical_render_id to panel

Revision ID: 446dd67bbfc8
Revises: c4f4431c3cd5
Create Date: 2026-04-06 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from alembic import op

revision: str = "446dd67bbfc8"
down_revision: Union[str, Sequence[str], None] = "c4f4431c3cd5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add canonical_render_id FK to panel table.

    Nullable — existing rows default to NULL and fall back to recency-ordered
    render query. Auto-populated on every new render going forward.
    ON DELETE SET NULL: deleting the referenced image clears the pointer
    without deleting the panel.
    """
    op.add_column(
        "panel",
        sa.Column(
            "canonical_render_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("image.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("panel", "canonical_render_id")
