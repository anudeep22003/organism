from functools import lru_cache
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import settings


@lru_cache(maxsize=1)
def _get_session_maker() -> "async_sessionmaker[AsyncSession]":
    """Create the SQLAlchemy async engine and session factory — once, on first call.

    @lru_cache(maxsize=1) means this function body executes exactly once regardless
    of how many times it is called. The same session_maker is returned on every
    subsequent call with no re-instantiation.

    Lazy creation (not at module import time) is critical because:
    - alembic/env.py imports app models which transitively import this module.
      If the engine were created at import time, importing any model would
      immediately open a DB connection — even in contexts where no DB is needed.
    - Tests can import modules freely without needing a live DB available.
    """
    engine = create_async_engine(settings.database_url, echo=False)
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
