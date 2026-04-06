"""
Story 50 test gate — POST /panel/{panel_id}/generate endpoint.

Test invariants:
  1. First call (empty attributes): creates EditEvent(GENERATE_PANEL, SUCCEEDED),
     panel.attributes is populated, panel.source_event_id is set.
  2. Calling generate on a panel that already has content returns 400.
  3. input_snapshot on the EditEvent is empty dict (first-gen has no prior attrs).
  4. output_snapshot contains the new attributes.
  5. Returns 404 for a panel that does not exist.
  6. EditEvent is marked FAILED (not left as PENDING) when the LLM call raises.
  7. generate creates panel_character join rows for characters in the LLM response.
  8. generate with a character slug not in the story does not create a join row for it.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.managers.jwt import JWTTokenManager
from core.auth.models.user import User
from core.story_engine.models import Character, Panel, Project, Story
from core.story_engine.models.edit_event import (
    EditEvent,
    EditEventOperationType,
    EditEventStatus,
    EditEventTargetType,
)
from core.story_engine.models.panel_character import PanelCharacter


def _auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    token = JWTTokenManager().create_access_token(str(user_id))
    return {"Authorization": f"Bearer {token}"}


def _mock_panel_content(
    background: str = "A dark forest",
    dialogue: str = "We must move.",
    characters: list[str] | None = None,
) -> MagicMock:
    m = MagicMock()
    m.background = background
    m.dialogue = dialogue
    m.characters = characters or []
    return m


async def test_generate_panel_first_call_populates_attributes(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """First call with empty attributes populates panel.attributes."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()

    mock_content = _mock_panel_content()

    with patch(
        "core.story_engine.service.panel_service.instructor_client.chat.completions.create",
        new_callable=AsyncMock,
        return_value=mock_content,
    ):
        response = await api_client.post(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
            f"/panel/{panel.id}/generate",
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["panel"]["attributes"]["background"] == "A dark forest"
    assert body["panel"]["attributes"]["dialogue"] == "We must move."


async def test_generate_panel_first_call_creates_edit_event_succeeded(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """First call creates EditEvent(GENERATE_PANEL, SUCCEEDED)."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()

    mock_content = _mock_panel_content()

    with patch(
        "core.story_engine.service.panel_service.instructor_client.chat.completions.create",
        new_callable=AsyncMock,
        return_value=mock_content,
    ):
        await api_client.post(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
            f"/panel/{panel.id}/generate",
            headers=_auth_headers(user.id),
        )

    result = await db_session.execute(
        select(EditEvent).where(
            EditEvent.target_type == EditEventTargetType.PANEL,
            EditEvent.target_id == panel.id,
            EditEvent.operation_type == EditEventOperationType.GENERATE_PANEL,
        )
    )
    event = result.scalar_one_or_none()
    assert event is not None
    assert event.status == EditEventStatus.SUCCEEDED


async def test_generate_panel_first_call_sets_source_event_id(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """First call sets panel.source_event_id to the new EditEvent's ID."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()
    panel_id = panel.id

    mock_content = _mock_panel_content()

    with patch(
        "core.story_engine.service.panel_service.instructor_client.chat.completions.create",
        new_callable=AsyncMock,
        return_value=mock_content,
    ):
        await api_client.post(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
            f"/panel/{panel_id}/generate",
            headers=_auth_headers(user.id),
        )

    # Fetch panel from DB with a fresh query to verify source_event_id was set
    # (Don't use expire_all() as it clears the user PK cache causing teardown issues)
    result = await db_session.execute(select(Panel).where(Panel.id == panel_id))
    refreshed_panel = result.scalar_one()
    # The app committed, so we need to refresh to see updated data
    await db_session.refresh(refreshed_panel)
    assert refreshed_panel.source_event_id is not None


async def test_generate_panel_returns_400_if_already_generated(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """400 when panel already has content — caller should use /refine instead."""
    panel = Panel.create(
        story_id=story.id,
        order_index=0,
        attributes={"background": "Forest", "dialogue": "Hello", "characters": []},
    )
    db_session.add(panel)
    await db_session.commit()

    response = await api_client.post(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
        f"/panel/{panel.id}/generate",
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 400


async def test_generate_panel_input_snapshot_is_empty_on_first_gen(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """input_snapshot is empty dict on first generation (no prior attributes)."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()

    mock_content = _mock_panel_content()

    with patch(
        "core.story_engine.service.panel_service.instructor_client.chat.completions.create",
        new_callable=AsyncMock,
        return_value=mock_content,
    ):
        await api_client.post(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
            f"/panel/{panel.id}/generate",
            headers=_auth_headers(user.id),
        )

    result = await db_session.execute(
        select(EditEvent).where(
            EditEvent.target_id == panel.id,
            EditEvent.operation_type == EditEventOperationType.GENERATE_PANEL,
        )
    )
    event = result.scalar_one()
    assert event.input_snapshot == {}


async def test_generate_panel_output_snapshot_contains_new_attributes(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """output_snapshot on EditEvent captures the new attributes."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()

    mock_content = _mock_panel_content(background="Beach")

    with patch(
        "core.story_engine.service.panel_service.instructor_client.chat.completions.create",
        new_callable=AsyncMock,
        return_value=mock_content,
    ):
        await api_client.post(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
            f"/panel/{panel.id}/generate",
            headers=_auth_headers(user.id),
        )

    result = await db_session.execute(
        select(EditEvent).where(
            EditEvent.target_id == panel.id,
            EditEvent.operation_type == EditEventOperationType.GENERATE_PANEL,
        )
    )
    event = result.scalar_one()
    assert event.output_snapshot is not None
    assert event.output_snapshot["background"] == "Beach"


async def test_generate_panel_returns_404_for_nonexistent_panel(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """Returns 404 for a panel that does not exist."""
    nonexistent = uuid.uuid4()
    response = await api_client.post(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
        f"/panel/{nonexistent}/generate",
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_generate_panel_edit_event_marked_failed_on_llm_error(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """EditEvent is marked FAILED when the LLM call raises an exception."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()

    with patch(
        "core.story_engine.service.panel_service.instructor_client.chat.completions.create",
        new_callable=AsyncMock,
        side_effect=RuntimeError("LLM unavailable"),
    ):
        response = await api_client.post(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
            f"/panel/{panel.id}/generate",
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 500

    result = await db_session.execute(
        select(EditEvent).where(
            EditEvent.target_id == panel.id,
            EditEvent.operation_type == EditEventOperationType.GENERATE_PANEL,
        )
    )
    event = result.scalar_one_or_none()
    assert event is not None
    assert event.status == EditEventStatus.FAILED


async def test_generate_panel_creates_panel_character_join_rows(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """generate creates panel_character rows for characters in the LLM response."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()

    # LLM returns the character's slug
    mock_content = _mock_panel_content(characters=[character.slug])

    with patch(
        "core.story_engine.service.panel_service.instructor_client.chat.completions.create",
        new_callable=AsyncMock,
        return_value=mock_content,
    ):
        response = await api_client.post(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
            f"/panel/{panel.id}/generate",
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 200

    result = await db_session.execute(
        select(PanelCharacter).where(PanelCharacter.panel_id == panel.id)
    )
    rows = list(result.scalars().all())
    assert len(rows) == 1
    assert rows[0].character_id == character.id


async def test_generate_panel_skips_unknown_slug_in_join_rows(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """generate skips panel_character creation for slugs not in the story."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()

    # LLM returns one valid slug and one that doesn't exist
    mock_content = _mock_panel_content(
        characters=[character.slug, "nonexistent-character"]
    )

    with patch(
        "core.story_engine.service.panel_service.instructor_client.chat.completions.create",
        new_callable=AsyncMock,
        return_value=mock_content,
    ):
        response = await api_client.post(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
            f"/panel/{panel.id}/generate",
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 200

    result = await db_session.execute(
        select(PanelCharacter).where(PanelCharacter.panel_id == panel.id)
    )
    rows = list(result.scalars().all())
    # Only one row — the invalid slug was silently dropped
    assert len(rows) == 1
    assert rows[0].character_id == character.id
