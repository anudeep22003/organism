from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.common import ORMBase, get_current_datetime_utc


class Entitlement(ORMBase):
    __tablename__ = "entitlement"
    __table_args__: object = (
        Index("ix_entitlement_user_feature", "user_id", "feature"),
        # Use a normal composite index here; the requested NOW()-based partial
        # index would be invalid in Postgres because the predicate is not immutable.
        Index(
            "ix_entitlement_active_lookup",
            "user_id",
            "feature",
            "valid_until",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    feature: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_current_datetime_utc, nullable=False
    )
