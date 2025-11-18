"""FastAPI dependency injection for auth."""

from collections import namedtuple
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.services.database import get_async_db_session

from .exceptions import ExpiredTokenError, InvalidTokenError
from .managers import JWTTokenManager, RefreshTokenManager, SessionManager, UserManager


def get_jwt_token_manager() -> JWTTokenManager:
    """Provide JWT token manager."""
    return JWTTokenManager()


def get_refresh_token_manager() -> RefreshTokenManager:
    """Provide refresh token manager."""
    return RefreshTokenManager()


def get_user_manager(
    db_session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> UserManager:
    """Provide user manager."""
    return UserManager(db_session=db_session)


def get_session_manager(
    db_session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> SessionManager:
    """Provide session manager."""
    return SessionManager(db_session=db_session)


async def get_current_user_id(
    jwt_manager: Annotated[JWTTokenManager, Depends(get_jwt_token_manager)],
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """
    Extract and validate current user from authorization header.

    Args:
        authorization: Authorization header value
        jwt_manager: JWT token manager

    Returns:
        The authenticated user's ID

    Raises:
        HTTPException: If auth fails
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authorization header provided",
        )

    # Extract token from "Bearer <token>"
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    token = parts[1]

    if token == "undefined":  # Frontend bug guard
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    try:
        user_id = jwt_manager.extract_user_id_from_access_token(token)
        return user_id
    except ExpiredTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token expired",
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


# this needs to be the BaseModel and not AliasedBaseModel
# because FastAPI's automated header extraction fails with aliasing
class SessionHeaders(BaseModel):
    host: str
    x_forwarded_for: str | None = None
    user_agent: str | None = None
    x_real_ip: str | None = None


async def get_user_agent_and_ip(
    session_headers: Annotated[SessionHeaders, Header()],
) -> tuple[str | None, str | None]:
    """
    Extract user agent and IP from session headers.

    Args:
        session_headers: Session headers

    Returns:
        User agent and IP
    """
    ip = (
        session_headers.x_forwarded_for
        or session_headers.x_real_ip
        or session_headers.host
    )
    user_agent = session_headers.user_agent
    return user_agent, ip
