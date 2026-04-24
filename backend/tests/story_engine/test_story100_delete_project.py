"""
Story 100 test gate — DELETE /v2/projects/{project_id}.

Test invariants:
  1. DELETE returns 204 with no body.
  2. After deletion, GET /v2/projects/{id} returns 404.
  3. DELETE cascades: stories and characters belonging to the project are gone.
  4. DELETE returns 404 for a project_id that does not exist.
  5. DELETE returns 404 when the project belongs to a different user.
  6. DELETE requires auth.
"""

import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_v2.models.user import User
from core.story_engine.models import Character, Project, Story
from tests.auth_helpers import auth_cookie_header


def _auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    return auth_cookie_header(user_id)


def _project_url(project_id: uuid.UUID) -> str:
    return f"/api/comic-builder/v2/projects/{project_id}"


async def test_delete_project_returns_204(
    api_client: AsyncClient,
    user: User,
    db_session: AsyncSession,
) -> None:
    """DELETE an existing project returns 204 with no body."""
    # Create a project to delete (don't use the shared fixture — we want to
    # delete it without affecting other tests)
    p = Project(user_id=user.id, name="Delete Me")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)

    response = await api_client.delete(
        _project_url(p.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 204
    assert response.content == b""


async def test_delete_project_then_get_returns_404(
    api_client: AsyncClient,
    user: User,
    db_session: AsyncSession,
) -> None:
    """After DELETE, GET on the same project_id returns 404."""
    p = Project(user_id=user.id, name="Gone Soon")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)

    await api_client.delete(_project_url(p.id), headers=_auth_headers(user.id))

    get_response = await api_client.get(
        _project_url(p.id), headers=_auth_headers(user.id)
    )
    assert get_response.status_code == 404


async def test_delete_project_cascades_to_stories_and_characters(
    api_client: AsyncClient,
    user: User,
    db_session: AsyncSession,
) -> None:
    """Deleting a project removes its stories and characters from the DB."""
    p = Project(user_id=user.id, name="Cascade Test")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)

    s = Story(project_id=p.id, story_text="Story to cascade away")
    db_session.add(s)
    await db_session.commit()
    await db_session.refresh(s)

    c = Character(
        story_id=s.id,
        name="Doomed Character",
        slug="doomed-character",
        attributes={"name": "Doomed Character"},
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    project_id = p.id
    story_id = s.id
    character_id = c.id

    # Expunge all so the session doesn't track the deleted objects
    db_session.expunge_all()

    response = await api_client.delete(
        _project_url(project_id), headers=_auth_headers(user.id)
    )
    assert response.status_code == 204

    # Verify story is gone
    story_result = await db_session.execute(
        text("SELECT id FROM story WHERE id = :id"), {"id": story_id}
    )
    assert story_result.fetchone() is None

    # Verify character is gone
    char_result = await db_session.execute(
        text("SELECT id FROM character WHERE id = :id"), {"id": character_id}
    )
    assert char_result.fetchone() is None


async def test_delete_project_404_for_nonexistent_project(
    api_client: AsyncClient,
    user: User,
) -> None:
    """DELETE on a project_id that does not exist returns 404."""
    response = await api_client.delete(
        _project_url(uuid.uuid4()),
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_delete_project_404_for_other_users_project(
    api_client: AsyncClient,
    db_session: AsyncSession,
    project: Project,
) -> None:
    """DELETE returns 404 when the project belongs to a different user."""
    from core.auth_v2.models.user import User as UserModel

    other_user = UserModel(
        email=f"other-delete-{uuid.uuid4()}@example.com", password_hash="x"
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    response = await api_client.delete(
        _project_url(project.id),
        headers=_auth_headers(other_user.id),
    )
    assert response.status_code == 404

    await db_session.execute(
        text('DELETE FROM "user" WHERE id = :id'), {"id": other_user.id}
    )
    await db_session.commit()


async def test_delete_project_requires_auth(
    api_client: AsyncClient,
    project: Project,
) -> None:
    """DELETE without a token returns 401."""
    response = await api_client.delete(_project_url(project.id))
    assert response.status_code == 401
