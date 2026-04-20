import uuid
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.services.database import get_async_db_session

from ..config import ACCESS_TOKEN_COOKIE_NAME
from ..exceptions import ExpiredAccessTokenError, InvalidAccessTokenError
from ..security import AccessTokenManager, Argon2Hasher, RefreshTokenManager
from ..services import AuthService


def get_access_token_manager() -> AccessTokenManager:
    return AccessTokenManager()


def get_password_hasher() -> Argon2Hasher:
    return Argon2Hasher()


def get_refresh_token_manager() -> RefreshTokenManager:
    return RefreshTokenManager(password_hasher=get_password_hasher())


async def get_auth_service(
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
    access_token_manager: Annotated[
        AccessTokenManager, Depends(get_access_token_manager)
    ],
    refresh_token_manager: Annotated[
        RefreshTokenManager, Depends(get_refresh_token_manager)
    ],
    password_hasher: Annotated[Argon2Hasher, Depends(get_password_hasher)],
) -> AuthService:
    return AuthService(
        db_session=db,
        access_token_manager=access_token_manager,
        refresh_token_manager=refresh_token_manager,
        password_hasher=password_hasher,
    )


async def get_current_user_id(
    access_token_manager: Annotated[
        AccessTokenManager, Depends(get_access_token_manager)
    ],
    access_token: Annotated[str | None, Cookie(alias=ACCESS_TOKEN_COOKIE_NAME)] = None,
) -> uuid.UUID:
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No access token provided",
        )

    try:
        return access_token_manager.extract_user_id(access_token)
    except ExpiredAccessTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token expired",
        )
    except InvalidAccessTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc) or "Invalid access token",
        )


async def get_request_client_context(
    request: Request,
) -> tuple[str | None, str | None]:
    user_agent = request.headers.get("user-agent")
    forwarded_for = request.headers.get("x-forwarded-for")
    real_ip = request.headers.get("x-real-ip")
    ip = forwarded_for or real_ip
    return user_agent, ip
