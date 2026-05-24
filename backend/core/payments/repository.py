import uuid
from datetime import datetime
from typing import Final

from sqlalchemy import and_, case, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    CheckoutSession,
    Entitlement,
    Invoice,
    Plan,
    StripeCustomer,
    StripeEvent,
    Subscription,
)
from .models.subscription import StripeSubscriptionStatus

DEFAULT_ENTITLEMENT_FEATURE: Final[str] = "pro_tier"


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

    async def list_active_plans(self) -> list[Plan]:
        query = (
            select(Plan)
            .where(Plan.is_active.is_(True))
            .order_by(Plan.sort_order.asc(), Plan.display_name.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_active_plan_by_plan_id(self, plan_id: str) -> Plan | None:
        query = select(Plan).where(
            Plan.plan_id == plan_id,
            Plan.is_active.is_(True),
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

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

    async def get_stripe_event_by_id(
        self, stripe_event_id: uuid.UUID
    ) -> StripeEvent | None:
        query = select(StripeEvent).where(StripeEvent.id == stripe_event_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_drainable_stripe_events(self, *, limit: int) -> list[StripeEvent]:
        query = (
            select(StripeEvent)
            .where(StripeEvent.processing_status.in_(["pending", "retryable_failed"]))
            .order_by(StripeEvent.received_at.asc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_retryable_stripe_events_by_customer_id(
        self, *, stripe_customer_id: str, limit: int
    ) -> list[StripeEvent]:
        query = (
            select(StripeEvent)
            .where(
                StripeEvent.customer_id == stripe_customer_id,
                StripeEvent.processing_status == "retryable_failed",
            )
            .order_by(StripeEvent.received_at.asc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

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

    async def get_blocking_checkout_subscription_by_user_id(
        self, user_id: uuid.UUID
    ) -> Subscription | None:
        query = select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.status.in_(
                [
                    StripeSubscriptionStatus.ACTIVE.value,
                    StripeSubscriptionStatus.TRIALING.value,
                    StripeSubscriptionStatus.PAST_DUE.value,
                    StripeSubscriptionStatus.UNPAID.value,
                    StripeSubscriptionStatus.PAUSED.value,
                ]
            ),
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_most_relevant_subscription_by_user_id(
        self, user_id: uuid.UUID
    ) -> Subscription | None:
        status_rank = case(
            (
                Subscription.status.in_(
                    [
                        StripeSubscriptionStatus.ACTIVE.value,
                        StripeSubscriptionStatus.TRIALING.value,
                    ]
                ),
                0,
            ),
            (
                Subscription.status.in_(
                    [
                        StripeSubscriptionStatus.PAST_DUE.value,
                        StripeSubscriptionStatus.UNPAID.value,
                        StripeSubscriptionStatus.PAUSED.value,
                    ]
                ),
                1,
            ),
            (Subscription.status == StripeSubscriptionStatus.INCOMPLETE.value, 2),
            (
                Subscription.status.in_(
                    [
                        StripeSubscriptionStatus.CANCELED.value,
                        StripeSubscriptionStatus.INCOMPLETE_EXPIRED.value,
                    ]
                ),
                3,
            ),
            else_=4,
        )
        query = (
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .order_by(
                status_rank.asc(),
                desc(Subscription.current_period_end),
                desc(Subscription.updated_at),
            )
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

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
        """Get an invoice for a subscription period, excluding a specific invoice id if provided."""
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

    async def list_current_entitlements(
        self,
        *,
        user_id: uuid.UUID,
        now: datetime,
    ) -> list[Entitlement]:
        query = (
            select(Entitlement)
            .where(
                and_(
                    Entitlement.user_id == user_id,
                    Entitlement.valid_from <= now,
                    or_(
                        Entitlement.valid_until.is_(None),
                        Entitlement.valid_until > now,
                    ),
                )
            )
            .order_by(Entitlement.feature.asc(), Entitlement.valid_until.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_plan_by_stripe_price_id(self, price_id: str) -> Plan | None:
        query = select(Plan).where(Plan.stripe_price_id == price_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def has_current_entitlement(
        self,
        *,
        user_id: uuid.UUID,
        feature: str,
        now: datetime,
    ) -> bool:
        query = (
            select(Entitlement.id)
            .where(
                and_(
                    Entitlement.user_id == user_id,
                    Entitlement.feature == feature,
                    Entitlement.valid_from <= now,
                    or_(
                        Entitlement.valid_until.is_(None),
                        Entitlement.valid_until > now,
                    ),
                )
            )
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
