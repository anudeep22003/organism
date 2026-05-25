from enum import StrEnum


class BillingErrorCode(StrEnum):
    ENTITLEMENT_REQUIRED = "billing_entitlement_required"
    PLAN_NOT_FOUND = "billing_plan_not_found"
    INVALID_CHECKOUT_REQUEST = "billing_invalid_checkout_request"
    SUBSCRIPTION_ALREADY_EXISTS = "billing_subscription_already_exists"
    STRIPE_WEBHOOK_INVALID = "billing_stripe_webhook_invalid"
    STRIPE_WEBHOOK_FAILED = "billing_stripe_webhook_failed"
    PLAN_CONFIGURATION_ERROR = "billing_plan_configuration_error"


class BillingEntitlementRequiredError(Exception):
    def __init__(self, *, required_feature: str) -> None:
        self.required_feature = required_feature
        super().__init__(f"Missing required entitlement: {required_feature}")
