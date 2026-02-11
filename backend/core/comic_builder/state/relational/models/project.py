from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.comic_builder.state.consolidated import (
    initialize_empty_consolidated_state_dict,
)
from core.common import ORMBase
from core.common.utils import get_current_datetime_utc

if TYPE_CHECKING:
    from .character import Character
    from .panel import ComicPanel
    from .story import Story


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
    # TODO: default state initialization for backward compatibilty, can be removed after full migration
    state: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=initialize_empty_consolidated_state_dict
    )

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
