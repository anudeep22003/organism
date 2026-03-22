from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.common import ORMBase

if TYPE_CHECKING:
    from .character import Character
    from .project import Project
    from .scene import Scene


class Story(ORMBase):
    __tablename__ = "story"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    story_text: Mapped[str] = mapped_column(Text, default="")
    user_input_text: Mapped[list[str]] = mapped_column(ARRAY(String()), default=list)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    project: Mapped[Project] = relationship("Project", back_populates="stories")
    story_characters: Mapped[list[StoryCharacter]] = relationship(
        "StoryCharacter",
        back_populates="story",
        cascade="all, delete-orphan",
    )
    characters: Mapped[list[Character]] = relationship(
        "Character",
        secondary="story_character",
        back_populates="stories",
        viewonly=True,
    )
    scenes: Mapped[list[Scene]] = relationship(
        "Scene",
        back_populates="story",
        cascade="all, delete-orphan",
        order_by="Scene.scene_order",
    )


class StoryCharacter(ORMBase):
    __tablename__ = "story_character"

    story_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("story.id", ondelete="CASCADE"), primary_key=True
    )
    character_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("character.id", ondelete="CASCADE"),
        primary_key=True,
    )
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    story: Mapped[Story] = relationship("Story", back_populates="story_characters")
    character: Mapped[Character] = relationship(
        "Character",
        back_populates="story_characters",
    )
