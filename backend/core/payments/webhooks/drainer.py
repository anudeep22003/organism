from __future__ import annotations

import uuid
from dataclasses import dataclass

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.infrastructure.database import get_async_session_maker
from core.payments.models import StripeEventProcessingStatus
from core.payments.repository import PaymentsRepository

from .exceptions import NonRetryableStripeWebhookError, RetryableStripeWebhookError
from .processor import StripeEventProcessor


@dataclass(slots=True)
class StripeEventDrainSummary:
    scanned: int = 0
    processed: int = 0
    retryable_failed: int = 0
    terminal_failed: int = 0
    already_processed: int = 0


class StripeEventDrainer:
    """Replay persisted Stripe events that are safe to retry automatically."""

    def __init__(
        self,
        *,
        session_maker: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self.session_maker = session_maker or get_async_session_maker()

    async def drain(self, *, limit: int = 50) -> StripeEventDrainSummary:
        summary = StripeEventDrainSummary()

        async with self.session_maker() as db:
            repository = PaymentsRepository(db)
            drainable_events = await repository.list_drainable_stripe_events(
                limit=limit
            )
            event_ids = [event.id for event in drainable_events]

        summary.scanned = len(event_ids)
        for event_id in event_ids:
            outcome = await self._drain_one(stripe_event_id=event_id)
            if outcome == StripeEventProcessingStatus.PROCESSED.value:
                summary.processed += 1
            elif outcome == StripeEventProcessingStatus.RETRYABLE_FAILED.value:
                summary.retryable_failed += 1
            elif outcome == StripeEventProcessingStatus.TERMINAL_FAILED.value:
                summary.terminal_failed += 1
            else:
                summary.already_processed += 1

        return summary

    async def drain_retryable_for_customer(
        self, *, external_stripe_customer_id: str, limit: int = 50
    ) -> StripeEventDrainSummary:
        summary = StripeEventDrainSummary()
        logger.info(
            f"Draining retryable events for customer {external_stripe_customer_id}"
        )
        async with self.session_maker() as db:
            repository = PaymentsRepository(db)
            drainable_events = (
                await repository.list_retryable_stripe_events_by_customer_id(
                    stripe_customer_id=external_stripe_customer_id,
                    limit=limit,
                )
            )
            logger.info(f"Found {len(drainable_events)} retryable events")
            event_ids = [event.id for event in drainable_events]

        summary.scanned = len(event_ids)
        for event_id in event_ids:
            outcome = await self._drain_one(stripe_event_id=event_id)
            if outcome == StripeEventProcessingStatus.PROCESSED.value:
                summary.processed += 1
            elif outcome == StripeEventProcessingStatus.RETRYABLE_FAILED.value:
                summary.retryable_failed += 1
            elif outcome == StripeEventProcessingStatus.TERMINAL_FAILED.value:
                summary.terminal_failed += 1
            else:
                summary.already_processed += 1
        logger.info("Drain summary: {}", summary)
        return summary

    async def _drain_one(self, *, stripe_event_id: uuid.UUID) -> str:
        async with self.session_maker() as db:
            repository = PaymentsRepository(db)
            stripe_event = await repository.get_stripe_event_by_id(stripe_event_id)
            if stripe_event is None:
                raise ValueError(f"Stripe event {stripe_event_id} not found")
            if (
                stripe_event.processing_status
                == StripeEventProcessingStatus.PROCESSED.value
            ):
                return StripeEventProcessingStatus.PROCESSED.value

            processor = StripeEventProcessor(db)
            try:
                await processor.process(stripe_event=stripe_event)
            except (
                RetryableStripeWebhookError,
                NonRetryableStripeWebhookError,
                Exception,
            ):
                pass

            refreshed_event = await repository.get_stripe_event_by_id(stripe_event_id)
            if refreshed_event is None:
                raise ValueError(
                    f"Stripe event {stripe_event_id} not found after replay"
                )
            return refreshed_event.processing_status
