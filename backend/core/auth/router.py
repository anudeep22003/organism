import uuid
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from loguru import logger
from passlib.context import CryptContext  # type: ignore[import-untyped]
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.services.database import get_async_db_session
from core.sockets.types.envelope import AliasedBaseModel
from core.universe.events import get_current_timestamp

from .exceptions import (
    InvalidCredentialsError,
    InvalidTokenError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from .manager import REFRESH_TOKEN_TTL, AuthManager, JWTTokensManager, SessionManager
from .models.user import User
from .schemas.user import UserResponse, UserSchemaCreate, UserSchemaSignin

logger = logger.bind(name=__name__)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

router = APIRouter(prefix="/auth", tags=["auth"])

SAFE_HEADERS_TO_STORE = {
    "user-agent",
    "referer",
    "accept-language",
    "sec-ch-ua",  # The browser's brand and version information in a structured format.
    "sec-ch-ua-mobile",  # Whether the browser is running on a mobile device.
    "sec-ch-ua-platform",  # The platform the browser is running on.
}


def get_safe_headers(request: Request) -> dict:
    """Extract only safe, non-sensitive headers from the request."""
    return {
        key: request.headers.get(key)
        for key in SAFE_HEADERS_TO_STORE
        if request.headers.get(key) is not None
    }


class LoginResponse(AliasedBaseModel):
    user: UserResponse
    access_token: str


@router.post("/signin", response_model=LoginResponse)
async def login(
    response: Response,
    request: Request,
    credentials: UserSchemaSignin,
    async_db_session: AsyncSession = Depends(get_async_db_session),
) -> LoginResponse:
    try:
        auth_manager = AuthManager(async_db_session=async_db_session)
        user = await auth_manager.authenticate_user(credentials=credentials)
        jwt_manager = JWTTokensManager()
        access_token = jwt_manager.create_access_token(str(user.id))
        return LoginResponse(
            user=UserResponse.model_validate(user), access_token=access_token
        )
    except (UserNotFoundError, InvalidCredentialsError):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    except Exception as e:
        logger.error(f"Error signing in user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")


@router.post("/signup", response_model=LoginResponse)
async def signup(
    response: Response,
    request: Request,
    body: UserSchemaCreate,
    async_db_session: AsyncSession = Depends(get_async_db_session),
) -> LoginResponse:
    try:
        auth_manager = AuthManager(async_db_session=async_db_session)
        new_user = await auth_manager.create_new_user(credentials=body, request=request)
        user_response = UserResponse.model_validate(
            new_user
        )  # have to do this here before session context is lost and greenlet errors show up
        session_manager = SessionManager(async_db_session=async_db_session)
        jwt_manager = JWTTokensManager()
        access_token = jwt_manager.create_access_token(str(user_response.id))
        refresh_token = jwt_manager.create_refresh_token()
        session = await session_manager.create_session(
            user_id=new_user.id, refresh_token=refresh_token
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            # TODO this is on the manager page as a constant. Needs to be fixed.
            max_age=REFRESH_TOKEN_TTL,
            path="/",
        )
        return LoginResponse(
            user=user_response, status_code="SUCCESS", access_token=access_token
        )
    except UserAlreadyExistsError as e:
        logger.error(f"User already exists: {e}")
        return LoginResponse(status_code="USER_ALREADY_EXISTS")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return LoginResponse(status_code="INTERNAL_ERROR")


@router.post("/refresh")
async def refresh(
    response: Response,
    request: Request,
    async_db_session: AsyncSession = Depends(get_async_db_session),
    refresh_token: Optional[str] = Cookie(None),
) -> LoginResponse:
    try:
        logger.debug("Refresh token", refresh_token=refresh_token)
        if refresh_token is None:
            raise HTTPException(
                status_code=401,
                detail="Unauthorized, no refresh token provided in cookies.",
            )
        access_token = request.headers.get("Authorization")
        logger.debug("Access token from headers", access_token=access_token)
        if access_token is None:
            raise HTTPException(
                status_code=401,
                detail="Unauthorized, no access token provided in headers.",
            )
        access_token = access_token.split(" ")[1]

        if access_token == "undefined":
            raise HTTPException(
                status_code=401,
                detail="Unauthorized, access token is undefined.",
            )

        jwt_manager = JWTTokensManager()
        decoded = jwt_manager.decode_token(access_token)
        user_id = decoded.get("sub")
        expires_at = decoded.get("exp")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Unauthorized, no user id found in access token.",
            )

        # ensure user exists
        user = await async_db_session.scalar(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        if user is None:
            raise HTTPException(status_code=401, detail="Unauthorized")

        user_response = UserResponse.model_validate(user)

        if expires_at is None or expires_at < get_current_timestamp():
            session_manager = SessionManager(async_db_session=async_db_session)
            session = await session_manager.find_session_by_user_id(user_id)
            if session is None:
                raise HTTPException(
                    status_code=401,
                    detail="Unauthorized, no session found for user id.",
                )
            if not jwt_manager.verify_refresh_token(
                refresh_token=refresh_token,
                hashed_refresh_token=session.refresh_token_hash,
            ):
                raise HTTPException(
                    status_code=401,
                    detail="Unauthorized, refresh token does not match.",
                )
            new_access_token = jwt_manager.create_access_token(user_id=user_id)
            return LoginResponse(
                user=user_response, status_code="SUCCESS", access_token=new_access_token
            )

        # access token is still valid
        return LoginResponse(
            user=user_response, status_code="SUCCESS", access_token=access_token
        )
    except InvalidTokenError as e:
        logger.error("Error refreshing token:", error=e)
        raise HTTPException(
            status_code=401, detail="Unauthorized, invalid access token."
        )
    except Exception as e:
        logger.error("Error refreshing token:", error=e)
        return LoginResponse(status_code="INTERNAL_ERROR")


@router.get("/me")
async def me(request: Response) -> LoginResponse:
    access_token = request.headers.get("Authorization")
    if access_token is None:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized, no access token provided in headers.",
        )
    access_token = access_token.split(" ")[1]
    if access_token == "undefined":
        raise HTTPException(
            status_code=401,
            detail="Unauthorized, access token is undefined.",
        )
    return LoginResponse(status_code="SUCCESS")
