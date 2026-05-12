import stripe
from loguru import logger

from core.payments.models import Subscription

from ..exceptions import NonRetryableStripeWebhookError, RetryableStripeWebhookError
from .base import BaseStripeWebhookHandler


class CustomerSubscriptionCreatedHandler(BaseStripeWebhookHandler):
    """Mirror a new Stripe subscription into the local database.

    Flow:
    - Read the Stripe customer id and subscription id from the event payload.
    - Find the local Stripe customer row that owns this subscription.
    - Retry later if the local Stripe customer mirror does not exist yet.
    - Update the local subscription if this Stripe subscription was already seen.
    - Reject the event if the user already has a different active subscription.
    - Otherwise create the local subscription mirror row.
    """

    async def handle(self, stripe_event: stripe.Event) -> None:
        stripe_customer_id = Subscription.extract_stripe_customer_id(
            stripe_event=stripe_event
        )
        stripe_subscription_id = Subscription.extract_stripe_subscription_id(
            stripe_event=stripe_event
        )

        stripe_customer = (
            await self.repository.get_stripe_customer_by_stripe_customer_id(
                stripe_customer_id
            )
        )
        # Webhooks can arrive before the local Stripe mirror exists. Treat that as
        # retryable so the persisted StripeEvent can be replayed after reconciliation.
        if stripe_customer is None:
            raise RetryableStripeWebhookError(
                f"Stripe customer {stripe_customer_id} not found locally"
            )

        existing_subscription = (
            await self.repository.get_subscription_by_stripe_subscription_id(
                stripe_subscription_id
            )
        )
        # `customer.subscription.created` is also our upsert signal for the Stripe
        # mirror row, so re-delivery just refreshes the existing local record.
        if existing_subscription is not None:
            existing_subscription.update_from_stripe_event(stripe_event=stripe_event)
            await self.db.flush()
            return

        active_subscriptions = (
            await self.repository.get_active_subscriptions_by_user_id(
                stripe_customer.user_id
            )
        )
        conflicting_subscriptions = [
            subscription
            for subscription in active_subscriptions
            if subscription.stripe_subscription_id != stripe_subscription_id
        ]
        # Current product policy is one active subscription per user. A different
        # active local subscription is an anomaly, not something we silently replace.
        if conflicting_subscriptions:
            logger.warning(
                "Conflicting active subscriptions found for user_id={}",
                stripe_customer.user_id,
            )
            raise NonRetryableStripeWebhookError(
                f"Conflicting active subscription exists for user {stripe_customer.user_id}"
            )

        subscription = Subscription.create(
            user_id=stripe_customer.user_id,
            stripe_customer_record_id=stripe_customer.id,
            stripe_event=stripe_event,
        )
        self.repository.add_subscription(subscription)
        await self.db.flush()
