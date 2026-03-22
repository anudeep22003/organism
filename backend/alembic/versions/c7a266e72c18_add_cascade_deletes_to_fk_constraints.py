"""add_cascade_deletes_to_fk_constraints

Revision ID: c7a266e72c18
Revises: 600fb91bc05b
Create Date: 2026-03-22 18:39:06.018391

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7a266e72c18"
down_revision: Union[str, Sequence[str], None] = "600fb91bc05b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # character.story_id → story.id  (CASCADE)
    op.drop_constraint("character_story_id_fkey", "character", type_="foreignkey")
    op.create_foreign_key(
        "character_story_id_fkey",
        "character",
        "story",
        ["story_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # character.source_event_id → edit_event.id  (SET NULL)
    op.drop_constraint("fk_character_source_event_id", "character", type_="foreignkey")
    op.create_foreign_key(
        "fk_character_source_event_id",
        "character",
        "edit_event",
        ["source_event_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # image.character_id → character.id  (CASCADE)
    op.drop_constraint("image_character_id_fkey", "image", type_="foreignkey")
    op.create_foreign_key(
        "image_character_id_fkey",
        "image",
        "character",
        ["character_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # image.project_id → project.id  (CASCADE)
    op.drop_constraint("image_project_id_fkey", "image", type_="foreignkey")
    op.create_foreign_key(
        "image_project_id_fkey",
        "image",
        "project",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # image.user_id → user.id  (CASCADE)
    op.drop_constraint("image_user_id_fkey", "image", type_="foreignkey")
    op.create_foreign_key(
        "image_user_id_fkey",
        "image",
        "user",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # project.user_id → user.id  (CASCADE)
    op.drop_constraint("project_user_id_fkey", "project", type_="foreignkey")
    op.create_foreign_key(
        "project_user_id_fkey",
        "project",
        "user",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # session.user_id → user.id  (CASCADE)
    op.drop_constraint("session_user_id_fkey", "session", type_="foreignkey")
    op.create_foreign_key(
        "session_user_id_fkey",
        "session",
        "user",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # story.source_event_id → edit_event.id  (SET NULL)
    op.drop_constraint("fk_story_source_event_id", "story", type_="foreignkey")
    op.create_foreign_key(
        "fk_story_source_event_id",
        "story",
        "edit_event",
        ["source_event_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # story.source_event_id
    op.drop_constraint("fk_story_source_event_id", "story", type_="foreignkey")
    op.create_foreign_key(
        "fk_story_source_event_id",
        "story",
        "edit_event",
        ["source_event_id"],
        ["id"],
    )

    # session.user_id
    op.drop_constraint("session_user_id_fkey", "session", type_="foreignkey")
    op.create_foreign_key(
        "session_user_id_fkey",
        "session",
        "user",
        ["user_id"],
        ["id"],
    )

    # project.user_id
    op.drop_constraint("project_user_id_fkey", "project", type_="foreignkey")
    op.create_foreign_key(
        "project_user_id_fkey",
        "project",
        "user",
        ["user_id"],
        ["id"],
    )

    # image.*
    op.drop_constraint("image_character_id_fkey", "image", type_="foreignkey")
    op.create_foreign_key(
        "image_character_id_fkey",
        "image",
        "character",
        ["character_id"],
        ["id"],
    )
    op.drop_constraint("image_user_id_fkey", "image", type_="foreignkey")
    op.create_foreign_key(
        "image_user_id_fkey",
        "image",
        "user",
        ["user_id"],
        ["id"],
    )
    op.drop_constraint("image_project_id_fkey", "image", type_="foreignkey")
    op.create_foreign_key(
        "image_project_id_fkey",
        "image",
        "project",
        ["project_id"],
        ["id"],
    )

    # character.*
    op.drop_constraint("fk_character_source_event_id", "character", type_="foreignkey")
    op.create_foreign_key(
        "fk_character_source_event_id",
        "character",
        "edit_event",
        ["source_event_id"],
        ["id"],
    )
    op.drop_constraint("character_story_id_fkey", "character", type_="foreignkey")
    op.create_foreign_key(
        "character_story_id_fkey",
        "character",
        "story",
        ["story_id"],
        ["id"],
    )
