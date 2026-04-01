"""
Story 90 test gate — PATCH /v2/projects/{project_id} rename a project.

Test invariants:
  1. PATCH with {"name": "New Name"} returns 200 and updated project.
  2. PATCH returns 404 for a project_id that does not exist.
  3. PATCH returns 404 when the project belongs to a different user.
  4. PATCH requires auth (no token → 401).
"""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.managers.jwt import JWTTokenManager
from core.auth.models.user import User
from core.story_engine.models import Project

_jwt = JWTTokenManager()


def _auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    token = _jwt.create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _rename_url(project_id: uuid.UUID) -> str:
    return f"/api/comic-builder/v2/projects/{project_id}"


async def test_rename_project_returns_200_and_updated_name(
    api_client: AsyncClient,
    user: User,
    project: Project,
) -> None:
    """PATCH with a new name returns 200 and the updated project with the new name."""
    response = await api_client.patch(
        _rename_url(project.id),
        headers=_auth_headers(user.id),
        json={"name": "Renamed Project"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Renamed Project"
    assert body["id"] == str(project.id)


async def test_rename_project_persists_name_to_db(
    api_client: AsyncClient,
    user: User,
    project: Project,
    db_session: AsyncSession,
) -> None:
    """After PATCH, the new name is persisted in the DB."""
    new_name = f"DB-Persisted-{uuid.uuid4()}"
    await api_client.patch(
        _rename_url(project.id),
        headers=_auth_headers(user.id),
        json={"name": new_name},
    )

    await db_session.refresh(project)
    assert project.name == new_name


async def test_rename_project_response_matches_project_response_schema(
    api_client: AsyncClient,
    user: User,
    project: Project,
) -> None:
    """The response conforms to ProjectResponseSchema field shape."""
    response = await api_client.patch(
        _rename_url(project.id),
        headers=_auth_headers(user.id),
        json={"name": "Shape Check"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "id" in body
    assert "name" in body
    assert "createdAt" in body
    assert "updatedAt" in body
    assert "state" in body


async def test_rename_project_404_for_nonexistent_project(
    api_client: AsyncClient,
    user: User,
) -> None:
    """PATCH on a project_id that does not exist returns 404."""
    response = await api_client.patch(
        _rename_url(uuid.uuid4()),
        headers=_auth_headers(user.id),
        json={"name": "Ghost Project"},
    )
    assert response.status_code == 404


async def test_rename_project_404_for_other_users_project(
    api_client: AsyncClient,
    db_session: AsyncSession,
    project: Project,
) -> None:
    """PATCH returns 404 when the project belongs to a different user (ownership boundary)."""
    from core.auth.models.user import User as UserModel

    other_user = UserModel(
        email=f"other-rename-{uuid.uuid4()}@example.com", password_hash="x"
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    response = await api_client.patch(
        _rename_url(project.id),
        headers=_auth_headers(other_user.id),
        json={"name": "Stolen Name"},
    )
    assert response.status_code == 404

    from sqlalchemy import text

    await db_session.execute(
        text('DELETE FROM "user" WHERE id = :id'), {"id": other_user.id}
    )
    await db_session.commit()


async def test_rename_project_requires_auth(
    api_client: AsyncClient,
    project: Project,
) -> None:
    """PATCH without a token returns 401."""
    response = await api_client.patch(
        _rename_url(project.id),
        json={"name": "No Auth"},
    )
    assert response.status_code == 401
