import stripe

from core.payments.models import Subscription

from ..exceptions import RetryableStripeWebhookError
from .base import BaseStripeWebhookHandler


class CustomerSubscriptionDeletedHandler(BaseStripeWebhookHandler):
    """Refresh the local subscription mirror when Stripe deletes a subscription.

    Flow:
    - Read the Stripe subscription id from the event payload.
    - Find the local subscription row for that Stripe subscription.
    - Retry later if the local subscription mirror does not exist yet.
    - Update the local subscription status and cancellation fields from Stripe.
    - Leave entitlements alone because access is governed by entitlement dates.
    """

    async def handle(self, stripe_event: stripe.Event) -> None:
        stripe_subscription_id = Subscription.extract_stripe_subscription_id(
            stripe_event=stripe_event
        )
        existing_subscription = (
            await self.repository.get_subscription_by_stripe_subscription_id(
                stripe_subscription_id
            )
        )
        if existing_subscription is None:
            raise RetryableStripeWebhookError(
                f"Subscription {stripe_subscription_id} not found locally"
            )

        # Deletion updates the Stripe mirror only. Period-based access remains
        # governed by entitlement validity and is not revoked here.
        existing_subscription.update_from_stripe_event(stripe_event=stripe_event)
        await self.db.flush()
