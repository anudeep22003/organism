from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import DATABASE_URL

async_db_engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(bind=async_db_engine)


class ORMBase(DeclarativeBase):
    pass


async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    try:
        async with async_session_maker() as session:
            yield session
    finally:
        await session.close()
