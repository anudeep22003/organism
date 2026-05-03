from typing import Literal

from pydantic import BaseModel, ConfigDict


class StripeCreateCustomerSchema(BaseModel):
    name: str | None = None
    email: str


class StripeCustomerResponseSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    object: Literal["customer"]
    created: int
    livemode: bool
