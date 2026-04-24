"""
Story 120 test gate — GET .../character/{character_id}/renders.

Test invariants:
  1. Returns 200 and an empty list when character exists but has no renders.
  2. Returns 404 when the character does not exist.
  3. After two render calls, both Image rows are returned, newest first.
  4. Each item in the list conforms to ImageResponseSchema shape.
  5. Requires auth.
"""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_v2.models.user import User
from core.story_engine.models import Character, Project, Story
from core.story_engine.models.image import Image as ImageModel
from core.story_engine.models.image import ImageContentType, ImageDiscriminatorKey
from tests.auth_helpers import auth_cookie_header


def _auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    return auth_cookie_header(user_id)


def _renders_url(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    character_id: uuid.UUID,
) -> str:
    return (
        f"/api/comic-builder/v2/project/{project_id}"
        f"/story/{story_id}/character/{character_id}/renders"
    )


async def test_character_renders_returns_empty_list_when_no_renders(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """Returns 200 and empty list when character exists but has no renders."""
    response = await api_client.get(
        _renders_url(project.id, story.id, character.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    assert response.json() == []


async def test_character_renders_returns_404_for_nonexistent_character(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """Returns 404 when the character does not exist."""
    response = await api_client.get(
        _renders_url(project.id, story.id, uuid.uuid4()),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 404


async def test_character_renders_returns_both_renders_newest_first(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """After two render rows, both are returned with the newest first."""
    first = ImageModel.create(
        project_id=project.id,
        user_id=user.id,
        target_id=character.id,
        width=512,
        height=512,
        content_type=ImageContentType.JPEG,
        object_key="char/render-1.jpg",
        bucket="test-bucket",
        size_bytes=100,
        discriminator_key=ImageDiscriminatorKey.CHARACTER_RENDER,
    )
    db_session.add(first)
    await db_session.flush()

    second = ImageModel.create(
        project_id=project.id,
        user_id=user.id,
        target_id=character.id,
        width=512,
        height=512,
        content_type=ImageContentType.JPEG,
        object_key="char/render-2.jpg",
        bucket="test-bucket",
        size_bytes=200,
        discriminator_key=ImageDiscriminatorKey.CHARACTER_RENDER,
    )
    db_session.add(second)
    await db_session.commit()

    response = await api_client.get(
        _renders_url(project.id, story.id, character.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 2
    # Newest first — second was inserted after first
    assert body[0]["id"] == str(second.id)
    assert body[1]["id"] == str(first.id)


async def test_character_renders_response_shape_matches_image_schema(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """Each item in the list conforms to ImageResponseSchema shape."""
    render = ImageModel.create(
        project_id=project.id,
        user_id=user.id,
        target_id=character.id,
        width=800,
        height=600,
        content_type=ImageContentType.JPEG,
        object_key="char/render-shape.jpg",
        bucket="test-bucket",
        size_bytes=4096,
        discriminator_key=ImageDiscriminatorKey.CHARACTER_RENDER,
    )
    db_session.add(render)
    await db_session.commit()

    response = await api_client.get(
        _renders_url(project.id, story.id, character.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    item = response.json()[0]

    assert "id" in item
    assert "objectKey" in item
    assert "bucket" in item
    assert "contentType" in item
    assert "width" in item
    assert "height" in item
    assert "sizeBytes" in item
    assert "createdAt" in item


async def test_character_renders_requires_auth(
    api_client: AsyncClient,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """GET without a token returns 401."""
    response = await api_client.get(_renders_url(project.id, story.id, character.id))
    assert response.status_code == 401
