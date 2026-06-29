import asyncio
import uuid

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.infrastructure.database import get_async_session_maker

from .dispatcher import EventDispatcher
from .repository import EventRepository
from .schemas import EmitEventSchema


class EventService:
    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session
        self.repository = EventRepository(db_session)

    async def create_event(
        self,
        *,
        event_schema: EmitEventSchema,
    ) -> uuid.UUID:
        from .models import Event

        event_model = Event.create(
            event_type=event_schema.event_type,
            aggregate_type=event_schema.aggregate_type,
            aggregate_id=event_schema.aggregate_id,
            payload=event_schema.payload,
        )
        # Flush assigns the durable event id before we hand work off to the dispatcher.
        self.repository.add(event_model)
        await self.db.flush()
        return event_model.id


def _log_dispatch_result(event_id: uuid.UUID, task: "asyncio.Task[None]") -> None:
    if task.cancelled():
        logger.warning("Event handling cancelled: {}", event_id)
        return

    exception = task.exception()
    if exception is not None:
        logger.error("Event handling failed for {}: {}", event_id, exception)
        return

    logger.debug("Event handled: {}", event_id)


async def emit_event(*, event: EmitEventSchema) -> None:
    async with get_async_session_maker()() as db_session:
        event_service = EventService(db_session=db_session)
        event_id = await event_service.create_event(event_schema=event)
        await db_session.commit()

    # Dispatch runs after the event row is committed so the handler always starts
    # from durable state, not request-scoped ORM objects.
    dispatcher = EventDispatcher()
    task = asyncio.create_task(dispatcher.dispatch_event_for_handling(event_id))
    task.add_done_callback(lambda task: _log_dispatch_result(event_id, task))
