"""
Manual smoke test for character refinement against an existing DB row.

This is intentionally not fixture-backed or teardown-safe. It is an opt-in
test for validating the end-to-end edit-event flow before a fully isolated
automated test exists.
"""

import pytest
from httpx import AsyncClient
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.story_engine.models import Character, EditEvent
from core.story_engine.models.edit_event import (
    EditEventOperationType,
    EditEventStatus,
    EditEventTargetType,
)
from core.story_engine.schemas.character import CharacterResponseSchema

# Manual Test targets
PROJECT_ID = "9c10291d-4b0a-4c2f-8deb-417d36a12d7b"
STORY_ID = "0a358afa-670c-4729-b1d3-838a76320993"
CHARACTER_ID = "61c317cf-06c9-4d95-bd06-6d9518a4eeba"


@pytest.mark.manual
async def test_refine_character_smoke_existing_row(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    # Local Test parameters
    test_instruction = "Make the character more interesting and engaging. Include the word interesting and engaging in the brief."
    test_expect_brief_contains = "interesting"

    character = await db_session.get(Character, CHARACTER_ID)
    assert character is not None
    assert str(character.story_id) == STORY_ID

    previous_source_event_id = character.source_event_id
    previous_attributes = dict(character.attributes)

    response = await api_client.post(
        f"/api/comic-builder/v2/project/{PROJECT_ID}"
        f"/story/{STORY_ID}"
        f"/character/{CHARACTER_ID}/refine",
        json={"instruction": test_instruction},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(CHARACTER_ID)
    assert body["sourceEventId"] is not None

    await db_session.refresh(character)
    assert character.source_event_id is not None
    assert character.source_event_id != previous_source_event_id
    assert str(character.source_event_id) == body["sourceEventId"]

    event = await db_session.get(EditEvent, character.source_event_id)
    assert event is not None
    assert str(event.project_id) == PROJECT_ID
    assert str(event.target_type) == EditEventTargetType.CHARACTER.value
    assert str(event.target_id) == CHARACTER_ID
    assert event.operation_type == EditEventOperationType.REFINE_CHARACTER.value
    assert event.user_instruction == test_instruction
    assert event.status == "succeeded"
    assert event.input_snapshot == previous_attributes
    assert event.output_snapshot == character.attributes

    if test_expect_brief_contains is not None:
        assert test_expect_brief_contains in character.attributes["brief"]


@pytest.mark.manual
async def test_get_existing_character_edit_history(
    api_client: AsyncClient,
) -> None:
    possible_operation_types = [
        EditEventOperationType.REFINE_CHARACTER,
    ]

    response = await api_client.get(
        f"/api/comic-builder/v2/project/{PROJECT_ID}"
        f"/story/{STORY_ID}"
        f"/character/{CHARACTER_ID}/history",
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1
    for event in body:
        assert str(event["targetId"]) == CHARACTER_ID
        assert event["operationType"] in possible_operation_types
        assert event["userInstruction"] != ""
        assert event["status"] in [
            EditEventStatus.SUCCEEDED,
            EditEventStatus.FAILED,
            EditEventStatus.PENDING,
        ]


@pytest.mark.manual
async def test_render_existing_character(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    pre_render_character = await db_session.get(Character, CHARACTER_ID)
    assert pre_render_character is not None

    # to compare
    pre_render_url = pre_render_character.render_url
    logger.info(f"Pre render URL: {pre_render_url}")

    response = await api_client.post(
        f"/api/comic-builder/v2/project/{PROJECT_ID}"
        f"/story/{STORY_ID}"
        f"/character/{CHARACTER_ID}/render",
    )

    assert response.status_code == 200
    body = response.json()
    post_render_character_schema = CharacterResponseSchema.model_validate(body)
    assert post_render_character_schema.render_url is not None
    assert post_render_character_schema.render_url != pre_render_url
    logger.info(f"Post render URL: {post_render_character_schema.render_url}")
    logger.info(f"Post render URL: {body}")
