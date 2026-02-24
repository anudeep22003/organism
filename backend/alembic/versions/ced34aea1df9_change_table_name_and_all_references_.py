"""change table name and all references from panel to scene

Revision ID: ced34aea1df9
Revises: 1ae41d62182d
Create Date: 2026-02-24 22:47:02.950077

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ced34aea1df9"
down_revision: Union[str, Sequence[str], None] = "1ae41d62182d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename tables/columns in place to preserve existing relational data.
    op.rename_table("comic_panel", "scene")
    op.rename_table("panel_character", "scene_character")

    op.alter_column("scene", "panel_order", new_column_name="scene_order")
    op.alter_column("scene_character", "panel_id", new_column_name="scene_id")

    op.execute(
        "ALTER TABLE scene RENAME CONSTRAINT uq_story_panel_order TO uq_story_scene_order"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "ALTER TABLE scene RENAME CONSTRAINT uq_story_scene_order TO uq_story_panel_order"
    )

    op.alter_column("scene_character", "scene_id", new_column_name="panel_id")
    op.alter_column("scene", "scene_order", new_column_name="panel_order")

    op.rename_table("scene_character", "panel_character")
    op.rename_table("scene", "comic_panel")
