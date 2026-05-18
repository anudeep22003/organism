from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

import stripe
from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.common import ORMBase, get_current_datetime_utc


@dataclass
class StripeEventHotFields:
    customer_id: str | None
    subscription_id: str | None
    invoice_id: str | None


class StripeEventProcessingStatus(StrEnum):
    PENDING = "pending"
    PROCESSED = "processed"
    RETRYABLE_FAILED = "retryable_failed"
    TERMINAL_FAILED = "terminal_failed"


class StripeEvent(ORMBase):
    __tablename__ = "event"
    __table_args__: object = (
        Index("ix_event_customer_id", "customer_id"),
        Index("ix_event_event_type", "event_type"),
        Index("ix_event_stripe_event_id", "stripe_event_id", unique=True),
        {"schema": "stripe"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    stripe_event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    api_version: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # These extracted ids are useful for direct filtering, but none are guaranteed
    # across all Stripe event types.
    customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invoice_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_current_datetime_utc, nullable=False
    )
    processing_status: Mapped[str] = mapped_column(
        String(32),
        default=StripeEventProcessingStatus.PENDING.value,
        nullable=False,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_attempted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_current_datetime_utc, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_current_datetime_utc,
        onupdate=get_current_datetime_utc,
        nullable=False,
    )

    @staticmethod
    def _extract_hot_fields(*, event: stripe.Event) -> StripeEventHotFields:
        obj = event.data.object  # whatever resource the event is about
        if event.type.startswith("customer.subscription."):
            return StripeEventHotFields(
                customer_id=StripeEvent._extract_stripe_id(
                    getattr(obj, "customer", None)
                ),
                subscription_id=StripeEvent._extract_stripe_id(
                    getattr(obj, "id", None)
                ),
                invoice_id=StripeEvent._extract_stripe_id(
                    getattr(obj, "latest_invoice", None)
                ),
            )

        if event.type.startswith("customer."):
            return StripeEventHotFields(
                customer_id=StripeEvent._extract_stripe_id(getattr(obj, "id", None)),
                subscription_id=None,
                invoice_id=None,
            )

        if event.type.startswith("invoice."):
            return StripeEventHotFields(
                customer_id=StripeEvent._extract_stripe_id(
                    getattr(obj, "customer", None)
                ),
                subscription_id=StripeEvent._extract_invoice_subscription_id(obj),
                invoice_id=StripeEvent._extract_stripe_id(getattr(obj, "id", None)),
            )

        return StripeEventHotFields(
            customer_id=StripeEvent._extract_stripe_id(getattr(obj, "customer", None)),
            subscription_id=StripeEvent._extract_stripe_id(
                getattr(obj, "subscription", None)
            ),
            invoice_id=StripeEvent._extract_stripe_id(getattr(obj, "invoice", None)),
        )

    @staticmethod
    def _extract_invoice_subscription_id(invoice: object) -> str | None:
        top_level_subscription = StripeEvent._extract_stripe_id(
            getattr(invoice, "subscription", None)
        )
        if top_level_subscription is not None:
            return top_level_subscription

        lines = getattr(invoice, "lines", None)
        data = getattr(lines, "data", None)
        if not isinstance(data, list) or len(data) == 0:
            return None

        first_line = data[0]
        parent = getattr(first_line, "parent", None)
        subscription_item_details = getattr(parent, "subscription_item_details", None)
        return StripeEvent._extract_stripe_id(
            getattr(subscription_item_details, "subscription", None)
        )

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
    def create(
        cls,
        *,
        stripe_event: stripe.Event,
    ) -> "StripeEvent":
        hot_fields = cls._extract_hot_fields(event=stripe_event)
        return cls(
            stripe_event_id=stripe_event.id,
            event_type=stripe_event.type,
            api_version=stripe_event.api_version,
            customer_id=hot_fields.customer_id,
            subscription_id=hot_fields.subscription_id,
            invoice_id=hot_fields.invoice_id,
            payload=stripe_event.to_dict(),
            processing_status=StripeEventProcessingStatus.PENDING.value,
            attempt_count=0,
        )

    def mark_processing_attempt(self) -> "StripeEvent":
        self.attempt_count += 1
        self.last_attempted_at = get_current_datetime_utc()
        self.processing_error = None
        return self

    def mark_processed(self) -> "StripeEvent":
        self.processing_status = StripeEventProcessingStatus.PROCESSED.value
        self.processed_at = get_current_datetime_utc()
        self.processing_error = None
        return self

    def mark_retryable_failed(self, *, error: str) -> "StripeEvent":
        self.processing_status = StripeEventProcessingStatus.RETRYABLE_FAILED.value
        self.processing_error = error
        return self

    def mark_terminal_failed(self, *, error: str) -> "StripeEvent":
        self.processing_status = StripeEventProcessingStatus.TERMINAL_FAILED.value
        self.processing_error = error
        return self
