import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.api import get_current_user_id
from core.common import get_current_datetime_utc
from core.infrastructure.database import get_async_db_session

from .exceptions import BillingEntitlementRequiredError
from .repository import PaymentsRepository


def require_entitlement(feature: str) -> Callable[..., Awaitable[None]]:
    """Require a current billing entitlement for a gated route.

    Raises `BillingEntitlementRequiredError` instead of `HTTPException` so the
    global handler in `main.py` can serialize one stable frontend contract:
    `403 {"code": "billing_entitlement_required", "requiredFeature": feature}`.
    """

    async def dependency(
        user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
        db: Annotated[AsyncSession, Depends(get_async_db_session)],
    ) -> None:
        has_entitlement = await PaymentsRepository(db).has_current_entitlement(
            user_id=user_id,
            feature=feature,
            now=get_current_datetime_utc(),
        )
        if not has_entitlement:
            raise BillingEntitlementRequiredError(required_feature=feature)

    return dependency
