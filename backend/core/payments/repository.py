import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import StripeCustomerModel


class PaymentsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_stripe_customer_in_db(
        self, stripe_customer: StripeCustomerModel
    ) -> None:
        self.db.add(stripe_customer)

    async def get_stripe_customer_by_user_id(
        self, user_id: uuid.UUID
    ) -> StripeCustomerModel | None:
        query = select(StripeCustomerModel).where(
            StripeCustomerModel.user_id == user_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
