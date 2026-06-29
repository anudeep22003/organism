from core.common import AliasedBaseModel


class PlanFeatureSchema(AliasedBaseModel):
    label: str
    description: str | None = None


class PlanPriceSchema(AliasedBaseModel):
    amount_minor: int
    currency: str
    interval: str


class PlanSchemaCustomerFacing(AliasedBaseModel):
    plan_id: str
    display_name: str
    description: str | None = None
    features: list[PlanFeatureSchema]
    price: PlanPriceSchema
    # is_recommended: bool = False


class ListPlansResponse(AliasedBaseModel):
    plans: list[PlanSchemaCustomerFacing]


class PlanSchemaAdmin(PlanSchemaCustomerFacing):
    stripe_price_id: str
    entitlement_feature: str
