from core.infrastructure.database import get_async_session_maker

from .schemas import EmitEventSchema
from .service import EventService


async def emit_event(*, event: EmitEventSchema) -> None:
    async with get_async_session_maker()() as db_session:
        event_service = EventService(db_session=db_session)
        await event_service.emit_event(event_schema=event)
