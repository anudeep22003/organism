from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from stripe import Customer
from stripe.checkout import Session

from core.common import ORMBase, get_current_datetime_utc


class StripeStatus(StrEnum):
    OPEN = "open"
    COMPLETE = "complete"
    EXPIRED = "expired"


class FulfillmentStatus(StrEnum):
    PENDING = "pending"
    FULFILLED = "fulfilled"
    FAILED = "failed"


class PaymentStatus(StrEnum):
    PAID = "paid"
    UNPAID = "unpaid"
    NO_PAYMENT_REQUIRED = "no_payment_required"


class PaymentIntent(StrEnum):
    SUBSCRIPTION_PURCHASE = "subscription_purchased"


class CheckoutSessionMode(StrEnum):
    PAYMENT = "payment"
    SUBSCRIPTION = "subscription"
    SETUP = "setup"


class CheckoutSession(ORMBase):
    __tablename__ = "checkout_session"
    __table_args__: object = (
        Index("ix_checkout_session_user_id", "user_id"),
        Index(
            "ix_checkout_session_stripe_session_id",
            "stripe_session_id",
            unique=True,
        ),
        Index(
            "ix_checkout_session_stripe_customer_record_id",
            "stripe_customer_record_id",
        ),
        Index(
            "ix_checkout_session_stripe_customer_id",
            "stripe_customer_id",
        ),
        Index(
            "ix_checkout_session_stripe_payment_intent_id",
            "stripe_payment_intent_id",
        ),
        Index(
            "ix_checkout_session_stripe_subscription_id",
            "stripe_subscription_id",
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

    stripe_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_customer_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stripe.customer.id", ondelete="CASCADE"),
        nullable=False,
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    mode: Mapped[str] = mapped_column(String(50), nullable=False)
    amount_total: Mapped[int | None] = mapped_column(nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    price_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    intent: Mapped[str] = mapped_column(String(100), nullable=False)
    livemode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    stripe_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=StripeStatus.OPEN.value
    )
    payment_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    fulfillment_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=FulfillmentStatus.PENDING.value
    )
    fulfillment_error: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_current_datetime_utc, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_current_datetime_utc,
        onupdate=get_current_datetime_utc,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    fulfilled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    raw: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    @classmethod
    def create_session_entry(
        cls,
        *,
        user_id: uuid.UUID,
        stripe_customer_record_id: uuid.UUID,
        stripe_customer_id: str,
        intent: PaymentIntent,
        price_id: str,
        mode: CheckoutSessionMode,
        stripe_status: StripeStatus,
        fulfillment_status: FulfillmentStatus,
        livemode: bool = False,
    ) -> "CheckoutSession":
        expires_at = get_current_datetime_utc() + timedelta(hours=24)
        return cls(
            user_id=user_id,
            stripe_customer_record_id=stripe_customer_record_id,
            stripe_customer_id=stripe_customer_id,
            intent=intent.value,
            price_id=price_id,
            mode=mode.value,
            livemode=livemode,
            stripe_status=stripe_status.value,
            fulfillment_status=fulfillment_status.value,
            expires_at=expires_at,
        )

    def update_session_entry_with_stripe_session(
        self,
        stripe_session: Session,
    ) -> "CheckoutSession":
        # we have to do this because stripe can return a customer object or just the id
        self.stripe_customer_id = self._extract_stripe_customer_id(stripe_session)
        self.stripe_session_id = stripe_session.id
        self.livemode = stripe_session.livemode
        if stripe_session.status is None:
            raise ValueError("Stripe session status not found")
        self.stripe_status = StripeStatus(stripe_session.status).value
        self.payment_status = stripe_session.payment_status
        self.amount_total = stripe_session.amount_total
        self.currency = stripe_session.currency
        self.stripe_payment_intent_id = self._extract_stripe_id(
            stripe_session.payment_intent
        )
        self.stripe_subscription_id = self._extract_stripe_id(
            stripe_session.subscription
        )
        self.expires_at = datetime.fromtimestamp(
            stripe_session.expires_at, timezone.utc
        )
        self.raw = stripe_session.to_dict()
        return self

    @staticmethod
    def _extract_stripe_customer_id(stripe_session: Session) -> str | None:
        if stripe_session.customer is None:
            return None
        if isinstance(stripe_session.customer, Customer):
            return stripe_session.customer.id
        if isinstance(stripe_session.customer, str):
            return stripe_session.customer
        raise ValueError("Invalid stripe customer type")

    @staticmethod
    def _extract_stripe_id(value: object | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if hasattr(value, "id") and isinstance(value.id, str):
            return value.id
        raise ValueError("Invalid Stripe expandable field type")
