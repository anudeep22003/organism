import asyncio
import uuid
from dataclasses import dataclass
from typing import Literal

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Event
from .repository import EventRepository
from .schemas import EmitEventSchema


async def handle_event(event: Event) -> None:
    logger.debug("Started handling event")
    await asyncio.sleep(1)  # simulate processing time


@dataclass(frozen=True, slots=True)
class EventCreationStatus:
    status: Literal["succeeded", "failed"]
    error: Exception | None = None


class EventService:
    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session
        self.repository = EventRepository(db_session)

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

        task = asyncio.create_task(handle_event(event))
        task.add_done_callback(lambda _: logger.debug(f"Event handled: {event}"))
        return EventCreationStatus(status="succeeded")

    async def get_event(self, event_id: uuid.UUID) -> Event | None:
        return await self.repository.get_event_by_id(event_id)
