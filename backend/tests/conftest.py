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

Teardown: only the `user` fixture issues an explicit DELETE. All downstream
rows (project, story, character, image, session, edit_event) are removed
automatically via ON DELETE CASCADE defined on each FK constraint.
"""

import os
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Awaitable, Callable

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
os.environ.setdefault(
    "STRIPE_CUSTOMER_PORTAL_URL",
    "https://billing.stripe.com/p/login/test_customer_portal",
)

# These imports must come after load_dotenv — pydantic-settings reads .env.local
# but load_dotenv with override=True above ensures test values take precedence.
from core.auth.config import ACCESS_TOKEN_COOKIE_NAME  # noqa: E402
from core.auth.models.user import User  # noqa: E402
from core.auth.security import AccessTokenManager  # noqa: E402
from core.config import settings  # noqa: E402
from core.payments.models import Entitlement  # noqa: E402
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
    engine = create_async_engine(settings.database_url, echo=False)
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


def make_auth_cookie_header(user_id: uuid.UUID) -> dict[str, str]:
    token = AccessTokenManager().create_access_token(user_id)
    return {"cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}"}


# ---------------------------------------------------------------------------
# Data fixtures — user → project → story → character
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> AsyncGenerator[User, None]:
    """Creates a User row. Deleted via raw SQL after the test.

    All downstream rows (project, story, character, image, session,
    edit_event) are removed automatically via ON DELETE CASCADE.
    """
    u = User(
        email=f"test-{uuid.uuid4()}@example.com",
        password_hash="not-a-real-hash",
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    entitlement = Entitlement(
        user_id=u.id,
        feature="pro_tier",
        source="test_fixture",
        source_id=None,
        valid_from=datetime.now(timezone.utc),
        valid_until=None,
    )
    db_session.add(entitlement)
    await db_session.commit()

    # Snapshot the scalar id before yielding. Some tests expunge ORM state or
    # leave the session rolled back, and teardown must not depend on reading
    # attributes from a detached/expired User instance.
    user_id = u.id
    yield u

    # Teardown uses a fresh engine + session, never the test's db_session.
    # If the test left db_session in an aborted transaction state, the DELETE
    # would silently fail on that connection — leaving the user row (and all
    # its cascaded children) permanently in the DB. A dedicated session is
    # immune to whatever state the test session is in.
    teardown_engine = create_async_engine(settings.database_url, echo=False)
    try:
        async with async_sessionmaker(teardown_engine)() as teardown_session:
            await teardown_session.execute(
                text('DELETE FROM "user" WHERE id = :id'), {"id": user_id}
            )
            await teardown_session.commit()
    finally:
        await teardown_engine.dispose()


@pytest_asyncio.fixture
async def user_factory(
    db_session: AsyncSession,
) -> AsyncGenerator[Callable[..., Awaitable[User]], None]:
    """Create additional test users that clean up reliably after the test.

    Use this when a test needs a second or third actor instead of hand-rolling
    inline user creation and remembering to delete it at the end of the test.
    """

    created_user_ids: list[uuid.UUID] = []

    async def _create_user(
        *,
        email: str | None = None,
        password_hash: str = "not-a-real-hash",
    ) -> User:
        created_user = User(
            email=email or f"test-{uuid.uuid4()}@example.com",
            password_hash=password_hash,
        )
        db_session.add(created_user)
        await db_session.commit()
        await db_session.refresh(created_user)

        db_session.add(
            Entitlement(
                user_id=created_user.id,
                feature="pro_tier",
                source="test_fixture",
                source_id=None,
                valid_from=datetime.now(timezone.utc),
                valid_until=None,
            )
        )
        await db_session.commit()

        created_user_ids.append(created_user.id)
        return created_user

    yield _create_user

    teardown_engine = create_async_engine(settings.database_url, echo=False)
    try:
        async with async_sessionmaker(teardown_engine)() as teardown_session:
            if created_user_ids:
                await teardown_session.execute(
                    text('DELETE FROM "user" WHERE id = ANY(:ids)'),
                    {"ids": created_user_ids},
                )
                await teardown_session.commit()
    finally:
        await teardown_engine.dispose()


@pytest_asyncio.fixture
async def project(
    db_session: AsyncSession, user: User
) -> AsyncGenerator[Project, None]:
    """Creates a Project owned by the test user."""
    p = Project(user_id=user.id)
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)

    yield p

    # No teardown needed — cascades from user delete.


@pytest_asyncio.fixture
async def story(
    db_session: AsyncSession, project: Project
) -> AsyncGenerator[Story, None]:
    """Creates a Story under the test project."""
    s = Story(project_id=project.id, story_text="Once upon a time...")
    db_session.add(s)
    await db_session.commit()
    await db_session.refresh(s)

    yield s

    # No teardown needed — cascades from user delete.


@pytest_asyncio.fixture
async def character(
    db_session: AsyncSession, story: Story
) -> AsyncGenerator[Character, None]:
    """Creates a Character under the test story with realistic attributes."""
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

    # No teardown needed — cascades from user delete.
