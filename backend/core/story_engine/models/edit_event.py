from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.common import ORMBase
from core.common.utils import get_current_datetime_utc


class EditEventTargetType(StrEnum):
    STORY = "story"
    CHARACTER = "character"
    PANEL = "panel"


class EditEventOperationType(StrEnum):
    GENERATE_STORY = "generate_story"
    REFINE_STORY = "refine_story"
    REFINE_CHARACTER = "refine_character"
    UPLOAD_REFERENCE_IMAGE = "upload_reference_image"
    RENDER_CHARACTER = "render_character"
    RENDER_CHARACTER_EDIT = "render_character_edit"
    GENERATE_PANEL = "generate_panel"
    RENDER_PANEL = "render_panel"
    RENDER_PANEL_EDIT = "render_panel_edit"


class EditEventStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class EditEvent(ORMBase):
    __tablename__ = "edit_event"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    operation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    user_instruction: Mapped[str] = mapped_column(Text, nullable=False)
    input_snapshot: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, default=None
    )
    output_snapshot: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, default=None
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=EditEventStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_current_datetime_utc
    )

    @classmethod
    def create_edit_event(
        cls,
        project_id: uuid.UUID,
        target_type: str,
        target_id: uuid.UUID,
        operation_type: EditEventOperationType,
        user_instruction: str,
        status: EditEventStatus,
        input_snapshot: dict[str, Any] | None = None,
        output_snapshot: dict[str, Any] | None = None,
    ) -> EditEvent:
        return cls(
            project_id=project_id,
            target_type=target_type,
            target_id=target_id,
            operation_type=operation_type.value,
            user_instruction=user_instruction,
            input_snapshot=input_snapshot,
            output_snapshot=output_snapshot,
            status=status.value,
        )
