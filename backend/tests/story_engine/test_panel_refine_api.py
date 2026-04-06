"""
Tests for POST .../panel/{panel_id}/refine.

Test invariants:
  1. 200 — refine updates panel attributes based on instruction; returns
     PanelRenderReferencesSchema with updated panel.attributes
  2. 200 — REFINE_PANEL edit event created with SUCCEEDED status, correct
     input_snapshot (pre-refine attributes) and output_snapshot (post-refine)
  3. 404 — panel does not exist
  4. 404 — panel exists but has no attributes yet (must generate before refining)
  5. 401 — no auth token
  6. refine with a new character added → panel_character row created
  7. refine with a character removed → stale panel_character row deleted
  8. refine with unchanged character list → join rows unchanged
"""

import uuid
from unittest.mock import AsyncMock, patch

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
)
from core.story_engine.models.panel_character import PanelCharacter

_jwt = JWTTokenManager()


def _auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    token = _jwt.create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _url(project_id: uuid.UUID, story_id: uuid.UUID, panel_id: uuid.UUID) -> str:
    return (
        f"/api/comic-builder/v2/project/{project_id}"
        f"/story/{story_id}/panel/{panel_id}/refine"
    )


def _mock_regenerate_response() -> object:
    """Minimal instructor response for _regenerate_panel."""
    from core.story_engine.schemas.panel import PanelContent

    return PanelContent(
        background="A refined moonlit forest",
        dialogue="We must move quickly.",
        characters=[],
    )


async def test_refine_panel_200_updates_attributes(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """200 — attributes are updated; response contains updated panel.attributes."""
    panel = Panel.create(
        story_id=story.id,
        order_index=0,
        attributes={
            "background": "Original dark forest",
            "dialogue": "Hello.",
            "characters": [character.slug],
        },
    )
    db_session.add(panel)
    await db_session.commit()

    mock_response = _mock_regenerate_response()

    with patch(
        "core.story_engine.service.panel_service.instructor_client.chat.completions.create",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await api_client.post(
            _url(project.id, story.id, panel.id),
            json={"instruction": "Make the scene more dramatic."},
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 200
    body = response.json()

    # Panel data is nested under "panel" key
    assert body["panel"]["id"] == str(panel.id)
    assert body["panel"]["attributes"]["background"] == "A refined moonlit forest"
    assert body["panel"]["attributes"]["dialogue"] == "We must move quickly."

    # Verify DB was updated
    await db_session.refresh(panel)
    assert panel.attributes["background"] == "A refined moonlit forest"


async def test_refine_panel_200_creates_refine_panel_edit_event(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """200 — REFINE_PANEL edit event created with SUCCEEDED status and correct snapshots."""
    original_attrs = {
        "background": "Original dark forest",
        "dialogue": "Hello.",
        "characters": [character.slug],
    }
    panel = Panel.create(
        story_id=story.id,
        order_index=0,
        attributes=original_attrs,
    )
    db_session.add(panel)
    await db_session.commit()

    mock_response = _mock_regenerate_response()

    with patch(
        "core.story_engine.service.panel_service.instructor_client.chat.completions.create",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await api_client.post(
            _url(project.id, story.id, panel.id),
            json={"instruction": "Make the scene more dramatic."},
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 200

    result = await db_session.execute(
        select(EditEvent).where(
            EditEvent.target_id == panel.id,
            EditEvent.operation_type == EditEventOperationType.REFINE_PANEL,
        )
    )
    event = result.scalar_one_or_none()
    assert event is not None
    assert event.status == EditEventStatus.SUCCEEDED
    assert event.user_instruction == "Make the scene more dramatic."
    # input_snapshot captures the pre-refine attributes
    assert event.input_snapshot == original_attrs
    # output_snapshot captures the post-refine attributes
    assert event.output_snapshot is not None
    assert event.output_snapshot["background"] == "A refined moonlit forest"


async def test_refine_panel_404_panel_not_found(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """404 when the panel does not exist."""
    response = await api_client.post(
        _url(project.id, story.id, uuid.uuid4()),
        json={"instruction": "Make it better."},
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_refine_panel_404_panel_not_yet_generated(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """404 when panel exists but has no attributes (cannot refine before generating)."""
    panel = Panel.create(
        story_id=story.id,
        order_index=0,
        attributes={},  # empty — not yet generated
    )
    db_session.add(panel)
    await db_session.commit()

    response = await api_client.post(
        _url(project.id, story.id, panel.id),
        json={"instruction": "Make it better."},
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_refine_panel_401_no_token(
    api_client: AsyncClient,
    project: Project,
    story: Story,
) -> None:
    """401 when no auth token is provided."""
    response = await api_client.post(
        _url(project.id, story.id, uuid.uuid4()),
        json={"instruction": "Make it better."},
    )
    assert response.status_code == 401


async def test_refine_panel_adds_panel_character_row_for_new_character(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """refine with a new character in the LLM response creates the panel_character row."""
    # Panel starts with no characters
    panel = Panel.create(
        story_id=story.id,
        order_index=0,
        attributes={"background": "Forest", "dialogue": "Hi.", "characters": []},
    )
    db_session.add(panel)
    await db_session.commit()

    # LLM returns the character as newly added
    mock_response = _mock_regenerate_response()
    mock_response.characters = [character.slug]  # type: ignore[attr-defined]

    with patch(
        "core.story_engine.service.panel_service.instructor_client.chat.completions.create",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await api_client.post(
            _url(project.id, story.id, panel.id),
            json={"instruction": f"Add {character.slug} to the scene."},
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 200

    result = await db_session.execute(
        select(PanelCharacter).where(PanelCharacter.panel_id == panel.id)
    )
    rows = list(result.scalars().all())
    assert len(rows) == 1
    assert rows[0].character_id == character.id


async def test_refine_panel_removes_panel_character_row_for_dropped_character(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """refine with character removed from LLM response deletes the panel_character row."""
    panel = Panel.create(
        story_id=story.id,
        order_index=0,
        attributes={
            "background": "Forest",
            "dialogue": "Hi.",
            "characters": [character.slug],
        },
    )
    db_session.add(panel)
    await db_session.flush()

    # Pre-existing join row
    db_session.add(PanelCharacter(panel_id=panel.id, character_id=character.id))
    await db_session.commit()

    # LLM returns no characters — character was removed
    mock_response = _mock_regenerate_response()
    mock_response.characters = []  # type: ignore[attr-defined]

    with patch(
        "core.story_engine.service.panel_service.instructor_client.chat.completions.create",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await api_client.post(
            _url(project.id, story.id, panel.id),
            json={"instruction": "Remove all characters from the scene."},
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 200

    result = await db_session.execute(
        select(PanelCharacter).where(PanelCharacter.panel_id == panel.id)
    )
    rows = list(result.scalars().all())
    assert len(rows) == 0


async def test_refine_panel_unchanged_character_list_keeps_join_rows(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """refine with unchanged character list leaves panel_character rows intact."""
    panel = Panel.create(
        story_id=story.id,
        order_index=0,
        attributes={
            "background": "Forest",
            "dialogue": "Hi.",
            "characters": [character.slug],
        },
    )
    db_session.add(panel)
    await db_session.flush()

    db_session.add(PanelCharacter(panel_id=panel.id, character_id=character.id))
    await db_session.commit()

    # LLM returns the same character
    mock_response = _mock_regenerate_response()
    mock_response.characters = [character.slug]  # type: ignore[attr-defined]

    with patch(
        "core.story_engine.service.panel_service.instructor_client.chat.completions.create",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await api_client.post(
            _url(project.id, story.id, panel.id),
            json={"instruction": "Make the dialogue more dramatic."},
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 200

    result = await db_session.execute(
        select(PanelCharacter).where(PanelCharacter.panel_id == panel.id)
    )
    rows = list(result.scalars().all())
    assert len(rows) == 1
    assert rows[0].character_id == character.id
