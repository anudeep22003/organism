from enum import StrEnum


class BillingErrorCode(StrEnum):
    ENTITLEMENT_REQUIRED = "billing_entitlement_required"


class BillingEntitlementRequiredError(Exception):
    def __init__(self, *, required_feature: str) -> None:
        self.required_feature = required_feature
        super().__init__(f"Missing required entitlement: {required_feature}")
