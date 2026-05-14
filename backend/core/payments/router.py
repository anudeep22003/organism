import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.api import get_current_user_id
from core.common import AliasedBaseModel
from core.infrastructure.database import get_async_db_session

from .service import (
    PaymentsService,
    StripeWebhookValidationError,
    SubscriptionAlreadyExistsError,
    UnhandledException,
)

router = APIRouter(prefix="/billing", tags=["billing"])


class CreateCheckoutSessionRequest(AliasedBaseModel):
    price_ids: list[str]


# Dependencies
def get_payments_service(
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> PaymentsService:
    return PaymentsService(db)


@router.post("/create-checkout-session")
async def create_checkout_session(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[PaymentsService, Depends(get_payments_service)],
) -> dict[str, str]:
    # price_id = "price_1TTLxCAMWKJyocPOBfg70ec9"
    # price_id = "price_1TTLpLAMWKJyocPOzDFvIMFG"
    # price_id = "price_1TVSvzAMWKJyocPOhf76pKXx"
    # price_id = "price_1TVTLYAMWKJyocPOEzUSFEIT"
    price_id = "price_1TVTbWAMWKJyocPO4ayR6keZ"
    try:
        url = await service.create_checkout_session(
            user_id=user_id,
            price_id=price_id,
        )
    except SubscriptionAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"url": url}


@router.post("/stripe/webhook")
async def webhook(
    request: Request,
    stripe_signature: Annotated[str, Header(alias="stripe-signature")],
    service: Annotated[PaymentsService, Depends(get_payments_service)],
) -> dict[str, str]:
    # verify signature on raw body, do not parse yet
    # parsing shifts whitespaces and breaks signature verification
    body = await request.body()
    try:
        await service.handle_stripe_webhook_event(
            body=body, stripe_signature=stripe_signature
        )
    except StripeWebhookValidationError as e:
        logger.warning("Stripe webhook validation error: {}", e)
        raise HTTPException(status_code=400, detail="invalid stripe webhook signature")
    except UnhandledException as e:
        logger.error("Unhandled error handling stripe webhook: {}", e)
        raise HTTPException(
            status_code=500, detail=f"Unhandled error handling stripe webhook: {e}"
        )
    return {"message": "Webhook received"}
