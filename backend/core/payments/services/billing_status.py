import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from core.payments.models import Entitlement, Plan, Subscription
from core.payments.models.subscription import StripeSubscriptionStatus
from core.payments.repository import PaymentsRepository
from core.payments.schemas import (
    BillingEntitlementSummary,
    BillingMeResponse,
    BillingRecommendedAction,
    BillingSubscriptionStatus,
    BillingSubscriptionSummary,
)


class BillingStatusService:
    def __init__(self, db: AsyncSession) -> None:
        self.repository = PaymentsRepository(db)

    async def get_billing_status(self, *, user_id: uuid.UUID) -> BillingMeResponse:
        now = datetime.now(timezone.utc)
        stripe_customer = await self.repository.get_stripe_customer_by_user_id(user_id)
        active_entitlements = await self.repository.list_current_entitlements(
            user_id=user_id,
            now=now,
        )
        subscription = await self.repository.get_most_relevant_subscription_by_user_id(
            user_id
        )
        plan = None
        if subscription is not None:
            plan = await self.repository.get_plan_by_stripe_price_id(
                subscription.price_id
            )

        has_active_entitlement = len(active_entitlements) > 0
        recommendation = self._billing_status_recommendation(
            subscription=subscription,
            has_active_entitlement=has_active_entitlement,
        )
        return BillingMeResponse(
            has_stripe_customer=stripe_customer is not None,
            has_active_entitlement=has_active_entitlement,
            active_entitlements=[
                self._to_billing_entitlement_summary(entitlement=entitlement)
                for entitlement in active_entitlements
            ],
            subscription=self._to_billing_subscription_summary(
                subscription=subscription,
                plan=plan,
            ),
            can_start_checkout=recommendation
            in {
                BillingRecommendedAction.SUBSCRIBE,
                BillingRecommendedAction.RESUBSCRIBE,
            },
            recommended_action=recommendation,
        )

    def _to_billing_entitlement_summary(
        self, *, entitlement: Entitlement
    ) -> BillingEntitlementSummary:
        return BillingEntitlementSummary(
            feature=entitlement.feature,
            valid_until=entitlement.valid_until,
        )

    def _to_billing_subscription_summary(
        self,
        *,
        subscription: Subscription | None,
        plan: Plan | None,
    ) -> BillingSubscriptionSummary | None:
        if subscription is None:
            return None

        status = BillingSubscriptionStatus(subscription.status)
        renews_on = None
        if (
            status
            in {BillingSubscriptionStatus.ACTIVE, BillingSubscriptionStatus.TRIALING}
            and not subscription.cancel_at_period_end
        ):
            renews_on = subscription.current_period_end

        valid_until = None
        if status in {
            BillingSubscriptionStatus.ACTIVE,
            BillingSubscriptionStatus.TRIALING,
        }:
            valid_until = subscription.current_period_end

        return BillingSubscriptionSummary(
            status=status,
            plan_id=plan.plan_id if plan is not None else None,
            plan_name=plan.display_name if plan is not None else None,
            current_period_end=subscription.current_period_end,
            renews_on=renews_on,
            valid_until=valid_until,
            trial_ends_at=subscription.trial_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
        )

    def _billing_status_recommendation(
        self,
        *,
        subscription: Subscription | None,
        has_active_entitlement: bool,
    ) -> BillingRecommendedAction:
        """Recommend billing UI action from separate billing and access truth.

        Billing truth:
        none -> checkout -> incomplete -> active/trialing
        incomplete -> incomplete_expired
        trialing -> active | past_due | canceled
        active -> active | past_due | active(cancel_at_period_end=true)
        active(cancel_at_period_end=true) -> canceled after period end
        past_due -> active | unpaid | canceled
        unpaid/paused -> portal recovery or no access
        canceled -> checkout -> active/trialing

        Access truth:
        local active entitlement at request time is the source of app access.
        Subscription status explains billing state, not whether paid actions are allowed.
        """
        if subscription is None:
            if has_active_entitlement:
                return BillingRecommendedAction.NONE
            return BillingRecommendedAction.SUBSCRIBE

        status = subscription.status
        if status in {
            StripeSubscriptionStatus.PAST_DUE.value,
            StripeSubscriptionStatus.UNPAID.value,
            StripeSubscriptionStatus.PAUSED.value,
        }:
            return BillingRecommendedAction.PAYMENT_FAILED

        if status == StripeSubscriptionStatus.TRIALING.value and has_active_entitlement:
            return BillingRecommendedAction.TRIAL_ACTIVE

        if status == StripeSubscriptionStatus.ACTIVE.value and has_active_entitlement:
            return BillingRecommendedAction.MANAGE_SUBSCRIPTION

        if (
            status
            in {
                StripeSubscriptionStatus.CANCELED.value,
                StripeSubscriptionStatus.INCOMPLETE_EXPIRED.value,
            }
            and not has_active_entitlement
        ):
            return BillingRecommendedAction.RESUBSCRIBE

        if (
            status
            in {
                StripeSubscriptionStatus.ACTIVE.value,
                StripeSubscriptionStatus.TRIALING.value,
            }
            and not has_active_entitlement
        ):
            return BillingRecommendedAction.MANAGE_SUBSCRIPTION

        if has_active_entitlement:
            return BillingRecommendedAction.NONE
        return BillingRecommendedAction.SUBSCRIBE
