from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.services.database import get_async_db_session

from ..service import AuthService


async def get_auth_service(
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> AuthService:
    return AuthService(db_session=db)
