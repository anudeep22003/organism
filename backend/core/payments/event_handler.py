from sqlalchemy.ext.asyncio import AsyncSession

from .service import PaymentsService


class PaymentsEventHandler:
    def __init__(self, db: AsyncSession) -> None:
        self.payments_service = PaymentsService(db)

    async def handle(self, payload: dict[str, str | None]) -> None:
        await self.payments_service.handle_create_customer(payload)
