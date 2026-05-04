import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from .models import Event


class EventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_event_by_id(self, event_id: uuid.UUID) -> Event | None:
        return await self.db.get(Event, event_id)

    def add(self, event: Event) -> None:
        self.db.add(event)

    def mark_completed(self, event: Event, *, handled_at: datetime) -> None:
        event.mark_completed(handled_at=handled_at)

    def mark_failed(self, event: Event, *, handled_at: datetime, error: str) -> None:
        event.mark_failed(handled_at=handled_at, error=error)
