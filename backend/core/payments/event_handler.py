from sqlalchemy.ext.asyncio import AsyncSession

from core.events.models import Event

from .service import PaymentsService


class PaymentsEventHandler:
    def __init__(self, db: AsyncSession) -> None:
        self.payments_service = PaymentsService(db)

    async def handle(self, event: Event) -> None:
        await self.payments_service.handle_create_customer(event.payload)
