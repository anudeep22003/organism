from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.common import ORMBase, get_current_datetime_utc


class Plan(ORMBase):
    """App-owned subscription plan catalog entry in the public schema.

    Fields:
    - `id`: internal UUID primary key for relationships.
    - `plan_id`: stable app/API id, e.g. `pro_monthly`.
    - `display_name`: customer-facing name, e.g. `Pro`.
    - `description`: nullable marketing copy when a plan needs supporting text.
    - `stripe_price_id`: Stripe Price id mapped server-side, e.g. `price_123`.
    - `entitlement_feature`: app capability granted by the plan, e.g. `story_generation`.
    - `features`: JSON display bullets/cards, e.g. `[{"label": "Unlimited stories"}]`.
    - `amount_minor`, `currency`, `interval`: nullable cached display price fields;
      null lets us create non-public/manual/test plans or backfill Stripe price data later.
    - `is_active`: hides retired plans without breaking historical references.
    - `sort_order`: backend-owned frontend display order.
    - `created_at`, `updated_at`: audit timestamps.

    This table is not in the Stripe schema because it is our product catalog;
    Stripe identifiers are implementation details attached to the plan.
    """

    __tablename__ = "plan"
    __table_args__: object = (
        Index("ix_plan_plan_id", "plan_id", unique=True),
        Index("ix_plan_stripe_price_id", "stripe_price_id", unique=True),
        Index("ix_plan_active_sort_order", "is_active", "sort_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan_id: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    stripe_price_id: Mapped[str] = mapped_column(String(255), nullable=False)
    entitlement_feature: Mapped[str] = mapped_column(String(255), nullable=False)
    features: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    amount_minor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    interval: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_current_datetime_utc, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_current_datetime_utc,
        onupdate=get_current_datetime_utc,
        nullable=False,
    )
