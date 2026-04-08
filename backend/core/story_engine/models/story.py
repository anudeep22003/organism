from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.common import ORMBase

if TYPE_CHECKING:
    from .character import Character
    from .edit_event import EditEvent
    from .panel import Panel
    from .project import Project


class Story(ORMBase):
    __tablename__ = "story"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("edit_event.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    story_text: Mapped[str] = mapped_column(Text, default="")
    user_input_text: Mapped[str] = mapped_column(Text, default="")
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    name: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    project: Mapped[Project] = relationship("Project", back_populates="stories")
    source_event: Mapped[EditEvent | None] = relationship(
        "EditEvent", foreign_keys=[source_event_id]
    )
    characters: Mapped[list[Character]] = relationship(
        "Character", back_populates="story", cascade="all, delete-orphan"
    )
    panels: Mapped[list[Panel]] = relationship(
        "Panel", back_populates="story", cascade="all, delete-orphan"
    )
