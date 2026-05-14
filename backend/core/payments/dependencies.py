import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.api import get_current_user_id
from core.common import get_current_datetime_utc
from core.infrastructure.database import get_async_db_session

from .repository import PaymentsRepository


def require_entitlement(feature: str) -> Callable[..., Awaitable[None]]:
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required entitlement: {feature}",
            )

    return dependency
