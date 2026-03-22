"""
API tests for story endpoints (v2).

GET  /api/comic-builder/v2/project/{project_id}/story/{story_id}
GET  /api/comic-builder/v2/project/{project_id}/story/{story_id}/history

The generate endpoint (POST …/generate) calls OpenAI and returns an NDJSON
stream — that path is covered by manual/integration smoke tests.  Here we
test only the non-LLM surfaces:

Invariants under test:
- Response shapes (camelCase, required fields, types)
- 404 for unknown story or wrong project
- Auth boundary: 401 without a token
- History endpoint returns an empty list when no edit events exist

No mocking. Real FastAPI app, real Postgres.
"""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.managers.jwt import JWTTokenManager
from core.auth.models.user import User
from core.story_engine.models import Project, Story
from core.story_engine.models.edit_event import (
    EditEvent,
    EditEventOperationType,
    EditEventStatus,
    EditEventTargetType,
)

_jwt = JWTTokenManager()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    token = _jwt.create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _story_url(project_id: uuid.UUID, story_id: uuid.UUID) -> str:
    return f"/api/comic-builder/v2/project/{project_id}/story/{story_id}"


def _history_url(project_id: uuid.UUID, story_id: uuid.UUID) -> str:
    return f"/api/comic-builder/v2/project/{project_id}/story/{story_id}/history"


# ---------------------------------------------------------------------------
# GET /project/{project_id}/story/{story_id}
# ---------------------------------------------------------------------------


async def test_get_story_returns_200(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """Fetching an existing story returns 200."""
    response = await api_client.get(
        _story_url(project.id, story.id),
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 200


async def test_get_story_response_shape(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """The story response contains all StoryResponseSchema fields.

    If the schema changes (field renames, removals), this test catches it.
    """
    response = await api_client.get(
        _story_url(project.id, story.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["id"] == str(story.id)
    assert body["projectId"] == str(project.id)
    assert "storyText" in body
    assert "userInputText" in body
    assert "sourceEventId" in body
    assert "meta" in body


async def test_get_story_text_matches_fixture(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """The returned storyText matches what was stored in the fixture."""
    response = await api_client.get(
        _story_url(project.id, story.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    assert response.json()["storyText"] == story.story_text


async def test_get_story_source_event_null_before_generation(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """A story that has never been generated has sourceEventId = null."""
    response = await api_client.get(
        _story_url(project.id, story.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    assert response.json()["sourceEventId"] is None


async def test_get_story_404_wrong_story_id(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,  # ensures project row exists
) -> None:
    """A non-existent story ID returns 404."""
    response = await api_client.get(
        _story_url(project.id, uuid.uuid4()),
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_get_story_404_wrong_project_id(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """A story under the wrong project ID returns 404."""
    response = await api_client.get(
        _story_url(uuid.uuid4(), story.id),
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_get_story_requires_auth(
    api_client: AsyncClient,
    project: Project,
    story: Story,
) -> None:
    """GET story without a token returns 401."""
    response = await api_client.get(_story_url(project.id, story.id))
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /project/{project_id}/story/{story_id}/history
# ---------------------------------------------------------------------------


async def test_get_story_history_returns_empty_list_when_no_events(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """A fresh story has no edit events — the history endpoint returns []."""
    response = await api_client.get(
        _history_url(project.id, story.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    assert response.json() == []


async def test_get_story_history_returns_list_with_events(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    db_session: AsyncSession,
) -> None:
    """After creating an edit event, the history endpoint returns it."""
    # Insert an edit event directly so we don't need to call OpenAI
    event = EditEvent.create_edit_event(
        project_id=project.id,
        target_type=EditEventTargetType.STORY,
        target_id=story.id,
        operation_type=EditEventOperationType.GENERATE_STORY,
        user_instruction="write me a story",
        status=EditEventStatus.SUCCEEDED,
        output_snapshot={"storyText": "Once upon a time…"},
    )
    db_session.add(event)
    await db_session.commit()

    response = await api_client.get(
        _history_url(project.id, story.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 1

    found = next((e for e in body if e["targetId"] == str(story.id)), None)
    assert found is not None


async def test_get_story_history_event_shape(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    db_session: AsyncSession,
) -> None:
    """Each history entry has all EditEventResponseSchema fields.

    Adding or removing schema fields should surface here.
    """
    event = EditEvent.create_edit_event(
        project_id=project.id,
        target_type=EditEventTargetType.STORY,
        target_id=story.id,
        operation_type=EditEventOperationType.GENERATE_STORY,
        user_instruction="make a comic story",
        status=EditEventStatus.SUCCEEDED,
    )
    db_session.add(event)
    await db_session.commit()

    response = await api_client.get(
        _history_url(project.id, story.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    entry = response.json()[0]

    # Fields from EditEventResponseSchema
    assert "id" in entry
    assert "projectId" in entry
    assert "targetType" in entry
    assert "targetId" in entry
    assert "operationType" in entry
    assert "userInstruction" in entry
    assert "status" in entry
    assert "createdAt" in entry
    # outputSnapshot may be null — but the key must be present
    assert "outputSnapshot" in entry


async def test_get_story_history_requires_auth(
    api_client: AsyncClient,
    project: Project,
    story: Story,
) -> None:
    """GET story history without a token returns 401."""
    response = await api_client.get(_history_url(project.id, story.id))
    assert response.status_code == 401


async def test_get_story_history_limit_param(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    db_session: AsyncSession,
) -> None:
    """The `limit` query param caps how many events are returned."""
    # Create 5 events
    for i in range(5):
        event = EditEvent.create_edit_event(
            project_id=project.id,
            target_type=EditEventTargetType.STORY,
            target_id=story.id,
            operation_type=EditEventOperationType.GENERATE_STORY,
            user_instruction=f"instruction {i}",
            status=EditEventStatus.SUCCEEDED,
        )
        db_session.add(event)
    await db_session.commit()

    response = await api_client.get(
        _history_url(project.id, story.id),
        headers=_auth_headers(user.id),
        params={"limit": 2},
    )

    assert response.status_code == 200
    assert len(response.json()) <= 2
