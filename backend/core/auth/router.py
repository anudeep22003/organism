from typing import Literal

from fastapi import APIRouter, Depends, Request, Response
from loguru import logger
from passlib.context import CryptContext  # type: ignore[import-untyped]
from sqlalchemy.ext.asyncio import AsyncSession

from core.services.database import get_async_db_session
from core.sockets.types.envelope import AliasedBaseModel

from .exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from .manager import AuthManager, SessionManager
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
    user: UserResponse | None = None
    status_code: Literal[
        "SUCCESS",
        "USER_NOT_FOUND",
        "INVALID_CREDENTIALS",
        "USER_ALREADY_EXISTS",
        "INTERNAL_ERROR",
    ]


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
        return LoginResponse(
            user=UserResponse.model_validate(user), status_code="SUCCESS"
        )
    except UserNotFoundError as e:
        logger.error(f"User not found: {e}")
        return LoginResponse(status_code="USER_NOT_FOUND")
    except InvalidCredentialsError as e:
        logger.error(f"Invalid credentials: {e}")
        return LoginResponse(status_code="INVALID_CREDENTIALS")
    except Exception as e:
        logger.error(f"Error signing in user: {e}")
        return LoginResponse(status_code="INTERNAL_ERROR")


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
        session = await session_manager.create_session(user_id=new_user.id)
        return LoginResponse(user=user_response, status_code="SUCCESS")
    except UserAlreadyExistsError as e:
        logger.error(f"User already exists: {e}")
        return LoginResponse(status_code="USER_ALREADY_EXISTS")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return LoginResponse(status_code="INTERNAL_ERROR")
