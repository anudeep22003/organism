from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, and_
from sqlalchemy import Enum as SQLAEnum
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint

from core.common import ORMBase
from core.common.utils import get_current_datetime_utc


class RenderableType(str, Enum):
    CHARACTER = "character"
    PANEL = "panel"


class RenderJobStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class Project(ORMBase):
    __tablename__ = "project"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_current_datetime_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_current_datetime_utc,
        onupdate=get_current_datetime_utc,
    )
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    stories: Mapped[list[Story]] = relationship(
        "Story",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    @property
    def characters(self) -> list[Character]:
        seen_ids: set[uuid.UUID] = set()
        unique_characters: list[Character] = []
        for story in self.stories:
            for character in story.characters:
                if character.id in seen_ids:
                    continue
                seen_ids.add(character.id)
                unique_characters.append(character)
        return unique_characters

    @property
    def panels(self) -> list[ComicPanel]:
        return [panel for story in self.stories for panel in story.panels]


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
    )
    panels: Mapped[list[ComicPanel]] = relationship(
        "ComicPanel",
        back_populates="story",
        cascade="all, delete-orphan",
        order_by="ComicPanel.panel_order",
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
    )
    panel_characters: Mapped[list[PanelCharacter]] = relationship(
        "PanelCharacter",
        back_populates="character",
        cascade="all, delete-orphan",
    )
    panels: Mapped[list[ComicPanel]] = relationship(
        "ComicPanel",
        secondary="panel_character",
        back_populates="characters",
    )
    render_jobs: Mapped[list[RenderJob]] = relationship(
        "RenderJob",
        primaryjoin=lambda: and_(
            Character.id == foreign(RenderJob.renderable_id),
            RenderJob.renderable_type == RenderableType.CHARACTER,
        ),
        back_populates="character",
        overlaps="panel,render_jobs",
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


class ComicPanel(ORMBase):
    __tablename__ = "comic_panel"
    __table_args__ = (
        UniqueConstraint("story_id", "panel_order", name="uq_story_panel_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    story_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("story.id", ondelete="CASCADE"), nullable=False
    )
    panel_order: Mapped[int] = mapped_column(Integer, nullable=False)
    background: Mapped[str] = mapped_column(Text, default="")
    dialogue: Mapped[str] = mapped_column(Text, default="")
    user_input_text: Mapped[list[str]] = mapped_column(ARRAY(String()), default=list)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    story: Mapped[Story] = relationship("Story", back_populates="panels")
    panel_characters: Mapped[list[PanelCharacter]] = relationship(
        "PanelCharacter",
        back_populates="panel",
        cascade="all, delete-orphan",
    )
    characters: Mapped[list[Character]] = relationship(
        "Character",
        secondary="panel_character",
        back_populates="panels",
    )
    render_jobs: Mapped[list[RenderJob]] = relationship(
        "RenderJob",
        primaryjoin=lambda: and_(
            ComicPanel.id == foreign(RenderJob.renderable_id),
            RenderJob.renderable_type == RenderableType.PANEL,
        ),
        back_populates="panel",
        overlaps="character,render_jobs",
    )


class PanelCharacter(ORMBase):
    __tablename__ = "panel_character"

    panel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("comic_panel.id", ondelete="CASCADE"),
        primary_key=True,
    )
    character_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("character.id", ondelete="CASCADE"),
        primary_key=True,
    )
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    panel: Mapped[ComicPanel] = relationship(
        "ComicPanel", back_populates="panel_characters"
    )
    character: Mapped[Character] = relationship(
        "Character",
        back_populates="panel_characters",
    )


class RenderJob(ORMBase):
    __tablename__ = "render_job"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    renderable_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    renderable_type: Mapped[RenderableType] = mapped_column(
        SQLAEnum(RenderableType, name="renderable_type"),
        nullable=False,
    )
    output_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt: Mapped[str] = mapped_column(Text, default="")
    inputs: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    user_input_text: Mapped[list[str]] = mapped_column(ARRAY(String()), default=list)
    status: Mapped[RenderJobStatus] = mapped_column(
        SQLAEnum(RenderJobStatus, name="render_job_status"),
        default=RenderJobStatus.PENDING,
        nullable=False,
    )

    character: Mapped[Character | None] = relationship(
        "Character",
        primaryjoin=lambda: and_(
            foreign(RenderJob.renderable_id) == Character.id,
            RenderJob.renderable_type == RenderableType.CHARACTER,
        ),
        back_populates="render_jobs",
        overlaps="panel,render_jobs",
    )
    panel: Mapped[ComicPanel | None] = relationship(
        "ComicPanel",
        primaryjoin=lambda: and_(
            foreign(RenderJob.renderable_id) == ComicPanel.id,
            RenderJob.renderable_type == RenderableType.PANEL,
        ),
        back_populates="render_jobs",
        overlaps="character,render_jobs",
    )
