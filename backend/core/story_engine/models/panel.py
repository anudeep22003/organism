from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String, Text, and_
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint

from core.common import ORMBase

if TYPE_CHECKING:
    from .character import Character
    from .render_job import RenderJob
    from .story import Story


def _panel_render_job_join() -> Any:
    from .render_job import RenderableType, RenderJob

    return and_(
        ComicPanel.id == foreign(RenderJob.renderable_id),
        RenderJob.renderable_type == RenderableType.PANEL,
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
        viewonly=True,
    )
    render_jobs: Mapped[list[RenderJob]] = relationship(
        "RenderJob",
        primaryjoin=_panel_render_job_join,
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
