import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    CheckoutSession,
    Entitlement,
    Invoice,
    StripeCustomer,
    StripeEvent,
    Subscription,
)
from .models.subscription import StripeSubscriptionStatus


class PaymentsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_stripe_customer_by_user_id(
        self, user_id: uuid.UUID
    ) -> StripeCustomer | None:
        query = select(StripeCustomer).where(StripeCustomer.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def add_stripe_customer(self, stripe_customer: StripeCustomer) -> None:
        self.db.add(stripe_customer)

    def add_checkout_session(self, checkout_session: CheckoutSession) -> None:
        self.db.add(checkout_session)

    async def get_stripe_customer_by_stripe_customer_id(
        self, stripe_customer_id: str
    ) -> StripeCustomer | None:
        query = select(StripeCustomer).where(
            StripeCustomer.stripe_customer_id == stripe_customer_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_stripe_event_by_stripe_event_id(
        self, stripe_event_id: str
    ) -> StripeEvent | None:
        query = select(StripeEvent).where(
            StripeEvent.stripe_event_id == stripe_event_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def add_stripe_event(self, stripe_event: StripeEvent) -> None:
        self.db.add(stripe_event)

    async def get_subscriptions_by_user_id(
        self, user_id: uuid.UUID
    ) -> list[Subscription]:
        query = select(Subscription).where(Subscription.user_id == user_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_active_subscriptions_by_user_id(
        self, user_id: uuid.UUID
    ) -> list[Subscription]:
        query = select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.status.in_(
                [
                    StripeSubscriptionStatus.ACTIVE.value,
                    StripeSubscriptionStatus.TRIALING.value,
                ]
            ),
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_subscription_by_stripe_subscription_id(
        self, stripe_subscription_id: str
    ) -> Subscription | None:
        query = select(Subscription).where(
            Subscription.stripe_subscription_id == stripe_subscription_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def add_subscription(self, subscription: Subscription) -> None:
        self.db.add(subscription)

    async def get_invoice_by_stripe_invoice_id(
        self, stripe_invoice_id: str
    ) -> Invoice | None:
        query = select(Invoice).where(Invoice.stripe_invoice_id == stripe_invoice_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_invoice_for_subscription_period(
        self,
        *,
        subscription_id: uuid.UUID,
        period_start: datetime,
        period_end: datetime,
        exclude_stripe_invoice_id: str | None = None,
    ) -> Invoice | None:
        query = select(Invoice).where(
            Invoice.subscription_id == subscription_id,
            Invoice.period_start == period_start,
            Invoice.period_end == period_end,
        )
        if exclude_stripe_invoice_id is not None:
            query = query.where(Invoice.stripe_invoice_id != exclude_stripe_invoice_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def add_invoice(self, invoice: Invoice) -> None:
        self.db.add(invoice)

    async def get_matching_entitlement(
        self,
        *,
        user_id: uuid.UUID,
        feature: str,
        source: str,
        source_id: str | None,
        valid_from: datetime,
        valid_until: datetime | None,
    ) -> Entitlement | None:
        query = select(Entitlement).where(
            Entitlement.user_id == user_id,
            Entitlement.feature == feature,
            Entitlement.source == source,
            Entitlement.valid_from == valid_from,
            Entitlement.valid_until == valid_until,
        )
        if source_id is None:
            query = query.where(Entitlement.source_id.is_(None))
        else:
            query = query.where(Entitlement.source_id == source_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def add_entitlement(self, entitlement: Entitlement) -> None:
        self.db.add(entitlement)
