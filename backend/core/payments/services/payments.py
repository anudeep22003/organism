import uuid
from datetime import datetime, timezone
from typing import Any, cast
from urllib.parse import urlencode, urljoin

import stripe
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from stripe import Customer, RequestOptions
from stripe.params import CustomerCreateParams, SubscriptionListParams
from stripe.params.checkout import SessionCreateParams

from core.auth.models import User
from core.config import settings
from core.infrastructure.stripe_client import get_stripe_client
from core.payments.models.checkout_session import FulfillmentStatus
from core.payments.webhooks import (
    NonRetryableStripeWebhookError,
    RetryableStripeWebhookError,
    StripeEventDrainer,
    StripeEventProcessor,
)

from ..models import (
    CheckoutSession,
    CheckoutSessionMode,
    PaymentIntent,
    Plan,
    StripeCustomer,
    StripeEvent,
    StripeStatus,
)
from ..repository import PaymentsRepository
from ..schemas import (
    ListPlansResponse,
    PlanFeatureSchema,
    PlanPriceSchema,
    PlanSchemaCustomerFacing,
)


class StripeWebhookValidationError(Exception):
    """Error raised when a stripe webhook event is not valid."""

    pass


class UserNotFoundError(Exception):
    """Error raised when a user is not found."""

    pass


class UnhandledException(Exception):
    """Error raised when an unknown error occurs."""

    pass


class SubscriptionAlreadyExistsError(Exception):
    """Error raised when a user already has a blocking subscription."""

    pass


class PlanNotFoundError(Exception):
    """Error raised when a requested public plan is not active or does not exist."""

    pass


class PlanConfigurationError(Exception):
    """Error raised when an active plan is missing data required for checkout/display."""

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
            user_id,
            livemode=settings.stripe_livemode,
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
        stripe_customer = await self.repository.get_stripe_customer_by_user_id(
            user_id,
            livemode=settings.stripe_livemode,
        )
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
        plan_id: str,
        return_path: str | None = None,
    ) -> str:
        await self._ensure_no_blocking_subscription(user_id=user_id)
        plan = await self.repository.get_active_plan_by_plan_id(plan_id)
        if plan is None:
            raise PlanNotFoundError(f"Plan {plan_id} not found")
        price_id = plan.stripe_price_id

        stripe_customer = await self.repository.get_stripe_customer_by_user_id(
            user_id,
            livemode=settings.stripe_livemode,
        )
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
            mode=CheckoutSessionMode.SUBSCRIPTION,
            stripe_status=StripeStatus.OPEN,
            fulfillment_status=FulfillmentStatus.PENDING,
            livemode=stripe_customer.livemode,
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
            success_url=self._checkout_success_url(return_path=return_path),
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

    def _checkout_success_url(self, *, return_path: str | None) -> str:
        success_path = "/payments/success"
        if return_path is not None:
            if not return_path.startswith("/") or return_path.startswith("//"):
                raise ValueError("return_path must be an app-relative path")
            success_path = f"{success_path}?{urlencode({'returnPath': return_path})}"
        return urljoin(settings.frontend_url, success_path)

    async def _ensure_no_blocking_subscription(self, *, user_id: uuid.UUID) -> None:
        local_subscription = (
            await self.repository.get_blocking_checkout_subscription_by_user_id(user_id)
        )
        if local_subscription is not None:
            logger.info(
                "Blocking checkout for user_id={} due to local subscription {} status={}",
                user_id,
                local_subscription.stripe_subscription_id,
                local_subscription.status,
            )
            raise SubscriptionAlreadyExistsError(
                "User already has an active subscription"
            )

        stripe_customer = await self.repository.get_stripe_customer_by_user_id(
            user_id,
            livemode=settings.stripe_livemode,
        )
        if stripe_customer is None:
            return

        stripe_subscription = await self._get_blocking_stripe_subscription(
            stripe_customer_id=stripe_customer.stripe_customer_id
        )
        if stripe_subscription is None:
            return

        stripe_subscription_id = stripe_subscription.id
        stripe_status = stripe_subscription.status
        logger.warning(
            "Blocking checkout for user_id={} due to Stripe subscription {} status={} missing from local mirror",
            user_id,
            stripe_subscription_id,
            stripe_status,
        )
        raise SubscriptionAlreadyExistsError("User already has an active subscription")

    async def _get_blocking_stripe_subscription(
        self, *, stripe_customer_id: str
    ) -> stripe.Subscription | None:
        params = SubscriptionListParams(
            customer=stripe_customer_id,
            status="all",
            limit=100,
        )
        subscriptions = await self.stripe_client.v1.subscriptions.list_async(
            params=params
        )
        for subscription in subscriptions.data:
            if subscription.status in {
                "active",
                "trialing",
                "past_due",
                "unpaid",
                "paused",
            }:
                return subscription
        return None

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
            and existing_stripe_event.processing_status == "processed"
        ):
            logger.info("Stripe event already processed: {}", stripe_event_id)
            return

        stripe_event_model = existing_stripe_event
        if existing_stripe_event is None:
            stripe_event_model = StripeEvent.create(
                stripe_event=stripe_event,
            )
            self.repository.add_stripe_event(stripe_event_model)
            await self.db.commit()
            logger.info("Stripe event committed to db: type: {}", stripe_event.type)

        if stripe_event_model is None:
            raise UnhandledException(
                f"Stripe event {stripe_event_id} was not available for processing"
            )

        processor = StripeEventProcessor(self.db)
        try:
            stripe_customer_id = stripe_event_model.customer_id
            await processor.process(stripe_event=stripe_event_model)
            await self._drain_retryable_events_for_customer(
                stripe_customer_id=stripe_customer_id
            )
        except RetryableStripeWebhookError as exc:
            raise UnhandledException(
                f"Retryable stripe webhook handling error: {exc}"
            ) from exc
        except NonRetryableStripeWebhookError as exc:
            logger.warning("Non-retryable stripe webhook error: {}", exc)
            return
        except Exception as exc:
            raise UnhandledException(
                f"Unexpected stripe webhook handling error: {exc}"
            ) from exc

    async def _drain_retryable_events_for_customer(
        self, *, stripe_customer_id: str | None
    ) -> None:
        if stripe_customer_id is None:
            return

        summary = await StripeEventDrainer().drain_retryable_for_customer(
            external_stripe_customer_id=stripe_customer_id
        )
        if summary.scanned > 0:
            logger.info(
                "Drained retryable stripe events for customer {}: scanned={} processed={} retryable_failed={} terminal_failed={}",
                stripe_customer_id,
                summary.scanned,
                summary.processed,
                summary.retryable_failed,
                summary.terminal_failed,
            )

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

    async def list_public_plans(self) -> ListPlansResponse:
        plans = await self.repository.list_active_plans()
        return ListPlansResponse(
            plans=[self._to_public_plan_schema(plan=plan) for plan in plans]
        )

    def _to_public_plan_schema(self, *, plan: Plan) -> PlanSchemaCustomerFacing:
        if plan.amount_minor is None or plan.currency is None or plan.interval is None:
            raise PlanConfigurationError(
                f"Active plan {plan.plan_id} is missing public price fields"
            )
        return PlanSchemaCustomerFacing(
            plan_id=plan.plan_id,
            display_name=plan.display_name,
            description=plan.description,
            features=self._to_plan_feature_schemas(features=plan.features),
            price=PlanPriceSchema(
                amount_minor=plan.amount_minor,
                currency=plan.currency,
                interval=plan.interval,
            ),
        )

    def _to_plan_feature_schemas(
        self, *, features: list[dict[str, Any]]
    ) -> list[PlanFeatureSchema]:
        feature_schemas: list[PlanFeatureSchema] = []
        for feature in features:
            label = feature.get("label")
            if not isinstance(label, str):
                raise PlanConfigurationError(
                    "Plan feature entries must include a string label"
                )
            description = feature.get("description")
            if description is not None and not isinstance(description, str):
                raise PlanConfigurationError(
                    "Plan feature description must be a string when provided"
                )
            feature_schemas.append(
                PlanFeatureSchema(label=label, description=description)
            )
        return feature_schemas
