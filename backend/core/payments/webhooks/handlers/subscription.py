import uuid

import stripe
from loguru import logger

from core.payments.models import StripeCustomer, Subscription

from ..exceptions import NonRetryableStripeWebhookError, RetryableStripeWebhookError
from .base import BaseStripeWebhookHandler


class SubscriptionWebhookHandler(BaseStripeWebhookHandler):
    """Handle Stripe subscription lifecycle events against the local mirror.

    Flow:
    - Read the Stripe customer and subscription ids from the event payload.
    - Resolve the local Stripe customer or subscription rows that own the event.
    - Retry later if Stripe fired before the local mirror rows exist.
    - Create or refresh the local subscription mirror from the Stripe payload.
    - Reject anomalies like a second different active subscription for one user.
    """

    async def handle_created(self, stripe_event: stripe.Event) -> None:
        stripe_customer_id = Subscription.extract_stripe_customer_id(
            stripe_event=stripe_event
        )
        stripe_subscription_id = Subscription.extract_stripe_subscription_id(
            stripe_event=stripe_event
        )

        stripe_customer = await self._require_local_customer(stripe_customer_id)
        existing_subscription = (
            await self.repository.get_subscription_by_stripe_subscription_id(
                stripe_subscription_id
            )
        )
        if existing_subscription is not None:
            existing_subscription.update_from_stripe_event(stripe_event=stripe_event)
            await self.db.flush()
            return

        await self._ensure_no_conflicting_active_subscription(
            user_id=stripe_customer.user_id,
            stripe_subscription_id=stripe_subscription_id,
        )
        subscription = Subscription.create(
            user_id=stripe_customer.user_id,
            stripe_customer_record_id=stripe_customer.id,
            stripe_event=stripe_event,
        )
        self.repository.add_subscription(subscription)
        await self.db.flush()

    async def handle_updated(self, stripe_event: stripe.Event) -> None:
        subscription = await self._require_local_subscription(stripe_event=stripe_event)
        subscription.update_from_stripe_event(stripe_event=stripe_event)
        await self.db.flush()

    async def handle_deleted(self, stripe_event: stripe.Event) -> None:
        subscription = await self._require_local_subscription(stripe_event=stripe_event)
        # Cancellation only updates the Stripe mirror. Access continues to be
        # governed by the entitlement window granted by successful invoices.
        subscription.update_from_stripe_event(stripe_event=stripe_event)
        await self.db.flush()

    async def _require_local_customer(self, stripe_customer_id: str) -> StripeCustomer:
        stripe_customer = (
            await self.repository.get_stripe_customer_by_stripe_customer_id(
                stripe_customer_id
            )
        )
        if stripe_customer is None:
            raise RetryableStripeWebhookError(
                f"Stripe customer {stripe_customer_id} not found locally"
            )
        return stripe_customer

    async def _require_local_subscription(
        self, *, stripe_event: stripe.Event
    ) -> Subscription:
        stripe_subscription_id = Subscription.extract_stripe_subscription_id(
            stripe_event=stripe_event
        )
        subscription = await self.repository.get_subscription_by_stripe_subscription_id(
            stripe_subscription_id
        )
        if subscription is None:
            raise RetryableStripeWebhookError(
                f"Subscription {stripe_subscription_id} not found locally"
            )
        return subscription

    async def _ensure_no_conflicting_active_subscription(
        self,
        *,
        user_id: uuid.UUID,
        stripe_subscription_id: str,
    ) -> None:
        active_subscriptions = (
            await self.repository.get_active_subscriptions_by_user_id(user_id)
        )
        conflicting_subscriptions = [
            subscription
            for subscription in active_subscriptions
            if subscription.stripe_subscription_id != stripe_subscription_id
        ]
        if conflicting_subscriptions:
            logger.warning(
                "Conflicting active subscriptions found for user_id={}",
                user_id,
            )
            raise NonRetryableStripeWebhookError(
                f"Conflicting active subscription exists for user {user_id}"
            )
