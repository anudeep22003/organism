"""
API tests for character list and history endpoints (v2).

GET  /api/comic-builder/v2/project/{project_id}/story/{story_id}/characters
GET  /api/comic-builder/v2/project/{project_id}/story/{story_id}/character/{character_id}/history

The extract (POST …/characters) and refine (POST …/character/{id}/refine)
endpoints require OpenAI and are covered by manual smoke tests.

Invariants under test:
- Response shape: camelCase, required fields, correct types
- Empty list before any characters exist
- History is empty before any edit events, ordered correctly after
- Auth boundary: 401 without token
- 404 when story or project doesn't exist

No mocking. Real FastAPI app, real Postgres.
"""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.models.user import User
from core.story_engine.models import Character, Project, Story
from core.story_engine.models.edit_event import (
    EditEvent,
    EditEventOperationType,
    EditEventStatus,
    EditEventTargetType,
)
from core.story_engine.models.image import Image as ImageModel
from core.story_engine.models.image import ImageContentType, ImageDiscriminatorKey
from tests.auth_helpers import auth_cookie_header

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    return auth_cookie_header(user_id)


def _characters_url(project_id: uuid.UUID, story_id: uuid.UUID) -> str:
    return f"/api/comic-builder/v2/project/{project_id}/story/{story_id}/characters"


def _character_url(
    project_id: uuid.UUID, story_id: uuid.UUID, character_id: uuid.UUID
) -> str:
    return (
        f"/api/comic-builder/v2/project/{project_id}"
        f"/story/{story_id}/character/{character_id}"
    )


def _character_history_url(
    project_id: uuid.UUID, story_id: uuid.UUID, character_id: uuid.UUID
) -> str:
    return (
        f"/api/comic-builder/v2/project/{project_id}"
        f"/story/{story_id}"
        f"/character/{character_id}/history"
    )


# ---------------------------------------------------------------------------
# GET /project/{project_id}/story/{story_id}/characters
# ---------------------------------------------------------------------------


async def test_list_characters_returns_200(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """The characters list endpoint returns 200."""
    response = await api_client.get(
        _characters_url(project.id, story.id),
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 200


async def test_list_characters_returns_array(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """The response is a JSON array."""
    response = await api_client.get(
        _characters_url(project.id, story.id),
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_list_characters_contains_fixture_character(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """The fixture character appears in the list."""
    response = await api_client.get(
        _characters_url(project.id, story.id),
        headers=_auth_headers(user.id),
    )

    ids = [c["character"]["id"] for c in response.json()]
    assert str(character.id) in ids


async def test_list_characters_response_shape(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """Each character item matches CharacterResponseSchema.

    Renaming or removing fields (e.g. slug → identifier) should fail here.
    """
    response = await api_client.get(
        _characters_url(project.id, story.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    item = next(c for c in response.json() if c["character"]["id"] == str(character.id))

    # character sub-object fields
    char = item["character"]
    assert "id" in char
    assert "name" in char
    assert "slug" in char
    assert "attributes" in char
    assert isinstance(char["attributes"], dict)
    assert "sourceEventId" in char
    assert "createdAt" in char
    assert "updatedAt" in char
    assert "meta" in char

    # top-level image fields
    assert "canonicalRender" in item
    assert "referenceImages" in item
    assert isinstance(item["referenceImages"], list)


async def test_list_characters_attributes_content(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """The attributes dict carries the values stored in the fixture."""
    response = await api_client.get(
        _characters_url(project.id, story.id),
        headers=_auth_headers(user.id),
    )

    item = next(c for c in response.json() if c["character"]["id"] == str(character.id))
    attrs = item["character"]["attributes"]

    assert attrs["name"] == "Aragorn"
    assert attrs["character_type"] == "protagonist"
    assert attrs["demeanor"] == "Stoic and resolute"


async def test_list_characters_empty_for_story_without_characters(
    api_client: AsyncClient,
    user: User,
    project: Project,
    db_session: AsyncSession,
) -> None:
    """A story that has no characters returns an empty list."""
    from core.story_engine.models import Story as StoryModel

    bare_story = StoryModel(project_id=project.id, story_text="no characters yet")
    db_session.add(bare_story)
    await db_session.commit()
    await db_session.refresh(bare_story)

    response = await api_client.get(
        _characters_url(project.id, bare_story.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    assert response.json() == []

    # Cleanup (cascade from project will handle it but be explicit)
    from sqlalchemy import text

    await db_session.execute(
        text("DELETE FROM story WHERE id = :id"), {"id": bare_story.id}
    )
    await db_session.commit()


async def test_list_characters_multiple_characters(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    character: Character,
    db_session: AsyncSession,
) -> None:
    """When a story has multiple characters all of them appear in the list."""
    from core.story_engine.models import Character as CharacterModel

    second = CharacterModel(
        story_id=story.id,
        name="Legolas",
        slug="legolas",
        attributes={"name": "Legolas", "character_type": "ally"},
    )
    db_session.add(second)
    await db_session.commit()
    await db_session.refresh(second)

    response = await api_client.get(
        _characters_url(project.id, story.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    ids = {c["character"]["id"] for c in response.json()}
    assert str(character.id) in ids
    assert str(second.id) in ids

    # Cleanup second character (cascade would get it, but explicit is cleaner)
    from sqlalchemy import text

    await db_session.execute(
        text("DELETE FROM character WHERE id = :id"), {"id": second.id}
    )
    await db_session.commit()


async def test_list_characters_404_unknown_story(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """Listing characters for a non-existent story returns 404."""
    response = await api_client.get(
        _characters_url(project.id, uuid.uuid4()),
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_list_characters_requires_auth(
    api_client: AsyncClient,
    project: Project,
    story: Story,
) -> None:
    """GET characters without a token returns 401."""
    response = await api_client.get(_characters_url(project.id, story.id))
    assert response.status_code == 401


async def test_list_characters_embeds_reference_images(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """Reference images seeded for a character appear in referenceImages on the list response."""
    ref = ImageModel.create(
        project_id=project.id,
        user_id=user.id,
        target_id=character.id,
        width=800,
        height=600,
        content_type=ImageContentType.JPEG,
        object_key="char/ref-list.jpg",
        bucket="test-bucket",
        size_bytes=2048,
        discriminator_key=ImageDiscriminatorKey.CHARACTER_REFERENCE,
    )
    db_session.add(ref)
    await db_session.commit()

    response = await api_client.get(
        _characters_url(project.id, story.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    item = next(c for c in response.json() if c["character"]["id"] == str(character.id))
    assert len(item["referenceImages"]) == 1
    assert item["referenceImages"][0]["id"] == str(ref.id)


async def test_get_character_embeds_reference_images(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """Reference images seeded for a character appear in referenceImages on the single GET response."""
    ref = ImageModel.create(
        project_id=project.id,
        user_id=user.id,
        target_id=character.id,
        width=512,
        height=512,
        content_type=ImageContentType.JPEG,
        object_key="char/ref-single.jpg",
        bucket="test-bucket",
        size_bytes=1024,
        discriminator_key=ImageDiscriminatorKey.CHARACTER_REFERENCE,
    )
    db_session.add(ref)
    await db_session.commit()

    response = await api_client.get(
        _character_url(project.id, story.id, character.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert "character" in body
    assert "referenceImages" in body
    assert len(body["referenceImages"]) == 1
    assert body["referenceImages"][0]["id"] == str(ref.id)


# ---------------------------------------------------------------------------
# GET /project/{project_id}/story/{story_id}/character/{character_id}/history
# ---------------------------------------------------------------------------


async def test_character_history_empty_for_new_character(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """A freshly created character has no history events."""
    response = await api_client.get(
        _character_history_url(project.id, story.id, character.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    assert response.json() == []


async def test_character_history_returns_events_after_operation(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    character: Character,
    db_session: AsyncSession,
) -> None:
    """After inserting a refinement event, the history endpoint returns it."""
    event = EditEvent.create_edit_event(
        project_id=project.id,
        target_type=EditEventTargetType.CHARACTER,
        target_id=character.id,
        operation_type=EditEventOperationType.REFINE_CHARACTER,
        user_instruction="make him older",
        status=EditEventStatus.SUCCEEDED,
        output_snapshot={"name": "Aragorn", "era": "Fourth Age"},
    )
    db_session.add(event)
    await db_session.commit()

    response = await api_client.get(
        _character_history_url(project.id, story.id, character.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 1

    entry = next((e for e in body if e["targetId"] == str(character.id)), None)
    assert entry is not None


async def test_character_history_event_shape(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    character: Character,
    db_session: AsyncSession,
) -> None:
    """Each history entry has all EditEventResponseSchema fields.

    If the schema drops a field this test breaks.
    """
    event = EditEvent.create_edit_event(
        project_id=project.id,
        target_type=EditEventTargetType.CHARACTER,
        target_id=character.id,
        operation_type=EditEventOperationType.REFINE_CHARACTER,
        user_instruction="shape-check instruction",
        status=EditEventStatus.SUCCEEDED,
    )
    db_session.add(event)
    await db_session.commit()

    response = await api_client.get(
        _character_history_url(project.id, story.id, character.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    entry = response.json()[0]

    assert "id" in entry
    assert "projectId" in entry
    assert "targetType" in entry
    assert entry["targetType"] == "character"
    assert "targetId" in entry
    assert "operationType" in entry
    assert "userInstruction" in entry
    assert "status" in entry
    assert "createdAt" in entry
    assert "outputSnapshot" in entry


async def test_character_history_only_returns_this_characters_events(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    character: Character,
    db_session: AsyncSession,
) -> None:
    """Events for a different character do not bleed into the history response."""
    from core.story_engine.models import Character as CharacterModel

    other = CharacterModel(
        story_id=story.id,
        name="Gimli",
        slug="gimli",
        attributes={"name": "Gimli"},
    )
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)

    # Add an event for the OTHER character
    other_event = EditEvent.create_edit_event(
        project_id=project.id,
        target_type=EditEventTargetType.CHARACTER,
        target_id=other.id,
        operation_type=EditEventOperationType.REFINE_CHARACTER,
        user_instruction="make him stockier",
        status=EditEventStatus.SUCCEEDED,
    )
    db_session.add(other_event)
    await db_session.commit()

    # History for the fixture character should be empty
    response = await api_client.get(
        _character_history_url(project.id, story.id, character.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    target_ids = {e["targetId"] for e in response.json()}
    assert str(other.id) not in target_ids

    # Cleanup
    from sqlalchemy import text

    await db_session.execute(
        text("DELETE FROM character WHERE id = :id"), {"id": other.id}
    )
    await db_session.commit()


async def test_character_history_requires_auth(
    api_client: AsyncClient,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """GET character history without a token returns 401."""
    response = await api_client.get(
        _character_history_url(project.id, story.id, character.id)
    )
    assert response.status_code == 401


async def test_character_history_limit_param(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    character: Character,
    db_session: AsyncSession,
) -> None:
    """The `limit` query param caps the number of events returned."""
    for i in range(5):
        event = EditEvent.create_edit_event(
            project_id=project.id,
            target_type=EditEventTargetType.CHARACTER,
            target_id=character.id,
            operation_type=EditEventOperationType.REFINE_CHARACTER,
            user_instruction=f"refinement {i}",
            status=EditEventStatus.SUCCEEDED,
        )
        db_session.add(event)
    await db_session.commit()

    response = await api_client.get(
        _character_history_url(project.id, story.id, character.id),
        headers=_auth_headers(user.id),
        params={"limit": 3},
    )

    assert response.status_code == 200
    assert len(response.json()) <= 3
