import stripe
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from .handlers import InvoiceWebhookHandler, SubscriptionWebhookHandler


class StripeWebhookDispatcher:
    """Route one persisted Stripe event to the matching domain handler.

    Flow:
    - Look at the Stripe event type.
    - Ignore the event if this app does not handle that type yet.
    - Instantiate the matching domain handler with the current database session.
    - Call the event-specific method for that Stripe lifecycle transition.
    - Let the handler apply the business rules and local writes for that domain.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def dispatch(self, stripe_event: stripe.Event) -> bool:
        # The dispatcher only routes supported Stripe event types; all domain
        # validation, idempotency, and state transitions live in the handlers.
        route = self._handler_for_event_type(stripe_event.type)
        if route is None:
            logger.info("Ignoring unsupported stripe event type: {}", stripe_event.type)
            return False
        handler_class, method_name = route
        handler = handler_class(self.db)
        # idiomatic way to look up the class's dict and walk up the mro to find any ancestor defining the method
        event_handler = getattr(handler, method_name)
        await event_handler(stripe_event)
        return True

    @staticmethod
    def _handler_for_event_type(
        event_type: str,
    ) -> (
        tuple[
            type[SubscriptionWebhookHandler | InvoiceWebhookHandler],
            str,
        ]
        | None
    ):
        match event_type:
            case "customer.subscription.created":
                return (SubscriptionWebhookHandler, "handle_created")
            case "customer.subscription.updated":
                return (SubscriptionWebhookHandler, "handle_updated")
            case "customer.subscription.deleted":
                return (SubscriptionWebhookHandler, "handle_deleted")
            case "invoice.paid":
                return (InvoiceWebhookHandler, "handle_paid")
            case "invoice.payment_failed":
                return (InvoiceWebhookHandler, "handle_payment_failed")
            case _:
                return None
