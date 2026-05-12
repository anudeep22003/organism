from sqlalchemy.ext.asyncio import AsyncSession

from core.payments.repository import PaymentsRepository


class BaseStripeWebhookHandler:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repository = PaymentsRepository(db)
