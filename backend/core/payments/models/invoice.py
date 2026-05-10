from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import stripe
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.common import ORMBase, get_current_datetime_utc


@dataclass(frozen=True, slots=True)
class StripeInvoiceFields:
    stripe_invoice_id: str
    status: str
    amount_paid: int
    currency: str
    period_start: datetime
    period_end: datetime
    paid_at: datetime | None
    raw: dict[str, Any]


class Invoice(ORMBase):
    __tablename__ = "invoice"
    __table_args__: object = (
        Index("ix_invoice_user_id", "user_id"),
        Index("ix_invoice_subscription_id", "subscription_id"),
        Index("ix_invoice_stripe_invoice_id", "stripe_invoice_id", unique=True),
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
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stripe.subscription.id"),
        nullable=True,
    )
    stripe_invoice_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    amount_paid: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_current_datetime_utc, nullable=False
    )
    raw: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    @classmethod
    def create(
        cls,
        *,
        user_id: uuid.UUID,
        stripe_event: stripe.Event,
        subscription_id: uuid.UUID | None = None,
    ) -> "Invoice":
        fields = cls._extract_fields(stripe_event=stripe_event)
        return cls(
            user_id=user_id,
            subscription_id=subscription_id,
            stripe_invoice_id=fields.stripe_invoice_id,
            status=fields.status,
            amount_paid=fields.amount_paid,
            currency=fields.currency,
            period_start=fields.period_start,
            period_end=fields.period_end,
            paid_at=fields.paid_at,
            raw=fields.raw,
        )

    @classmethod
    def _extract_fields(cls, *, stripe_event: stripe.Event) -> StripeInvoiceFields:
        invoice = stripe_event.data.object
        period_start, period_end = cls._extract_service_period(invoice)

        return StripeInvoiceFields(
            stripe_invoice_id=cls._require_stripe_id(invoice.id),
            status=cls._require_str(invoice.status, field_name="status"),
            amount_paid=cls._require_int(invoice.amount_paid, field_name="amount_paid"),
            currency=cls._require_str(invoice.currency, field_name="currency"),
            period_start=period_start,
            period_end=period_end,
            paid_at=cls._extract_paid_at(invoice),
            raw=invoice.to_dict(),
        )

    @classmethod
    def _extract_service_period(cls, invoice: object) -> tuple[datetime, datetime]:
        line_period = cls._extract_first_line_period(invoice)
        if line_period is not None:
            return line_period

        period_start = cls._timestamp_to_datetime(
            getattr(invoice, "period_start", None)
        )
        period_end = cls._timestamp_to_datetime(getattr(invoice, "period_end", None))
        if period_start is None or period_end is None:
            raise ValueError("Stripe invoice did not include a billable period")
        return (period_start, period_end)

    @classmethod
    def _extract_first_line_period(
        cls, invoice: object
    ) -> tuple[datetime, datetime] | None:
        lines = getattr(invoice, "lines", None)
        data = getattr(lines, "data", None)
        if not isinstance(data, list) or len(data) == 0:
            return None

        first_line = data[0]
        period = getattr(first_line, "period", None)
        period_start = cls._timestamp_to_datetime(getattr(period, "start", None))
        period_end = cls._timestamp_to_datetime(getattr(period, "end", None))
        if period_start is None or period_end is None:
            return None
        return (period_start, period_end)

    @classmethod
    def _extract_paid_at(cls, invoice: object) -> datetime | None:
        status_transitions = getattr(invoice, "status_transitions", None)
        paid_at = getattr(status_transitions, "paid_at", None)
        return cls._timestamp_to_datetime(paid_at)

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
    def _require_int(value: object, *, field_name: str) -> int:
        if not isinstance(value, int):
            raise ValueError(f"Expected {field_name} to be an integer")
        return value
