from core.common import AliasedBaseModel


class CreateCheckoutSessionRequest(AliasedBaseModel):
    plan_id: str
    return_path: str | None = None


class CreateCheckoutSessionResponse(AliasedBaseModel):
    checkout_url: str
