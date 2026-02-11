from __future__ import annotations

import uuid
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SQLAEnum
from sqlalchemy import String, Text, and_
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from core.common import ORMBase

if TYPE_CHECKING:
    from .character import Character
    from .panel import ComicPanel


class RenderableType(str, Enum):
    CHARACTER = "character"
    PANEL = "panel"


class RenderJobStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


def _render_job_character_join() -> Any:
    from .character import Character

    return and_(
        foreign(RenderJob.renderable_id) == Character.id,
        RenderJob.renderable_type == RenderableType.CHARACTER,
    )


def _render_job_panel_join() -> Any:
    from .panel import ComicPanel

    return and_(
        foreign(RenderJob.renderable_id) == ComicPanel.id,
        RenderJob.renderable_type == RenderableType.PANEL,
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
        primaryjoin=_render_job_character_join,
        back_populates="render_jobs",
        overlaps="panel,render_jobs",
    )
    panel: Mapped[ComicPanel | None] = relationship(
        "ComicPanel",
        primaryjoin=_render_job_panel_join,
        back_populates="render_jobs",
        overlaps="character,render_jobs",
    )
