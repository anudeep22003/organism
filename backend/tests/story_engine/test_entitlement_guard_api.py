import uuid
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.models.user import User
from core.payments.models import Entitlement
from tests.auth_helpers import auth_cookie_header


def _projects_url() -> str:
    return "/api/comic-builder/v2/projects"


async def _create_user_without_entitlement(
    db_session: AsyncSession,
) -> User:
    user = User(
        email=f"entitlement-{uuid.uuid4()}@example.com",
        password_hash="not-a-real-hash",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _delete_user(db_session: AsyncSession, user_id: uuid.UUID) -> None:
    await db_session.execute(text('DELETE FROM "user" WHERE id = :id'), {"id": user_id})
    await db_session.commit()


async def test_story_engine_route_returns_403_without_entitlement(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await _create_user_without_entitlement(db_session)

    try:
        response = await api_client.get(
            _projects_url(),
            headers=auth_cookie_header(user.id),
        )
        assert response.status_code == 403
        assert response.json() == {
            "code": "billing_entitlement_required",
            "requiredFeature": "pro_tier",
        }
    finally:
        await _delete_user(db_session, user.id)


async def test_story_engine_route_returns_403_for_expired_entitlement(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await _create_user_without_entitlement(db_session)
    expired_entitlement = Entitlement(
        user_id=user.id,
        feature="pro_tier",
        source="test_fixture",
        source_id=None,
        valid_from=datetime.now(timezone.utc) - timedelta(days=2),
        valid_until=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add(expired_entitlement)
    await db_session.commit()

    try:
        response = await api_client.get(
            _projects_url(),
            headers=auth_cookie_header(user.id),
        )
        assert response.status_code == 403
        assert response.json() == {
            "code": "billing_entitlement_required",
            "requiredFeature": "pro_tier",
        }
    finally:
        await _delete_user(db_session, user.id)


async def test_story_engine_route_returns_403_for_future_entitlement(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await _create_user_without_entitlement(db_session)
    future_entitlement = Entitlement(
        user_id=user.id,
        feature="pro_tier",
        source="test_fixture",
        source_id=None,
        valid_from=datetime.now(timezone.utc) + timedelta(days=1),
        valid_until=None,
    )
    db_session.add(future_entitlement)
    await db_session.commit()

    try:
        response = await api_client.get(
            _projects_url(),
            headers=auth_cookie_header(user.id),
        )
        assert response.status_code == 403
        assert response.json() == {
            "code": "billing_entitlement_required",
            "requiredFeature": "pro_tier",
        }
    finally:
        await _delete_user(db_session, user.id)
