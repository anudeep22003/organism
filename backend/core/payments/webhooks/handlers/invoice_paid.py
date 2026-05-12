import stripe

from core.payments.models import Entitlement, Invoice

from ..exceptions import NonRetryableStripeWebhookError, RetryableStripeWebhookError
from ..feature_mapping import resolve_feature_for_price
from .base import BaseStripeWebhookHandler


class InvoicePaidHandler(BaseStripeWebhookHandler):
    """Create invoice and entitlement state from a paid Stripe invoice.

    Flow:
    - Read the Stripe invoice id and stop early if this invoice was already stored.
    - Read the Stripe subscription id that the invoice belongs to.
    - Retry later if the event cannot be tied to a local subscription yet.
    - Check whether another invoice already exists for the same billed period.
    - Create the local invoice mirror row for this paid billing period.
    - Resolve which product feature this subscription price unlocks.
    - Create the entitlement if the same feature and period were not already granted.
    """

    async def handle(self, stripe_event: stripe.Event) -> None:
        stripe_invoice_id = Invoice.extract_stripe_invoice_id(stripe_event=stripe_event)
        existing_invoice = await self.repository.get_invoice_by_stripe_invoice_id(
            stripe_invoice_id
        )
        # Stripe can redeliver the same invoice event; the invoice mirror row is
        # the first domain-level dedupe boundary after StripeEvent persistence.
        if existing_invoice is not None:
            return

        stripe_subscription_id = Invoice.extract_stripe_subscription_id(
            stripe_event=stripe_event
        )
        # We only grant access for subscription-backed invoices. If the local
        # subscription mirror is missing, persist failure and retry later.
        if stripe_subscription_id is None:
            raise RetryableStripeWebhookError(
                f"Invoice {stripe_invoice_id} did not include a subscription id"
            )

        subscription = await self.repository.get_subscription_by_stripe_subscription_id(
            stripe_subscription_id
        )
        if subscription is None:
            raise RetryableStripeWebhookError(
                f"Subscription {stripe_subscription_id} not found locally"
            )

        period_start, period_end = Invoice.extract_service_period(
            stripe_event=stripe_event
        )
        conflicting_invoice = await self.repository.get_invoice_for_subscription_period(
            subscription_id=subscription.id,
            period_start=period_start,
            period_end=period_end,
            exclude_stripe_invoice_id=stripe_invoice_id,
        )
        # Two different invoice ids for the same billed period indicate local or
        # upstream anomaly; we do not mint a second invoice or entitlement.
        if conflicting_invoice is not None:
            raise NonRetryableStripeWebhookError(
                "A different invoice already exists for the same billed period"
            )

        invoice = Invoice.create(
            user_id=subscription.user_id,
            subscription_id=subscription.id,
            stripe_event=stripe_event,
        )
        self.repository.add_invoice(invoice)

        feature = resolve_feature_for_price(subscription.price_id)
        existing_entitlement = await self.repository.get_matching_entitlement(
            user_id=subscription.user_id,
            feature=feature,
            source="subscription",
            source_id=str(subscription.id),
            valid_from=invoice.period_start,
            valid_until=invoice.period_end,
        )
        # Entitlements are period-based. Matching source + feature + period makes
        # repeated invoice.paid delivery a no-op for access state.
        if existing_entitlement is None:
            entitlement = Entitlement.create_from_invoice_paid(
                user_id=subscription.user_id,
                feature=feature,
                stripe_event=stripe_event,
                source_id=str(subscription.id),
            )
            self.repository.add_entitlement(entitlement)

        await self.db.flush()
