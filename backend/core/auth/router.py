from fastapi import APIRouter, Depends, HTTPException, Request, Response
from loguru import logger
from passlib.context import CryptContext  # type: ignore[import-untyped]
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select

from core.auth.manager import AuthManager
from core.services.database import get_async_db_session

from .models.user import User
from .schemas.user import UserResponse, UserSchemaCreate, UserSchemaSignin
from .types import LoginResponse

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


@router.post("/signin", response_model=LoginResponse)
async def login(
    response: Response,
    request: Request,
    credentials: UserSchemaSignin,
    session: AsyncSession = Depends(get_async_db_session),
) -> LoginResponse:
    try:
        select_user = select(User).where(User.email == credentials.email)
        user = await session.scalar(select_user)
        if not user:
            return LoginResponse(status_code="USER_NOT_FOUND")
        # verify password
        if not pwd_context.verify(credentials.password, user.password_hash):
            return LoginResponse(status_code="INVALID_CREDENTIALS")
        # update user metadata
        user.meta = get_safe_headers(request)
        await session.commit()
        await session.refresh(user)
        return LoginResponse(
            user=UserResponse.model_validate(user), status_code="SUCCESS"
        )
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
        return await auth_manager.handle_new_user(user_request=body, request=request)
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
