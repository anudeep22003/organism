from datetime import datetime
from enum import StrEnum

from core.common import AliasedBaseModel


class BillingRecommendedAction(StrEnum):
    SUBSCRIBE = "subscribe"
    RESUBSCRIBE = "resubscribe"
    TRIAL_ACTIVE = "trial_active"
    MANAGE_SUBSCRIPTION = "manage_subscription"
    PAYMENT_FAILED = "payment_failed"
    NONE = "none"


class BillingSubscriptionStatus(StrEnum):
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    PAUSED = "paused"
    CANCELED = "canceled"


class BillingEntitlementSummary(AliasedBaseModel):
    feature: str
    valid_until: datetime | None = None


class BillingSubscriptionSummary(AliasedBaseModel):
    status: BillingSubscriptionStatus
    plan_id: str | None = None
    plan_name: str | None = None
    current_period_end: datetime
    renews_on: datetime | None = None
    valid_until: datetime | None = None
    trial_ends_at: datetime | None = None
    cancel_at_period_end: bool


class BillingMeResponse(AliasedBaseModel):
    has_stripe_customer: bool
    has_active_entitlement: bool
    active_entitlements: list[BillingEntitlementSummary]
    subscription: BillingSubscriptionSummary | None = None
    can_start_checkout: bool
    recommended_action: BillingRecommendedAction
