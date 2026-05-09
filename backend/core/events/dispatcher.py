import uuid

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.common.utils import get_current_datetime_utc
from core.infrastructure.database import get_async_session_maker
from core.payments.service import PaymentsService

from .models import Event, EventType
from .repository import EventRepository
from .schemas import UserCreatedEventPayload


class EventNotFoundError(Exception):
    """Event not found."""

    pass


class EventDispatcher:
    async def dispatch_event_for_handling(self, event_id: uuid.UUID) -> None:
        async with get_async_session_maker()() as db_session:
            repository = EventRepository(db_session)
            event = await repository.get_event_by_id(event_id)
            if event is None:
                raise EventNotFoundError(f"Event {event_id} not found")

            try:
                # The dispatcher owns the local transaction boundary for handling:
                # domain side effects stage changes, then we persist both business
                # state and event completion together in one commit.
                await self._dispatch_event(db_session=db_session, event=event)
                repository.mark_completed(event, handled_at=get_current_datetime_utc())
                await db_session.commit()
            except Exception as exc:
                logger.exception("Failed to handle event {}", event_id)
                # Roll back any staged local writes before recording failure state.
                await db_session.rollback()

                failed_event = await repository.get_event_by_id(event_id)
                if failed_event is None:
                    raise EventNotFoundError(f"Event {event_id} not found")

                repository.mark_failed(
                    failed_event,
                    handled_at=get_current_datetime_utc(),
                    error=str(exc),
                )
                await db_session.commit()

    async def _dispatch_event(self, *, db_session: AsyncSession, event: Event) -> None:
        if event.event_type == EventType.USER_CREATED:
            payload = UserCreatedEventPayload.model_validate(event.payload)
            await PaymentsService(db_session).provision_customer(
                user_id=payload.user_id
            )
            return

        raise ValueError(f"No handler configured for event type {event.event_type}")
