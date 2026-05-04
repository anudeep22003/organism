import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import StripeCustomer


class PaymentsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_stripe_customer_by_user_id(
        self, user_id: uuid.UUID
    ) -> StripeCustomer | None:
        query = select(StripeCustomer).where(StripeCustomer.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def add_stripe_customer(self, stripe_customer: StripeCustomer) -> None:
        self.db.add(stripe_customer)
