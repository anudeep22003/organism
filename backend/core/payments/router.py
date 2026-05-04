import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.api import get_current_user_id
from core.common import AliasedBaseModel
from core.infrastructure.database import get_async_db_session

from .service import PaymentsService

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
    price_id = "price_1TTLxCAMWKJyocPOBfg70ec9"
    url = await service.create_checkout_session(
        user_id=user_id,
        price_id=price_id,
    )
    return {"url": url}
