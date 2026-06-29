from core.common import AliasedBaseModel
from core.payments.exceptions import BillingErrorCode


class BillingErrorDetail(AliasedBaseModel):
    code: BillingErrorCode
    message: str


class BillingEntitlementRequiredResponse(AliasedBaseModel):
    code: BillingErrorCode = BillingErrorCode.ENTITLEMENT_REQUIRED
    required_feature: str
