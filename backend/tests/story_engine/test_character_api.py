"""
API tests for character endpoints (GET single, PATCH, DELETE).

Full stack — real FastAPI app, real service + repository, real Postgres.
Fixtures in conftest.py handle data setup and cleanup.

Base URL: /api/comic-builder/v2/project/{project_id}/story/{story_id}/characters/{character_id}
"""

import uuid

from httpx import AsyncClient

from core.story_engine.models import Character, Project, Story

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def character_url(project: Project, story: Story, character: Character) -> str:
    return (
        f"/api/comic-builder/v2/project/{project.id}"
        f"/story/{story.id}"
        f"/characters/{character.id}"
    )


def bad_character_url(project: Project, story: Story) -> str:
    """A URL with a valid project/story but a non-existent character ID."""
    return (
        f"/api/comic-builder/v2/project/{project.id}"
        f"/story/{story.id}"
        f"/characters/{uuid.uuid4()}"
    )


def bad_story_url(project: Project, character: Character) -> str:
    """A URL with a valid project/character but a non-existent story ID."""
    return (
        f"/api/comic-builder/v2/project/{project.id}"
        f"/story/{uuid.uuid4()}"
        f"/characters/{character.id}"
    )


# ---------------------------------------------------------------------------
# GET /project/{project_id}/story/{story_id}/characters/{character_id}
# ---------------------------------------------------------------------------


async def test_get_character_200(
    api_client: AsyncClient,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """Returns 200 with the correct character payload."""
    response = await api_client.get(character_url(project, story, character))

    assert response.status_code == 200
    body = response.json()

    # IDs and core fields
    assert body["id"] == str(character.id)
    assert body["name"] == character.name
    assert body["slug"] == character.slug
    assert body["sourceEventId"] is None

    # AliasedBaseModel serialises to camelCase
    assert "createdAt" in body
    assert "updatedAt" in body

    # Attributes are returned as-is
    assert body["attributes"]["name"] == "Aragorn"
    assert body["attributes"]["character_type"] == "protagonist"


async def test_get_character_404_bad_character(
    api_client: AsyncClient,
    project: Project,
    story: Story,
    character: Character,  # ensures story exists — only character ID is wrong
) -> None:
    """Returns 404 when the character ID does not exist."""
    response = await api_client.get(bad_character_url(project, story))

    assert response.status_code == 404


async def test_get_character_404_bad_story(
    api_client: AsyncClient,
    project: Project,
    story: Story,
    character: Character,  # ensures character row exists — only story ID is wrong
) -> None:
    """Returns 404 when the story ID does not exist under the project."""
    response = await api_client.get(bad_story_url(project, character))

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /project/{project_id}/story/{story_id}/characters/{character_id}
# ---------------------------------------------------------------------------


async def test_patch_character_200_name(
    api_client: AsyncClient,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """PATCH with a new name returns 200 and the updated name."""
    response = await api_client.patch(
        character_url(project, story, character),
        json={"name": "Strider"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Strider"
    assert body["attributes"]["name"] == "Strider"


async def test_patch_character_only_updates_provided_fields(
    api_client: AsyncClient,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """PATCH with one field leaves all other attribute fields untouched."""
    response = await api_client.patch(
        character_url(project, story, character),
        json={"role": "King"},
    )

    assert response.status_code == 200
    body = response.json()

    # Updated field
    assert body["attributes"]["role"] == "King"

    # All other fields must be unchanged
    assert body["attributes"]["name"] == "Aragorn"
    assert body["attributes"]["character_type"] == "protagonist"
    assert body["attributes"]["demeanor"] == "Stoic and resolute"


async def test_patch_character_404_bad_character(
    api_client: AsyncClient,
    project: Project,
    story: Story,
    character: Character,  # ensures story exists — only character ID is wrong
) -> None:
    """PATCH returns 404 when the character ID does not exist."""
    response = await api_client.patch(
        bad_character_url(project, story),
        json={"name": "Ghost"},
    )

    assert response.status_code == 404


async def test_patch_character_404_bad_story(
    api_client: AsyncClient,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """PATCH returns 404 when the story ID does not exist."""
    response = await api_client.patch(
        bad_story_url(project, character),
        json={"name": "Ghost"},
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /project/{project_id}/story/{story_id}/characters/{character_id}
# ---------------------------------------------------------------------------


async def test_delete_character_204(
    api_client: AsyncClient,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """DELETE returns 204 with no response body."""
    response = await api_client.delete(character_url(project, story, character))

    assert response.status_code == 204
    assert response.content == b""


async def test_delete_character_then_get_404(
    api_client: AsyncClient,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """After a successful DELETE, GET on the same ID returns 404."""
    url = character_url(project, story, character)

    delete_response = await api_client.delete(url)
    assert delete_response.status_code == 204

    get_response = await api_client.get(url)
    assert get_response.status_code == 404


async def test_delete_character_404_bad_character(
    api_client: AsyncClient,
    project: Project,
    story: Story,
    character: Character,  # ensures story exists — only character ID is wrong
) -> None:
    """DELETE returns 404 when the character ID does not exist."""
    response = await api_client.delete(bad_character_url(project, story))

    assert response.status_code == 404
