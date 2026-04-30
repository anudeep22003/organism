import uuid
from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Event, EventStatus


class EventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_event_by_id(self, event_id: uuid.UUID) -> Event | None:
        return await self.db.get(Event, event_id)

    async def create_event(self, event: Event) -> Event:
        self.db.add(event)
        return event

    async def list_pending_events(self, *, limit: int = 100) -> Sequence[Event]:
        query: Select[tuple[Event]] = (
            select(Event)
            .where(Event.status == EventStatus.PENDING.value)
            .order_by(Event.created_at.asc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()
