"""
Manual smoke test for character refinement against an existing DB row.

This is intentionally not fixture-backed or teardown-safe. It is an opt-in
test for validating the end-to-end edit-event flow before a fully isolated
automated test exists.
"""

import os
import uuid
from pathlib import Path

import pytest
from dotenv import load_dotenv
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.story_engine.models import Character, EditEvent
from core.story_engine.models.edit_event import OperationType, TargetType

load_dotenv(
    dotenv_path=Path(__file__).resolve().parents[2] / ".env.smoketest",
    override=False,
)


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        pytest.skip(f"{name} is required for the manual smoke test")
    return value


@pytest.mark.manual
async def test_refine_character_smoke_existing_row(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    project_id = uuid.UUID(_required_env("CHARACTER_REFINE_SMOKE_PROJECT_ID"))
    story_id = uuid.UUID(_required_env("CHARACTER_REFINE_SMOKE_STORY_ID"))
    character_id = uuid.UUID(_required_env("CHARACTER_REFINE_SMOKE_CHARACTER_ID"))
    instruction = _required_env("CHARACTER_REFINE_SMOKE_INSTRUCTION")
    expected_brief_contains = os.getenv("CHARACTER_REFINE_SMOKE_EXPECT_BRIEF_CONTAINS")

    character = await db_session.get(Character, character_id)
    assert character is not None
    assert character.story_id == story_id

    previous_source_event_id = character.source_event_id
    previous_attributes = dict(character.attributes)

    response = await api_client.post(
        f"/api/comic-builder/v2/project/{project_id}"
        f"/story/{story_id}"
        f"/characters/{character_id}/refine",
        json={"instruction": instruction},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(character_id)
    assert body["sourceEventId"] is not None

    await db_session.refresh(character)
    assert character.source_event_id is not None
    assert character.source_event_id != previous_source_event_id
    assert str(character.source_event_id) == body["sourceEventId"]

    event = await db_session.get(EditEvent, character.source_event_id)
    assert event is not None
    assert event.project_id == project_id
    assert event.target_type == TargetType.CHARACTER.value
    assert event.target_id == character_id
    assert event.operation_type == OperationType.REFINE_CHARACTER.value
    assert event.user_instruction == instruction
    assert event.status == "succeeded"
    assert event.input_snapshot == previous_attributes
    assert event.output_snapshot == character.attributes

    if expected_brief_contains is not None:
        assert expected_brief_contains in character.attributes["brief"]
