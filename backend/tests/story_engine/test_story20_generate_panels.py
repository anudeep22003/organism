"""
Story 20 test gate — POST /panels/generate endpoint.

Test invariants:
  1. POST .../panels/generate returns 201 and a list of panels.
  2. Panels are persisted with sequential order_index starting from 0.
  3. Each panel has a corresponding EditEvent(GENERATE_PANEL, SUCCEEDED) in the DB.
  4. panel_character rows reference the correct character UUIDs (slug resolution).
  5. output_snapshot on each EditEvent contains the panel attributes dict.
  6. Returns 400 when story has no text (NoStoryTextError).
  7. Returns 404 when story does not exist.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.models.user import User
from core.story_engine.models import Character, Project, Story
from core.story_engine.models.edit_event import (
    EditEvent,
    EditEventOperationType,
    EditEventStatus,
    EditEventTargetType,
)
from core.story_engine.models.panel_character import PanelCharacter
from tests.auth_helpers import auth_cookie_header


def _auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    return auth_cookie_header(user_id)


def _mock_instructor_panels_response(
    character_slugs: list[str],
) -> MagicMock:
    """Build a mock instructor response with two panels using the given character slugs."""
    mock_response = MagicMock()
    mock_response.panels = [
        MagicMock(
            background="A dark forest clearing",
            dialogue="We must move quickly.",
            characters=character_slugs[:1],  # first panel has first character
        ),
        MagicMock(
            background="A stone fortress",
            dialogue="The gate holds.",
            characters=character_slugs,  # second panel has all characters
        ),
    ]
    return mock_response


# ---------------------------------------------------------------------------
# Endpoint tests (via HTTP API)
# ---------------------------------------------------------------------------


async def test_generate_panels_returns_201_and_list(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """POST .../panels/generate returns 201 with a list of panels."""
    mock_response = _mock_instructor_panels_response([character.slug])

    with patch(
        "core.story_engine.service.panel_service.instructor_client.chat.completions.create",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await api_client.post(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/panels/generate",
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 201
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 2


async def test_generate_panels_sequential_order_index(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """Panels are persisted with sequential order_index starting at 0."""
    mock_response = _mock_instructor_panels_response([character.slug])

    with patch(
        "core.story_engine.service.panel_service.instructor_client.chat.completions.create",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await api_client.post(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/panels/generate",
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 201
    body = response.json()
    order_indices = [p["panel"]["orderIndex"] for p in body]
    assert order_indices == list(range(len(body)))


async def test_generate_panels_creates_edit_events(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """Each panel gets its own EditEvent(GENERATE_PANEL, SUCCEEDED)."""
    mock_response = _mock_instructor_panels_response([character.slug])

    with patch(
        "core.story_engine.service.panel_service.instructor_client.chat.completions.create",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await api_client.post(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/panels/generate",
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 201

    # Fetch panels created during this call
    panel_ids = [uuid.UUID(p["panel"]["id"]) for p in response.json()]

    for panel_id in panel_ids:
        result = await db_session.execute(
            select(EditEvent).where(
                EditEvent.target_type == EditEventTargetType.PANEL,
                EditEvent.target_id == panel_id,
                EditEvent.operation_type == EditEventOperationType.GENERATE_PANEL,
            )
        )
        event = result.scalar_one_or_none()
        assert event is not None, f"No EditEvent found for panel {panel_id}"
        assert event.status == EditEventStatus.SUCCEEDED


async def test_generate_panels_panel_character_slug_resolution(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """panel_character rows reference the correct character_id UUIDs."""
    mock_response = _mock_instructor_panels_response([character.slug])

    with patch(
        "core.story_engine.service.panel_service.instructor_client.chat.completions.create",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await api_client.post(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/panels/generate",
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 201
    panel_ids = [uuid.UUID(p["panel"]["id"]) for p in response.json()]

    # First panel has 1 character (character.slug), second has 1 too
    for panel_id in panel_ids:
        result = await db_session.execute(
            select(PanelCharacter).where(PanelCharacter.panel_id == panel_id)
        )
        join_rows = list(result.scalars().all())
        assert len(join_rows) >= 1
        for row in join_rows:
            assert row.character_id == character.id


async def test_generate_panels_output_snapshot_contains_attributes(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """output_snapshot on EditEvent contains the panel attributes dict."""
    mock_response = _mock_instructor_panels_response([character.slug])

    with patch(
        "core.story_engine.service.panel_service.instructor_client.chat.completions.create",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await api_client.post(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/panels/generate",
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 201
    panel_ids = [uuid.UUID(p["panel"]["id"]) for p in response.json()]

    for panel_id in panel_ids:
        result = await db_session.execute(
            select(EditEvent).where(
                EditEvent.target_type == EditEventTargetType.PANEL,
                EditEvent.target_id == panel_id,
            )
        )
        event = result.scalar_one_or_none()
        assert event is not None
        assert event.output_snapshot is not None
        assert "background" in event.output_snapshot
        assert "dialogue" in event.output_snapshot


async def test_generate_panels_returns_400_when_story_has_no_text(
    api_client: AsyncClient,
    user: User,
    project: Project,
    db_session: AsyncSession,
) -> None:
    """Returns 400 when the story has no text (NoStoryTextError)."""
    empty_story = Story(project_id=project.id, story_text="")
    db_session.add(empty_story)
    await db_session.commit()
    await db_session.refresh(empty_story)

    try:
        response = await api_client.post(
            f"/api/comic-builder/v2/project/{project.id}/story/{empty_story.id}/panels/generate",
            headers=_auth_headers(user.id),
        )
        assert response.status_code == 400
    finally:
        await db_session.delete(empty_story)
        await db_session.commit()


async def test_generate_panels_returns_404_when_story_does_not_exist(
    api_client: AsyncClient,
    user: User,
    project: Project,
) -> None:
    """Returns 404 when the story ID does not exist."""
    nonexistent_story_id = uuid.uuid4()
    response = await api_client.post(
        f"/api/comic-builder/v2/project/{project.id}/story/{nonexistent_story_id}/panels/generate",
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404
