from loguru import logger
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from stripe import Customer
from stripe.params import CustomerCreateParams

from core.infrastructure.stripe_client import get_stripe_client

from .models import StripeCustomerModel
from .repository import PaymentsRepository


class CreateCustomerPayload(BaseModel):
    user_id: str
    email: str
    name: str | None = None


class EventPayloadMalformedError(Exception):
    """Error validating event payload."""

    pass


class PaymentsService:
    def __init__(self, db: AsyncSession):
        self.stripe_client = get_stripe_client()
        self.payments_repository = PaymentsRepository(db)

    async def handle_create_customer(
        self,
        payload: dict[str, str | None],
    ) -> None:
        try:
            validated_payload = CreateCustomerPayload.model_validate(payload)
        except ValidationError as e:
            logger.error(f"Invalid payload: {e}")
            raise EventPayloadMalformedError(
                f"Invalid payload: {e}, payload: {payload}, error: {e.errors()}"
            ) from e

        user_id, email, name = (
            validated_payload.user_id,
            validated_payload.email,
            validated_payload.name,
        )

        # check if user_id has an attached stripe entry
        stripe_customer_model = (
            await self.payments_repository.get_stripe_customer_by_user_id(user_id)
        )
        if stripe_customer_model is not None:
            logger.info(f"Stripe customer already exists for user_id: {user_id}")
            return

        # create a customer at stripe
        try:
            stripe_customer = await self._create_customer_at_stripe(
                user_id, email, name
            )
        except Exception as e:
            logger.error(f"Error creating customer at stripe: {e}")
            raise

        new_stripe_customer_model = await self._create_stripe_customer_model(
            stripe_customer
        )

        # then persist it to our db
        await self.payments_repository.create_stripe_customer_in_db(
            new_stripe_customer_model
        )
        return

    async def _create_customer_at_stripe(
        self, user_id: str, email: str, name: str | None = None
    ) -> Customer:
        if name:
            params = CustomerCreateParams(name=name, email=email)
        else:
            params = CustomerCreateParams(email=email)
        stripe_customer = await self.stripe_client.v1.customers.create_async(
            params=params
        )
        logger.info(f"Stripe customer created: {stripe_customer}")
        return stripe_customer

    async def _create_stripe_customer_model(
        self, stripe_customer: Customer
    ) -> StripeCustomerModel:
        return StripeCustomerModel(
            stripe_customer_id=stripe_customer.id,
            stripe_object=stripe_customer.object,
            livemode=stripe_customer.livemode,
            raw_stripe_object=stripe_customer.to_dict(),
            stripe_created_at=stripe_customer.created,
        )
