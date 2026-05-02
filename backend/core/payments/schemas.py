from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StripeCreateCustomerSchema(BaseModel):
    name: str
    email: str


class StripeCustomerResponse(BaseModel):
    model_config = ConfigDict(extra="allow")  # <- keep unknown fields

    id: str
    object: Literal["customer"]
    address: dict[str, Any] | None = None
    customer_account: str | None = None
    description: str | None = None
    email: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    name: str | None = None
    phone: str | None = None
    shipping: dict[str, Any] | None = None
    tax: dict[str, Any] | None = None
    created: int
    currency: str | None = None
    delinquent: bool | None = None
    livemode: bool
    subscriptions: dict[str, Any] | None = None
