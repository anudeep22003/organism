"""
Story 80 test gate — GET /panel/{panel_id}/history endpoint.

Test invariants:
  1. GET .../history returns 200 with EditEvents ordered newest first.
  2. Returns an empty list when no events exist (not 404).
  3. Returns 404 when the panel does not exist.
  4. History includes both GENERATE_PANEL and RENDER_PANEL event types.
  5. The limit query parameter restricts the number of results returned.
"""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_v2.models.user import User
from core.story_engine.models import Panel, Project, Story
from core.story_engine.models.edit_event import (
    EditEvent,
    EditEventOperationType,
    EditEventStatus,
    EditEventTargetType,
)
from tests.auth_helpers import auth_cookie_header


def _auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    return auth_cookie_header(user_id)


def _make_edit_event(
    project_id: uuid.UUID,
    panel_id: uuid.UUID,
    operation_type: EditEventOperationType,
) -> EditEvent:
    return EditEvent.create_edit_event(
        project_id=project_id,
        target_type=EditEventTargetType.PANEL,
        target_id=panel_id,
        operation_type=operation_type,
        user_instruction="",
        status=EditEventStatus.SUCCEEDED,
    )


async def test_panel_history_returns_200_ordered_newest_first(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """GET .../history returns 200 with events ordered newest first."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.flush()

    event1 = _make_edit_event(
        project.id, panel.id, EditEventOperationType.GENERATE_PANEL
    )
    event2 = _make_edit_event(project.id, panel.id, EditEventOperationType.RENDER_PANEL)
    db_session.add(event1)
    db_session.add(event2)
    await db_session.commit()

    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
        f"/panel/{panel.id}/history",
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 2
    # Newest first — event2 was created after event1
    assert body[0]["id"] == str(event2.id)
    assert body[1]["id"] == str(event1.id)


async def test_panel_history_returns_empty_list_when_no_events(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """Returns empty list (not 404) when no events exist."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()

    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
        f"/panel/{panel.id}/history",
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    assert response.json() == []


async def test_panel_history_returns_404_when_panel_not_found(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """Returns 404 when the panel does not exist."""
    nonexistent = uuid.uuid4()
    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
        f"/panel/{nonexistent}/history",
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_panel_history_includes_both_generate_and_render_event_types(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """History includes both GENERATE_PANEL and RENDER_PANEL event types."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.flush()

    generate_event = _make_edit_event(
        project.id, panel.id, EditEventOperationType.GENERATE_PANEL
    )
    render_event = _make_edit_event(
        project.id, panel.id, EditEventOperationType.RENDER_PANEL
    )
    db_session.add(generate_event)
    db_session.add(render_event)
    await db_session.commit()

    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
        f"/panel/{panel.id}/history",
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    body = response.json()
    op_types = {e["operationType"] for e in body}
    assert EditEventOperationType.GENERATE_PANEL in op_types
    assert EditEventOperationType.RENDER_PANEL in op_types


async def test_panel_history_limit_restricts_results(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """?limit=N caps the number of results returned."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.flush()

    for _ in range(5):
        event = _make_edit_event(
            project.id, panel.id, EditEventOperationType.GENERATE_PANEL
        )
        db_session.add(event)
    await db_session.commit()

    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
        f"/panel/{panel.id}/history?limit=3",
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    assert len(response.json()) == 3
