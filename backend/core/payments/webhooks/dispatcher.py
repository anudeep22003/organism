import stripe
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from .handlers import (
    CustomerSubscriptionCreatedHandler,
    CustomerSubscriptionDeletedHandler,
    InvoicePaidHandler,
)


class StripeWebhookDispatcher:
    """Route one persisted Stripe event to the matching domain handler.

    Flow:
    - Look at the Stripe event type.
    - Ignore the event if this app does not handle that type yet.
    - Instantiate the matching handler with the current database session.
    - Let the handler apply the event-specific business rules and writes.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def dispatch(self, stripe_event: stripe.Event) -> bool:
        # The dispatcher only routes supported Stripe event types; all event-specific
        # idempotency and local state checks live inside the individual handlers.
        handler = self._handler_for_event_type(stripe_event.type)
        if handler is None:
            logger.info("Ignoring unsupported stripe event type: {}", stripe_event.type)
            return False
        await handler(self.db).handle(stripe_event)
        return True

    @staticmethod
    def _handler_for_event_type(
        event_type: str,
    ) -> (
        type[
            CustomerSubscriptionCreatedHandler
            | CustomerSubscriptionDeletedHandler
            | InvoicePaidHandler
        ]
        | None
    ):
        match event_type:
            case "customer.subscription.created":
                return CustomerSubscriptionCreatedHandler
            case "customer.subscription.deleted":
                return CustomerSubscriptionDeletedHandler
            case "invoice.paid":
                return InvoicePaidHandler
            case _:
                return None
