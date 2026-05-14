from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

import stripe
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.common import ORMBase, get_current_datetime_utc


@dataclass(frozen=True, slots=True)
class StripeSubscriptionFields:
    stripe_subscription_id: str
    stripe_customer_id: str
    status: str
    price_id: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    canceled_at: datetime | None
    trial_end: datetime | None
    raw: dict[str, Any]


class StripeSubscriptionStatus(StrEnum):
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    PAUSED = "paused"
    CANCELED = "canceled"


class Subscription(ORMBase):
    __tablename__ = "subscription"
    __table_args__: object = (
        Index("ix_subscription_user_id", "user_id"),
        Index(
            "ix_subscription_stripe_customer_record_id",
            "stripe_customer_record_id",
        ),
        Index("ix_subscription_stripe_customer_id", "stripe_customer_id"),
        Index(
            "ix_subscription_stripe_subscription_id",
            "stripe_subscription_id",
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
    stripe_customer_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stripe.customer.id", ondelete="CASCADE"),
        nullable=False,
    )
    stripe_subscription_id: Mapped[str] = mapped_column(String(255), nullable=False)
    stripe_customer_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    price_id: Mapped[str] = mapped_column(String(255), nullable=False)
    current_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    current_period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    canceled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    trial_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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
    raw: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    @classmethod
    def create(
        cls,
        *,
        user_id: uuid.UUID,
        stripe_customer_record_id: uuid.UUID,
        stripe_event: stripe.Event,
    ) -> "Subscription":
        fields = cls._extract_fields(stripe_event=stripe_event)
        return cls(
            user_id=user_id,
            stripe_customer_record_id=stripe_customer_record_id,
            stripe_subscription_id=fields.stripe_subscription_id,
            stripe_customer_id=fields.stripe_customer_id,
            status=fields.status,
            price_id=fields.price_id,
            current_period_start=fields.current_period_start,
            current_period_end=fields.current_period_end,
            cancel_at_period_end=fields.cancel_at_period_end,
            canceled_at=fields.canceled_at,
            trial_end=fields.trial_end,
            raw=fields.raw,
        )

    def is_active(self) -> bool:
        return self.status in {
            StripeSubscriptionStatus.ACTIVE.value,
            StripeSubscriptionStatus.TRIALING.value,
        }

    def update_from_stripe_event(self, *, stripe_event: stripe.Event) -> "Subscription":
        fields = self._extract_fields(stripe_event=stripe_event)
        self.stripe_subscription_id = fields.stripe_subscription_id
        self.stripe_customer_id = fields.stripe_customer_id
        self.status = fields.status
        self.price_id = fields.price_id
        self.current_period_start = fields.current_period_start
        self.current_period_end = fields.current_period_end
        self.cancel_at_period_end = fields.cancel_at_period_end
        self.canceled_at = fields.canceled_at
        self.trial_end = fields.trial_end
        self.raw = fields.raw
        return self

    @classmethod
    def extract_stripe_subscription_id(cls, *, stripe_event: stripe.Event) -> str:
        return cls._require_stripe_id(stripe_event.data.object.id)

    @classmethod
    def extract_stripe_customer_id(cls, *, stripe_event: stripe.Event) -> str:
        return cls._require_stripe_id(stripe_event.data.object.customer)

    @classmethod
    def _extract_fields(cls, *, stripe_event: stripe.Event) -> StripeSubscriptionFields:
        subscription = stripe_event.data.object
        stripe_subscription_id = cls._require_stripe_id(subscription.id)
        stripe_customer_id = cls._require_stripe_id(subscription.customer)
        price_id = cls._extract_price_id(subscription)
        current_period_start = cls._extract_period_start(subscription)
        current_period_end = cls._extract_period_end(subscription)

        return StripeSubscriptionFields(
            stripe_subscription_id=stripe_subscription_id,
            stripe_customer_id=stripe_customer_id,
            status=cls._require_str(subscription.status, field_name="status"),
            price_id=price_id,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            cancel_at_period_end=cls._require_bool(
                subscription.cancel_at_period_end,
                field_name="cancel_at_period_end",
            ),
            canceled_at=cls._timestamp_to_datetime(subscription.canceled_at),
            trial_end=cls._timestamp_to_datetime(subscription.trial_end),
            raw=cls._require_dict(subscription.to_dict(), field_name="raw"),
        )

    @classmethod
    def _extract_price_id(cls, subscription: object) -> str:
        price_id = cls._extract_first_subscription_item_price_id(subscription)
        if price_id is not None:
            return price_id
        plan = getattr(subscription, "plan", None)
        plan_id = cls._extract_stripe_id(plan)
        if plan_id is None:
            raise ValueError("Stripe subscription did not include a price or plan id")
        return plan_id

    @classmethod
    def _extract_period_start(cls, subscription: object) -> datetime:
        current_period_start = cls._timestamp_to_datetime(
            getattr(subscription, "current_period_start", None)
        )
        if current_period_start is not None:
            return current_period_start

        first_item = cls._extract_first_subscription_item(subscription)
        item_period_start = cls._timestamp_to_datetime(
            getattr(first_item, "current_period_start", None)
        )
        if item_period_start is None:
            raise ValueError(
                "Stripe subscription did not include a current period start"
            )
        return item_period_start

    @classmethod
    def _extract_period_end(cls, subscription: object) -> datetime:
        current_period_end = cls._timestamp_to_datetime(
            getattr(subscription, "current_period_end", None)
        )
        if current_period_end is not None:
            return current_period_end

        first_item = cls._extract_first_subscription_item(subscription)
        item_period_end = cls._timestamp_to_datetime(
            getattr(first_item, "current_period_end", None)
        )
        if item_period_end is None:
            raise ValueError("Stripe subscription did not include a current period end")
        return item_period_end

    @staticmethod
    def _extract_first_subscription_item(subscription: object) -> object:
        items = getattr(subscription, "items", None)
        data = getattr(items, "data", None)
        if not isinstance(data, list) or len(data) == 0:
            raise ValueError(
                "Stripe subscription did not include any subscription items"
            )
        return data[0]

    @classmethod
    def _extract_first_subscription_item_price_id(
        cls, subscription: object
    ) -> str | None:
        first_item = cls._extract_first_subscription_item(subscription)
        price = getattr(first_item, "price", None)
        return cls._extract_stripe_id(price)

    @staticmethod
    def _timestamp_to_datetime(value: int | None) -> datetime | None:
        if value is None:
            return None
        return datetime.fromtimestamp(value, tz=timezone.utc)

    @staticmethod
    def _extract_stripe_id(value: object | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if hasattr(value, "id") and isinstance(value.id, str):
            return value.id
        raise ValueError("Invalid Stripe expandable field type")

    @classmethod
    def _require_stripe_id(cls, value: object | None) -> str:
        stripe_id = cls._extract_stripe_id(value)
        if stripe_id is None:
            raise ValueError("Expected Stripe id but found none")
        return stripe_id

    @staticmethod
    def _require_str(value: object, *, field_name: str) -> str:
        if not isinstance(value, str):
            raise ValueError(f"Expected {field_name} to be a string")
        return value

    @staticmethod
    def _require_bool(value: object, *, field_name: str) -> bool:
        if not isinstance(value, bool):
            raise ValueError(f"Expected {field_name} to be a boolean")
        return value

    @staticmethod
    def _require_dict(value: object, *, field_name: str) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError(f"Expected {field_name} to be a dictionary")
        return value
