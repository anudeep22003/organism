import uuid
from datetime import datetime, timezone
from typing import cast

import stripe
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from stripe import Customer, RequestOptions
from stripe.params import CustomerCreateParams
from stripe.params.checkout import SessionCreateParams

from core.auth.models import User
from core.config import settings
from core.infrastructure.stripe_client import get_stripe_client
from core.payments.models.checkout_session import FulfillmentStatus
from core.payments.webhooks import (
    NonRetryableStripeWebhookError,
    RetryableStripeWebhookError,
    StripeWebhookDispatcher,
)

from .models import (
    CheckoutSession,
    CheckoutSessionMode,
    PaymentIntent,
    StripeCustomer,
    StripeEvent,
    StripeStatus,
)
from .repository import PaymentsRepository


class StripeWebhookValidationError(Exception):
    """Error raised when a stripe webhook event is not valid."""

    pass


class UserNotFoundError(Exception):
    """Error raised when a user is not found."""

    pass


class UnhandledException(Exception):
    """Error raised when an unknown error occurs."""

    pass


class PaymentsService:
    def __init__(self, db: AsyncSession):
        self.stripe_client = get_stripe_client()
        self.db = db
        self.repository = PaymentsRepository(db)

    async def provision_customer(
        self,
        *,
        user_id: uuid.UUID,
    ) -> StripeCustomer:
        # Local lookup is the fast path; Stripe idempotency and metadata are the
        # backup guardrails if a prior external create succeeded but DB persistence did not.
        stripe_customer_model = await self.repository.get_stripe_customer_by_user_id(
            user_id
        )
        if stripe_customer_model is not None:
            logger.info("Stripe customer already exists for user_id: {}", user_id)
            return stripe_customer_model

        user = await self.db.get(User, user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")

        stripe_customer = await self._create_customer_at_stripe(user=user)
        new_stripe_customer = self._create_stripe_customer_model(
            user_id, stripe_customer
        )
        # The dispatcher commits this staged row together with the event status update.
        self.repository.add_stripe_customer(new_stripe_customer)
        logger.info("Prepared stripe customer for user_id: {}", user_id)
        await self.db.flush()
        return new_stripe_customer

    async def user_stripe_customer_id(self, user_id: uuid.UUID) -> str | None:
        stripe_customer = await self.repository.get_stripe_customer_by_user_id(user_id)
        if stripe_customer is None:
            return None
        return stripe_customer.stripe_customer_id

    async def _internal_create_stripe_customer(
        self, *, user_id: uuid.UUID
    ) -> StripeCustomer:
        stripe_customer = await self.provision_customer(user_id=user_id)
        await self.db.commit()  # since the above method only flushes, and depends on event dispatcher to commit
        return stripe_customer

    async def _create_customer_at_stripe(self, *, user: User) -> Customer:
        await self.db.refresh(user)
        params = CustomerCreateParams(
            name=user.name or "No name on google account",
            email=user.email,
            metadata={"internal_user_id": str(user.id)},
        )
        # Stable idempotency lets retries reuse the same Stripe-side create result.
        options = RequestOptions(
            idempotency_key=f"customer:create:{str(user.id)}",
        )
        stripe_customer = await self.stripe_client.v1.customers.create_async(
            params=params,
            options=options,
        )
        logger.info("Stripe customer created: {}", stripe_customer.id)
        return stripe_customer

    def _create_stripe_customer_model(
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
            logger.warning("Stripe customer not found for user_id: {}", user_id)
            stripe_customer = await self._internal_create_stripe_customer(
                user_id=user_id
            )
        await self.db.refresh(stripe_customer)
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
        await self.db.flush()
        await self.db.refresh(checkout_session)

        # create an idempotency key with intent prefixed to avoid key collision
        # stripe cannot accept same indempotency key for all requests
        idempotency_key = f"checkout_session:create:{str(checkout_session.id)}"

        params = SessionCreateParams(
            customer=stripe_customer_id,
            client_reference_id=str(user_id),
            line_items=[{"price": price_id, "quantity": 1}],
            mode=CheckoutSessionMode.SUBSCRIPTION.value,
            # mode=CheckoutSessionMode.PAYMENT.value,
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

    async def handle_stripe_webhook_event(
        self,
        *,
        body: bytes,
        stripe_signature: str,
    ) -> None:
        stripe_event = self._validate_stripe_webhook_body(
            body=body, sig_header=stripe_signature
        )
        logger.info("stripe event received: type: {}", stripe_event.type)

        stripe_event_id = stripe_event.id
        existing_stripe_event = (
            await self.repository.get_stripe_event_by_stripe_event_id(stripe_event_id)
        )
        if (
            existing_stripe_event is not None
            and existing_stripe_event.processed_at is not None
        ):
            logger.info("Stripe event already processed: {}", stripe_event_id)
            return

        if existing_stripe_event is None:
            stripe_event_model = StripeEvent.create(
                stripe_event=stripe_event,
            )
            self.repository.add_stripe_event(stripe_event_model)
            await self.db.commit()
            logger.info("Stripe event committed to db: type: {}", stripe_event.type)

        dispatcher = StripeWebhookDispatcher(self.db)
        try:
            await dispatcher.dispatch(stripe_event)
        except RetryableStripeWebhookError as exc:
            await self.db.rollback()
            await self._mark_stripe_event_failed(stripe_event_id, str(exc))
            raise UnhandledException(
                f"Retryable stripe webhook handling error: {exc}"
            ) from exc
        except NonRetryableStripeWebhookError as exc:
            await self.db.rollback()
            await self._mark_stripe_event_failed(stripe_event_id, str(exc))
            logger.warning("Non-retryable stripe webhook error: {}", exc)
            return
        except Exception as exc:
            await self.db.rollback()
            await self._mark_stripe_event_failed(
                stripe_event_id, f"Unexpected webhook handling error: {exc}"
            )
            raise UnhandledException(
                f"Unexpected stripe webhook handling error: {exc}"
            ) from exc

        await self._mark_stripe_event_processed(stripe_event_id)

    def _validate_stripe_webhook_body(
        self, body: bytes, sig_header: str
    ) -> "stripe.Event":
        try:
            event = stripe.Webhook.construct_event(
                payload=body,
                sig_header=sig_header,
                secret=settings.stripe_webhook_secret,
            )
            logger.info("Stripe validation passed")
            try:
                # this is in case the event.to_dict fails and takes the entire webhook handling down
                logger.info("[STRIPE_EVENT]: {}", event.to_dict())
            except Exception as e:
                logger.error("Error logging stripe event: {}", e)

            return cast(stripe.Event, event)
        except stripe.error.SignatureVerificationError:
            raise StripeWebhookValidationError("Invalid stripe webhook signature")
        except Exception as e:
            raise UnhandledException(
                f"Unknown error validating stripe webhook body: {e}"
            ) from e

    async def _mark_stripe_event_processed(self, stripe_event_id: str) -> None:
        stripe_event = await self.repository.get_stripe_event_by_stripe_event_id(
            stripe_event_id
        )
        if stripe_event is None:
            raise UnhandledException(
                f"Stripe event {stripe_event_id} was not found for processed marking"
            )
        stripe_event.mark_processed()
        await self.db.commit()

    async def _mark_stripe_event_failed(self, stripe_event_id: str, error: str) -> None:
        stripe_event = await self.repository.get_stripe_event_by_stripe_event_id(
            stripe_event_id
        )
        if stripe_event is None:
            raise UnhandledException(
                f"Stripe event {stripe_event_id} was not found for failure marking"
            )
        stripe_event.mark_failed(error=error)
        await self.db.commit()
