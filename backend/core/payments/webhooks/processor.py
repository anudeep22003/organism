from __future__ import annotations

import uuid

import stripe
from sqlalchemy.ext.asyncio import AsyncSession

from core.payments.models import StripeEvent, StripeEventProcessingStatus
from core.payments.repository import PaymentsRepository

from .dispatcher import StripeWebhookDispatcher
from .exceptions import NonRetryableStripeWebhookError, RetryableStripeWebhookError


class StripeEventProcessor:
    """Process one persisted Stripe event and persist its terminal state.

    This is shared by the live webhook request path and the manual drainer so
    both code paths use the same replay and failure semantics.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repository = PaymentsRepository(db)
        self.dispatcher = StripeWebhookDispatcher(db)

    async def process(self, *, stripe_event: StripeEvent) -> bool:
        if (
            stripe_event.processing_status
            == StripeEventProcessingStatus.PROCESSED.value
        ):
            return False

        event_id = stripe_event.id
        reconstructed_event = self._reconstruct_event(stripe_event=stripe_event)
        try:
            stripe_event.mark_processing_attempt()
            handled = await self.dispatcher.dispatch(reconstructed_event)
            stripe_event.mark_processed()
            await self.db.commit()
            return handled
        except RetryableStripeWebhookError as exc:
            await self.db.rollback()
            await self._mark_retryable_failed(stripe_event_id=event_id, error=str(exc))
            raise
        except NonRetryableStripeWebhookError as exc:
            await self.db.rollback()
            await self._mark_terminal_failed(stripe_event_id=event_id, error=str(exc))
            raise
        except Exception as exc:
            await self.db.rollback()
            await self._mark_retryable_failed(stripe_event_id=event_id, error=str(exc))
            raise

    @staticmethod
    def _reconstruct_event(*, stripe_event: StripeEvent) -> stripe.Event:
        # if you set the key to actual stripe key, the events become live, you can do api calls from the event
        # however, we are not using this, hence key is None
        return stripe.Event.construct_from(stripe_event.payload, key=None)

    async def _mark_retryable_failed(
        self, *, stripe_event_id: uuid.UUID, error: str
    ) -> None:
        stripe_event = await self.repository.get_stripe_event_by_id(stripe_event_id)
        if stripe_event is None:
            raise ValueError(f"Stripe event {stripe_event_id} not found")
        stripe_event.mark_processing_attempt()
        stripe_event.mark_retryable_failed(error=error)
        await self.db.commit()

    async def _mark_terminal_failed(
        self, *, stripe_event_id: uuid.UUID, error: str
    ) -> None:
        stripe_event = await self.repository.get_stripe_event_by_id(stripe_event_id)
        if stripe_event is None:
            raise ValueError(f"Stripe event {stripe_event_id} not found")
        stripe_event.mark_processing_attempt()
        stripe_event.mark_terminal_failed(error=error)
        await self.db.commit()
