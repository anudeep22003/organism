import os
from functools import lru_cache
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@lru_cache(maxsize=1)
def _get_session_maker() -> "async_sessionmaker[AsyncSession]":
    """Create the SQLAlchemy async engine and session factory — once, on first call.

    @lru_cache(maxsize=1) means this function body executes exactly once regardless
    of how many times it is called. The same session_maker is returned on every
    subsequent call with no re-instantiation.

    Reads DATABASE_URL from os.environ at call time (not at import time).
    This keeps module import side-effect free — importing this module does not
    trigger core.config imports, which means alembic can safely import app models
    (which transitively import this module) without needing API keys.
    """
    database_url = os.environ["DATABASE_URL"]
    engine = create_async_engine(database_url, echo=False)
    return async_sessionmaker(bind=engine)


async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session for the duration of a request.

    Usage in route handlers (unchanged from before):
        db: Annotated[AsyncSession, Depends(get_async_db_session)]

    The session is created from the lazily-initialised session_maker. The engine
    is opened on the very first request that touches the database, not at startup.
    """
    async with _get_session_maker()() as session:
        yield session
