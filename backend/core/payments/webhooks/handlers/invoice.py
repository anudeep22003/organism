import stripe

from core.payments.models import Entitlement, Invoice, Subscription

from ..exceptions import NonRetryableStripeWebhookError, RetryableStripeWebhookError
from ..feature_mapping import resolve_feature_for_price
from .base import BaseStripeWebhookHandler


class InvoiceWebhookHandler(BaseStripeWebhookHandler):
    """Handle Stripe invoice lifecycle events for billing periods and access.

    Flow:
    - Read the Stripe invoice and subscription ids from the event payload.
    - Resolve the local subscription that owns the billing period.
    - Create or refresh the local invoice mirror row for this Stripe invoice.
    - Reject anomalies like two different invoice ids for the same period.
    - Grant entitlement only when the invoice is successfully paid.
    - Leave failed invoices as billing records only and wait for later recovery.
    """

    async def handle_paid(self, stripe_event: stripe.Event) -> None:
        subscription = await self._require_local_subscription(stripe_event=stripe_event)
        invoice = await self._create_or_update_invoice(
            stripe_event=stripe_event,
            subscription=subscription,
            reject_period_conflicts=True,
        )

        feature = resolve_feature_for_price(subscription.price_id)
        existing_entitlement = await self.repository.get_matching_entitlement(
            user_id=subscription.user_id,
            feature=feature,
            source="subscription",
            source_id=str(subscription.id),
            valid_from=invoice.period_start,
            valid_until=invoice.period_end,
        )
        # Matching source + feature + billed period makes repeated paid delivery,
        # or failed-then-paid recovery for the same invoice, idempotent.
        if existing_entitlement is None:
            entitlement = Entitlement.create_from_invoice_paid(
                user_id=subscription.user_id,
                feature=feature,
                stripe_event=stripe_event,
                source_id=str(subscription.id),
            )
            self.repository.add_entitlement(entitlement)

        await self.db.flush()

    async def handle_payment_failed(self, stripe_event: stripe.Event) -> None:
        subscription = await self._require_local_subscription(stripe_event=stripe_event)
        await self._create_or_update_invoice(
            stripe_event=stripe_event,
            subscription=subscription,
            reject_period_conflicts=False,
        )
        await self.db.flush()

    async def _require_local_subscription(
        self, *, stripe_event: stripe.Event
    ) -> Subscription:
        stripe_invoice_id = Invoice.extract_stripe_invoice_id(stripe_event=stripe_event)
        stripe_subscription_id = Invoice.extract_stripe_subscription_id(
            stripe_event=stripe_event
        )
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
        return subscription

    async def _create_or_update_invoice(
        self,
        *,
        stripe_event: stripe.Event,
        subscription: Subscription,
        reject_period_conflicts: bool,
    ) -> Invoice:
        stripe_invoice_id = Invoice.extract_stripe_invoice_id(stripe_event=stripe_event)
        period_start, period_end = Invoice.extract_service_period(
            stripe_event=stripe_event
        )

        conflicting_invoice = await self.repository.get_invoice_for_subscription_period(
            subscription_id=subscription.id,
            period_start=period_start,
            period_end=period_end,
            exclude_stripe_invoice_id=stripe_invoice_id,
        )
        if reject_period_conflicts and conflicting_invoice is not None:
            raise NonRetryableStripeWebhookError(
                "A different invoice already exists for the same billed period"
            )

        existing_invoice = await self.repository.get_invoice_by_stripe_invoice_id(
            stripe_invoice_id
        )
        if existing_invoice is not None:
            existing_invoice.update_from_stripe_event(
                stripe_event=stripe_event,
                subscription_id=subscription.id,
            )
            return existing_invoice

        invoice = Invoice.create(
            user_id=subscription.user_id,
            subscription_id=subscription.id,
            stripe_event=stripe_event,
        )
        self.repository.add_invoice(invoice)
        return invoice
