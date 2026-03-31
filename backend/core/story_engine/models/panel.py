from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.common import ORMBase
from core.common.utils import get_current_datetime_utc

if TYPE_CHECKING:
    from .edit_event import EditEvent
    from .story import Story


class Panel(ORMBase):
    __tablename__ = "panel"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    story_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("story.id", ondelete="CASCADE"), nullable=False
    )
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("edit_event.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    attributes: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_current_datetime_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_current_datetime_utc,
        onupdate=get_current_datetime_utc,
    )

    story: Mapped[Story] = relationship("Story", back_populates="panels")
    source_event: Mapped[EditEvent | None] = relationship(
        "EditEvent", foreign_keys=[source_event_id]
    )

    @classmethod
    def create(
        cls,
        story_id: uuid.UUID,
        order_index: int,
        attributes: dict[str, Any] | None = None,
    ) -> "Panel":
        return cls(
            story_id=story_id,
            order_index=order_index,
            attributes=attributes or {},
        )
