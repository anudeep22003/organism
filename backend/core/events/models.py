from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.common import ORMBase
from core.common.utils import get_current_datetime_utc


class EventStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class EventType(StrEnum):
    USER_CREATED = "user.created"


class AggregateType(StrEnum):
    """Identifies the primary domain entity the event belongs to."""

    USER = "user"


class Event(ORMBase):
    __tablename__ = "event"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    aggregate_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    aggregate_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=EventStatus.PENDING
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_current_datetime_utc, nullable=False
    )
    claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    failed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_current_datetime_utc, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_current_datetime_utc,
        onupdate=get_current_datetime_utc,
        nullable=False,
    )

    @classmethod
    def create(
        cls,
        *,
        event_type: str,
        payload: dict[str, Any],
        aggregate_type: str | None = None,
        aggregate_id: uuid.UUID | None = None,
    ) -> "Event":
        return cls(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
            status=EventStatus.PENDING.value,
        )

    def mark_completed(self, *, handled_at: datetime) -> None:
        self.status = EventStatus.COMPLETED.value
        self.claimed_at = handled_at
        self.processed_at = handled_at
        self.failed_at = None
        self.last_error = None
        self.attempt_count += 1

    def mark_failed(self, *, handled_at: datetime, error: str) -> None:
        self.status = EventStatus.FAILED.value
        self.claimed_at = handled_at
        self.processed_at = handled_at
        self.failed_at = handled_at
        self.last_error = error
        self.attempt_count += 1
