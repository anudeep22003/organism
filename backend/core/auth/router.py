from fastapi import APIRouter, Depends, HTTPException, Request, Response
from loguru import logger
from passlib.context import CryptContext  # type: ignore[import-untyped]
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select

from core.services.database import get_async_db_session

from .models import User
from .schemas import UserSchema, UserSchemaCreate

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


@router.post("/login2", response_model=UserSchema)
async def login(
    response: Response,
    request: Request,
    body: UserSchemaCreate,
    session: AsyncSession = Depends(get_async_db_session),
) -> UserSchema:
    select_user = select(User).where(User.email == body.email)
    user = await session.scalar(select_user)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return UserSchema.model_validate(user)


@router.post("/login", response_model=UserSchema)
async def register(
    response: Response,
    request: Request,
    body: UserSchemaCreate,
    session: AsyncSession = Depends(get_async_db_session),
) -> UserSchema:
    try:
        password_hash = pwd_context.hash(body.password)
        metadata = dict(request.headers)
        user = User(email=body.email, password_hash=password_hash, meta=metadata)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return UserSchema.model_validate(user)
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
