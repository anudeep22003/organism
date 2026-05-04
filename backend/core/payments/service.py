import uuid
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from stripe import Customer, RequestOptions
from stripe.params import CustomerCreateParams
from stripe.params.checkout import SessionCreateParams

from core.infrastructure.stripe_client import get_stripe_client
from core.payments.models.checkout_session import FulfillmentStatus

from .models import (
    CheckoutSession,
    CheckoutSessionMode,
    PaymentIntent,
    StripeCustomer,
    StripeStatus,
)
from .repository import PaymentsRepository


class PaymentsService:
    def __init__(self, db: AsyncSession):
        self.stripe_client = get_stripe_client()
        self.db = db
        self.repository = PaymentsRepository(db)

    async def provision_customer(
        self,
        *,
        user_id: uuid.UUID,
        email: str,
        name: str | None,
    ) -> None:
        # Local lookup is the fast path; Stripe idempotency and metadata are the
        # backup guardrails if a prior external create succeeded but DB persistence did not.
        stripe_customer_model = await self.repository.get_stripe_customer_by_user_id(
            user_id
        )
        if stripe_customer_model is not None:
            logger.info("Stripe customer already exists for user_id: {}", user_id)
            return

        stripe_customer = await self._create_customer_at_stripe(
            email=email,
            internal_user_id=user_id,
            name=name,
        )
        new_stripe_customer = self._create_stripe_customer(user_id, stripe_customer)
        # The dispatcher commits this staged row together with the event status update.
        self.repository.add_stripe_customer(new_stripe_customer)
        logger.info("Prepared stripe customer for user_id: {}", user_id)

    async def _create_customer_at_stripe(
        self, *, email: str, internal_user_id: uuid.UUID, name: str | None
    ) -> Customer:
        params = CustomerCreateParams(
            name=name or "No name on google account",
            email=email,
            metadata={"internal_user_id": str(internal_user_id)},
        )
        # Stable idempotency lets retries reuse the same Stripe-side create result.
        options = RequestOptions(
            idempotency_key=str(internal_user_id),
        )
        stripe_customer = await self.stripe_client.v1.customers.create_async(
            params=params,
            options=options,
        )
        logger.info("Stripe customer created: {}", stripe_customer.id)
        return stripe_customer

    def _create_stripe_customer(
        self, user_id: uuid.UUID, stripe_customer: Customer
    ) -> StripeCustomer:
        created_at_datetime = datetime.fromtimestamp(
            stripe_customer.created, timezone.utc
        )
        return StripeCustomer.create(
            user_id=user_id,
            stripe_customer_id=stripe_customer.id,
            livemode=stripe_customer.livemode,
            raw_stripe_object=stripe_customer.to_dict(),
            stripe_created_at=created_at_datetime,
            stripe_object=stripe_customer.object,
        )

    async def create_checkout_session(
        self,
        *,
        user_id: uuid.UUID,
        price_id: str,
    ) -> str:
        stripe_customer = await self.repository.get_stripe_customer_by_user_id(user_id)
        if stripe_customer is None:
            # should we create a customer if one is not found as a failsafe
            raise ValueError("Stripe customer not found")

        stripe_customer_id = stripe_customer.stripe_customer_id
        internal_stripe_customer_record_id = stripe_customer.id

        # first create an entry in our database before calling stripe session create
        checkout_session = CheckoutSession.create_session_entry(
            user_id=user_id,
            stripe_customer_record_id=internal_stripe_customer_record_id,
            stripe_customer_id=stripe_customer_id,
            price_id=price_id,
            intent=PaymentIntent.SUBSCRIPTION_PURCHASE,
            mode=CheckoutSessionMode.PAYMENT,
            stripe_status=StripeStatus.OPEN,
            fulfillment_status=FulfillmentStatus.PENDING,
        )
        self.repository.add_checkout_session(checkout_session)

        # create an idempotency key with intent prefixed to avoid key collision
        # stripe cannot accept same indempotency key for all requests
        idempotency_key = f"checkout_session:create:{str(user_id)}"

        params = SessionCreateParams(
            customer=stripe_customer_id,
            client_reference_id=str(user_id),
            line_items=[{"price": price_id, "quantity": 1}],
            mode=CheckoutSessionMode.PAYMENT.value,
            success_url="http://localhost:5173/payments/success",
        )
        options = RequestOptions(
            idempotency_key=idempotency_key,
        )

        stripe_session = await self.stripe_client.v1.checkout.sessions.create_async(
            params=params,
            options=options,
        )
        logger.info("Stripe session created: {}", stripe_session.id)
        logger.info("[STRIPE_SESSION]: {}", stripe_session.to_dict())

        if stripe_session is None:
            raise ValueError("Stripe session not found")
        if stripe_session.url is None:
            raise ValueError("Stripe session URL not found")

        # update the db entry
        checkout_session.update_session_entry_with_stripe_session(stripe_session)
        await self.db.commit()
        return stripe_session.url
