from __future__ import annotations

import uuid
from datetime import datetime

import stripe
from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.common import ORMBase, get_current_datetime_utc

from .invoice import Invoice


class Entitlement(ORMBase):
    __tablename__ = "entitlement"
    # This table intentionally lives in the default public schema because it is
    # app-owned access state, not a Stripe mirror.
    __table_args__: object = (
        Index("ix_entitlement_user_feature", "user_id", "feature"),
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

    @classmethod
    def create_from_invoice_paid(
        cls,
        *,
        user_id: uuid.UUID,
        feature: str,
        stripe_event: stripe.Event,
        source: str = "subscription",
        source_id: str | None = None,
    ) -> "Entitlement":
        period_start, period_end = Invoice._extract_service_period(
            stripe_event.data.object
        )
        return cls(
            user_id=user_id,
            feature=feature,
            source=source,
            source_id=source_id,
            valid_from=period_start,
            valid_until=period_end,
        )
