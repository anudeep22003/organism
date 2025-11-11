from fastapi import APIRouter, Depends, HTTPException, Request, Response
from loguru import logger
from passlib.context import CryptContext  # type: ignore[import-untyped]
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.manager import AuthManager, SessionManager
from core.services.database import get_async_db_session

from .schemas.user import UserSchemaCreate, UserSchemaSignin
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
    async_db_session: AsyncSession = Depends(get_async_db_session),
) -> LoginResponse:
    try:
        auth_manager = AuthManager(async_db_session=async_db_session)
        return await auth_manager.handle_returning_user(credentials=credentials)
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
        login_response = await auth_manager.handle_new_user(
            user_request=body, request=request
        )
        if login_response.status_code == "SUCCESS" and login_response.user is not None:
            session_manager = SessionManager(async_db_session=async_db_session)
            session = await session_manager.create_session(
                user_id=login_response.user.id
            )
            logger.debug("Session created", session=session)
        return login_response
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
