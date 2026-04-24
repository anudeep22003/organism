"""
Tests for DELETE .../character/{character_id}/reference-image/{image_id}.

Test invariants:
  1. Returns 204 when the reference image exists and belongs to the character.
  2. After deletion, the image no longer appears in GET .../reference-images.
  3. Returns 404 when the image_id does not exist.
  4. Returns 404 when the image belongs to a different character (cross-character guard).
  5. Returns 401 when no auth token is provided.
  6. Returns 404 when the image exists but has the wrong discriminator (render, not reference).
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


def _delete_url(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    character_id: uuid.UUID,
    image_id: uuid.UUID,
) -> str:
    return (
        f"/api/comic-builder/v2/project/{project_id}"
        f"/story/{story_id}/character/{character_id}/reference-image/{image_id}"
    )


def _reference_images_url(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    character_id: uuid.UUID,
) -> str:
    return (
        f"/api/comic-builder/v2/project/{project_id}"
        f"/story/{story_id}/character/{character_id}/reference-images"
    )


def _make_reference_image(
    project: Project,
    user: User,
    character: Character,
    object_key: str = "char/ref-1.jpg",
) -> ImageModel:
    return ImageModel.create(
        project_id=project.id,
        user_id=user.id,
        target_id=character.id,
        width=512,
        height=512,
        content_type=ImageContentType.JPEG,
        object_key=object_key,
        bucket="test-bucket",
        size_bytes=1024,
        discriminator_key=ImageDiscriminatorKey.CHARACTER_REFERENCE,
    )


async def test_delete_reference_image_204(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """204 on success; image is no longer returned by the list endpoint."""
    image = _make_reference_image(project, user, character)
    db_session.add(image)
    await db_session.commit()

    response = await api_client.delete(
        _delete_url(project.id, story.id, character.id, image.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 204
    assert response.content == b""

    list_response = await api_client.get(
        _reference_images_url(project.id, story.id, character.id),
        headers=_auth_headers(user.id),
    )
    assert list_response.status_code == 200
    assert list_response.json() == []


async def test_delete_reference_image_404_bad_image(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """404 when the image_id does not exist."""
    response = await api_client.delete(
        _delete_url(project.id, story.id, character.id, uuid.uuid4()),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 404


async def test_delete_reference_image_404_wrong_character(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """404 when the image belongs to a different character."""
    other_character = Character(
        story_id=story.id,
        name="Other",
        slug="other",
        attributes={
            "name": "Other",
            "brief": "Another character",
            "character_type": "humanoid",
            "era": "modern",
            "visual_form": "tall",
            "color_palette": "grey",
            "distinctive_markers": "none",
            "demeanor": "calm",
            "role": "minor",
        },
    )
    db_session.add(other_character)
    await db_session.flush()

    image = _make_reference_image(
        project, user, character, object_key="char/ref-wrong.jpg"
    )
    db_session.add(image)
    await db_session.commit()

    response = await api_client.delete(
        _delete_url(project.id, story.id, other_character.id, image.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 404


async def test_delete_reference_image_401_no_token(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """401 when no Authorization header is provided."""
    image = _make_reference_image(
        project, user, character, object_key="char/ref-auth.jpg"
    )
    db_session.add(image)
    await db_session.commit()

    response = await api_client.delete(
        _delete_url(project.id, story.id, character.id, image.id),
    )

    assert response.status_code == 401


async def test_delete_reference_image_404_wrong_discriminator(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """404 when the image exists but is a render, not a reference image."""
    render_image = ImageModel.create(
        project_id=project.id,
        user_id=user.id,
        target_id=character.id,
        width=512,
        height=512,
        content_type=ImageContentType.JPEG,
        object_key="char/render-disc.jpg",
        bucket="test-bucket",
        size_bytes=2048,
        discriminator_key=ImageDiscriminatorKey.CHARACTER_RENDER,
    )
    db_session.add(render_image)
    await db_session.commit()

    response = await api_client.delete(
        _delete_url(project.id, story.id, character.id, render_image.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 404
