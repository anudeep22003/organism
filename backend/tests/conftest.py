"""
Shared pytest fixtures for all tests.

Fixture chain (mirrors FK chain in the DB):
    db_session
        └── user
              └── project
                    └── story
                          └── character

Any test that needs a character just declares `character` as a parameter —
pytest builds the full chain automatically.

Teardown uses raw SQL DELETE (not ORM delete) to avoid SQLAlchemy identity
map issues when the session is shared across fixtures and a test may have
already deleted a row (e.g. the DELETE endpoint test).
"""

import os
import uuid
from collections.abc import AsyncGenerator

import pytest_asyncio
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Load .env.local before any core imports — config.py raises on import
# if the required env vars are not present.
load_dotenv(
    dotenv_path=os.path.join(os.path.dirname(__file__), "../.env.local"), override=True
)

# These imports must come after load_dotenv
from core.auth.models.user import User  # noqa: E402
from core.config import DATABASE_URL  # noqa: E402
from core.story_engine.models import Character, Project, Story  # noqa: E402
from main import fastapi_app  # noqa: E402

# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """A real AsyncSession connected to the local Postgres instance.

    Uses the same DATABASE_URL as the running app (from .env.local).
    Each test gets its own session and engine; cleaned up after the test.
    """
    engine = create_async_engine(DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        yield session

    await engine.dispose()


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    """An httpx AsyncClient wired directly to the real FastAPI app.

    No network socket — requests are handled in-process.
    The full router chain (/api/comic-builder/v2/...) is already mounted.
    """
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
    ) as client:
        yield client


# ---------------------------------------------------------------------------
# Data fixtures — user → project → story → character
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> AsyncGenerator[User, None]:
    """Creates a User row. Deleted via raw SQL after the test."""
    u = User(
        email=f"test-{uuid.uuid4()}@example.com",  # unique per test run
        password_hash="not-a-real-hash",
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    yield u

    # Raw SQL: bypasses the ORM identity map and avoids FK teardown ordering
    # issues. The project fixture deletes its row first (LIFO teardown order),
    # so by the time we reach here the user row has no referencing project rows.
    await db_session.execute(text('DELETE FROM "user" WHERE id = :id'), {"id": u.id})
    await db_session.commit()


@pytest_asyncio.fixture
async def project(
    db_session: AsyncSession, user: User
) -> AsyncGenerator[Project, None]:
    """Creates a Project owned by the test user. Deleted after the test."""
    p = Project(user_id=user.id)
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)

    yield p

    await db_session.execute(text("DELETE FROM project WHERE id = :id"), {"id": p.id})
    await db_session.commit()


@pytest_asyncio.fixture
async def story(
    db_session: AsyncSession, project: Project
) -> AsyncGenerator[Story, None]:
    """Creates a Story under the test project. Deleted after the test."""
    s = Story(project_id=project.id, story_text="Once upon a time...")
    db_session.add(s)
    await db_session.commit()
    await db_session.refresh(s)

    yield s

    await db_session.execute(text("DELETE FROM story WHERE id = :id"), {"id": s.id})
    await db_session.commit()


@pytest_asyncio.fixture
async def character(
    db_session: AsyncSession, story: Story
) -> AsyncGenerator[Character, None]:
    """Creates a Character under the test story with realistic attributes.

    Teardown is a no-op if the character was already deleted by the test
    (e.g. the DELETE endpoint test).
    """
    c = Character(
        story_id=story.id,
        name="Aragorn",
        slug="aragorn",
        attributes={
            "name": "Aragorn",
            "brief": "A ranger of the north and heir to the throne of Gondor.",
            "character_type": "protagonist",
            "era": "Third Age",
            "visual_form": "Tall, weathered ranger in worn travelling clothes",
            "color_palette": ["dark grey", "forest green", "brown"],
            "distinctive_markers": ["Ranger's cloak", "Sword Anduril"],
            "demeanor": "Stoic and resolute",
            "role": "Hero",
        },
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    yield c

    # DELETE ... WHERE id = :id is idempotent — safe even if the test already
    # deleted this row (the DELETE endpoint test does exactly that).
    await db_session.execute(text("DELETE FROM character WHERE id = :id"), {"id": c.id})
    await db_session.commit()
