import asyncio
import uuid
from dataclasses import dataclass
from typing import Literal

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.payments.event_handler import PaymentsEventHandler

from .dispatcher import DispatchHandlerMap, EventDispatcher
from .models import Event, EventType
from .repository import EventRepository
from .schemas import EmitEventSchema


@dataclass(frozen=True, slots=True)
class EventCreationStatus:
    status: Literal["succeeded", "failed"]
    error: Exception | None = None


class EventService:
    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session
        self.repository = EventRepository(db_session)
        self.payments_event_handler = PaymentsEventHandler(db_session)
        self.dispatcher = EventDispatcher(
            dispatch_handlers_map=self._dispatch_handler_map(),
            repository=self.repository,
        )

    def _dispatch_handler_map(self) -> DispatchHandlerMap:
        return {
            EventType.USER_CREATED: [self.payments_event_handler.handle],
        }

    async def emit_event(
        self,
        *,
        event_schema: EmitEventSchema,
    ) -> EventCreationStatus:
        event_model = Event.create_pending_event(
            event_type=event_schema.event_type,
            aggregate_type=event_schema.aggregate_type,
            aggregate_id=event_schema.aggregate_id,
            payload=event_schema.payload,
        )
        try:
            event = await self.repository.create_event(event_model)
        except Exception as e:
            return EventCreationStatus(status="failed", error=e)
        try:
            await self.db.commit()
        except Exception as e:
            return EventCreationStatus(status="failed", error=e)

        task = asyncio.create_task(
            self.dispatcher.dispatch_event_for_handling(
                event.id, event_schema.event_type
            )
        )
        task.add_done_callback(lambda _: logger.debug(f"Event handled: {event}"))
        return EventCreationStatus(status="succeeded")

    async def get_event(self, event_id: uuid.UUID) -> Event | None:
        return await self.repository.get_event_by_id(event_id)
