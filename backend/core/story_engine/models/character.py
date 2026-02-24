from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String, Text, and_
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint

from core.common import ORMBase

if TYPE_CHECKING:
    from .render_job import RenderJob
    from .scene import Scene, SceneCharacter
    from .story import Story, StoryCharacter


def _character_render_job_join() -> Any:
    from .render_job import RenderableType, RenderJob

    return and_(
        Character.id == foreign(RenderJob.renderable_id),
        RenderJob.renderable_type == RenderableType.CHARACTER,
    )


class Character(ORMBase):
    __tablename__ = "character"
    __table_args__ = (
        UniqueConstraint("user_id", "slug", name="uq_character_user_slug"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    brief: Mapped[str] = mapped_column(Text, default="")
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    user_input_text: Mapped[list[str]] = mapped_column(ARRAY(String()), default=list)
    reference_image_urls: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    story_characters: Mapped[list[StoryCharacter]] = relationship(
        "StoryCharacter",
        back_populates="character",
        cascade="all, delete-orphan",
    )
    stories: Mapped[list[Story]] = relationship(
        "Story",
        secondary="story_character",
        back_populates="characters",
        viewonly=True,
    )
    scene_characters: Mapped[list[SceneCharacter]] = relationship(
        "SceneCharacter",
        back_populates="character",
        cascade="all, delete-orphan",
    )
    scenes: Mapped[list[Scene]] = relationship(
        "Scene",
        secondary="scene_character",
        back_populates="characters",
        viewonly=True,
    )
    render_jobs: Mapped[list[RenderJob]] = relationship(
        "RenderJob",
        primaryjoin=_character_render_job_join,
        back_populates="character",
        overlaps="scene,render_jobs",
    )
