"""add character.source_event_id

Revision ID: c7e01ef411e3
Revises: a60670590304
Create Date: 2026-03-11 12:45:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7e01ef411e3"
down_revision: Union[str, Sequence[str], None] = "a60670590304"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("character", sa.Column("source_event_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_character_source_event_id",
        "character",
        "edit_event",
        ["source_event_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_character_source_event_id", "character", type_="foreignkey")
    op.drop_column("character", "source_event_id")
