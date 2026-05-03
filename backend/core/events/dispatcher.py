import uuid
from datetime import datetime
from typing import Awaitable, Callable

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.infrastructure.database import get_async_session_maker

from .models import Event, EventStatus, EventType
from .repository import EventRepository


class EventNotFoundError(Exception):
    """Event not found."""

    pass


DispatchHandler = Callable[[Event], Awaitable[None]]


class EventDispatcher:
    async def dispatch_event_for_handling(
        self, event_id: uuid.UUID, event_type: EventType
    ) -> None:
        async with get_async_session_maker()() as db_session:
            repository = EventRepository(db_session)
            event = await repository.get_event_by_id(event_id)
            if event is None:
                raise EventNotFoundError(f"Event {event_id} not found")

            handlers = self._build_handlers(db_session, event_type)
            claimed_at = datetime.now(event.created_at.tzinfo)

            try:
                for handler in handlers:
                    await handler(event)
            except Exception as exc:
                logger.exception(f"Failed to handle event {event_id}")
                await repository.update_event(
                    event,
                    status=EventStatus.FAILED,
                    claimed_at=claimed_at,
                    processed_at=datetime.now(event.created_at.tzinfo),
                    failed_at=datetime.now(event.created_at.tzinfo),
                    last_error=str(exc),
                )
            else:
                await repository.update_event(
                    event,
                    status=EventStatus.COMPLETED,
                    claimed_at=claimed_at,
                    processed_at=datetime.now(event.created_at.tzinfo),
                    failed_at=None,
                    last_error=None,
                )

            await db_session.commit()

    def _build_handlers(
        self, db_session: AsyncSession, event_type: EventType
    ) -> list[DispatchHandler]:
        from core.payments.event_handler import PaymentsEventHandler

        if event_type == EventType.USER_CREATED:
            return [PaymentsEventHandler(db_session).handle]

        raise ValueError(f"No handlers configured for event type {event_type}")
