from fastapi import APIRouter, Depends, HTTPException, Request, Response
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select

from core.auth.schemas import UserSchema, UserSchemaCreate
from core.services.database import get_async_db_session

logger = logger.bind(name=__name__)

from .models import User

router = APIRouter(prefix="/auth", tags=["auth"])


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
        user = User(email=body.email, password=body.password)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return UserSchema.model_validate(user)
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
