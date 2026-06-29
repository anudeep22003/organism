from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.common import ORMBase, get_current_datetime_utc


class StripeCustomer(ORMBase):
    __tablename__ = "customer"
    __table_args__: object = (
        Index(
            "ix_customer_user_livemode",
            "user_id",
            "livemode",
            unique=True,
        ),
        Index(
            "ix_customer_stripe_customer_id",
            "stripe_customer_id",
            unique=True,
        ),
        {"schema": "stripe"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    stripe_customer_id: Mapped[str] = mapped_column(String(255), nullable=False)
    stripe_object: Mapped[str] = mapped_column(String(50), nullable=False)
    livemode: Mapped[bool] = mapped_column(Boolean, nullable=False)
    raw_stripe_object: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    stripe_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_current_datetime_utc, nullable=False
    )
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
        user_id: uuid.UUID,
        stripe_customer_id: str,
        stripe_created_at: datetime,
        livemode: bool,
        raw_stripe_object: dict,
        stripe_object: str,
    ) -> "StripeCustomer":
        return cls(
            user_id=user_id,
            stripe_customer_id=stripe_customer_id,
            stripe_created_at=stripe_created_at,
            livemode=livemode,
            raw_stripe_object=raw_stripe_object,
            stripe_object=stripe_object,
        )
