from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import EmitEventSchema
from .service import EventService


async def emit_event(*, event: EmitEventSchema, db_session: AsyncSession) -> None:
    event_service = EventService(db_session=db_session)
    await event_service.emit_event(event_schema=event)
